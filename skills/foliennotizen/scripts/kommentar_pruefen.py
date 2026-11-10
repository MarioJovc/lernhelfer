#!/usr/bin/env python3
"""Schritt 4: Kommentierten Foliensatz pruefen, bevor er ausgeliefert wird.

    python3 kommentar_pruefen.py --folien arbeit/folien.pdf --pdf "VL04_kommentiert.pdf" \\
        [--original Upload.pdf] [--bericht pruefbericht.md]

Prueft unabhaengig vom Build:
  1. Format: jede Seite A4 hoch, Folie vollstaendig in der oberen Haelfte, Seitenverhaeltnis erhalten.
  2. Vollstaendigkeit und Reihenfolge: jede Folie 1..N kommt vor, in aufsteigender Reihenfolge,
     ihre Seiten stehen zusammen, die erste Seite jeder Folie ist die unmarkierte Gesamtansicht.
  3. Unveraendert: Jede eingebettete Folie wird mit ausgeblendeter Markierungsebene gerendert und
     pixelweise mit dem Original verglichen; zusaetzlich wird der Folientext Wort fuer Wort verglichen.
  4. Markierungen: Schritt-Seiten tragen eine sichtbare Markierung, Ueberblicksseiten keine.
  5. Herkunft: Die Pruef-PDF ist dieselbe Datei, aus der gebaut wurde (SHA-256), optional auch
     dieselbe wie der Upload des Nutzers (--original).
Exitcode 0 = BESTANDEN, 1 = NICHT BESTANDEN.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pymupdf

A4_B, A4_H = 595.276, 841.89
ZOOM = 2.0
MITTEL_MAX = 1.0       # mittlere Abweichung je Pixel (0-255)
ANTEIL_MAX = 0.0005    # Anteil echter Abweichungen (>40 auch nach 1-px-Toleranz)
LOKAL_MAX = 24.0       # staerkste mittlere Abweichung in einem 3x3-pt-Feld


def sha256(pfad) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for teil in iter(lambda: f.read(1 << 20), b""):
            h.update(teil)
    return h.hexdigest()


def pixel(page, matrix, clip=None) -> np.ndarray:
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False, colorspace=pymupdf.csRGB)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(np.int16)


def vergleich(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Mittlere Abweichung, Anteil echter Abweichungen, staerkste lokale Abweichung.

    Kantenglaettung kann einzelne Glyphen um Bruchteile eines Pixels verschieben. Deshalb zaehlt
    als echte Abweichung nur, was sich auch mit einer Verschiebung um 1 px nicht erklaeren laesst;
    lokal wird in Feldern von 6x6 px (3x3 pt) gemittelt, damit auch kleine Abdeckungen auffallen.
    """
    if abs(a.shape[0] - b.shape[0]) > 2 or abs(a.shape[1] - b.shape[1]) > 2:
        return 255.0, 1.0, 255.0
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    a, b = a[:h, :w], b[:h, :w]
    d = np.abs(a - b).max(axis=2)
    pa = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    dmin = d.copy()
    for dy in range(3):
        for dx in range(3):
            dmin = np.minimum(dmin, np.abs(pa[dy:dy + h, dx:dx + w] - b).max(axis=2))
    hh, ww = (h // 6) * 6, (w // 6) * 6
    lokal = dmin[:hh, :ww].reshape(hh // 6, 6, ww // 6, 6).mean(axis=(1, 3)).max() if hh and ww else 0.0
    return float(d.mean()), float((dmin > 40).mean()), float(lokal)


def privat(doc, page) -> dict | None:
    basis = "PieceInfo/FolienKommentar/Private/"
    t, art = doc.xref_get_key(page.xref, basis + "Art")
    if t == "name" and art.lstrip("/") == "Zusammenfassung":
        return {"art": "Zusammenfassung", "folie": None}
    typ, folie = doc.xref_get_key(page.xref, basis + "Folie")
    if typ != "int":
        return None
    werte = {"folie": int(folie)}
    for k in ("Schritt", "Schritte", "Markierungen"):
        t, v = doc.xref_get_key(page.xref, basis + k)
        werte[k.lower()] = int(v) if t == "int" else 0
    t, v = doc.xref_get_key(page.xref, basis + "Art")
    werte["art"] = v.lstrip("/") if t == "name" else "?"
    t, v = doc.xref_get_key(page.xref, basis + "Fortsetzung")
    werte["fortsetzung"] = v == "true"
    t, v = doc.xref_get_key(page.xref, basis + "Rect")
    if t != "array":
        return None
    werte["rect"] = pymupdf.Rect([float(x) for x in v.strip("[]").split()])
    return werte


def woerter(page, clip=None) -> list[str]:
    return sorted(w[4] for w in page.get_text("words", clip=clip))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folien", required=True, help="Folien-PDF, aus der gebaut wurde (arbeit/folien.pdf)")
    ap.add_argument("--pdf", required=True, help="kommentierte PDF")
    ap.add_argument("--original", help="Upload des Nutzers, falls PDF (Byte-Vergleich mit --folien)")
    ap.add_argument("--bericht", help="Prüfbericht als Markdown schreiben")
    ap.add_argument("--entwurf-ok", action="store_true", help="Entwurfsfassung nicht als Fehler werten")
    a = ap.parse_args()

    src = pymupdf.open(a.folien)
    aus_an = pymupdf.open(a.pdf)
    aus_aus = pymupdf.open(a.pdf)
    n = len(src)
    fehler, hinweise = [], []

    # Herkunft
    typ, wert = aus_an.xref_get_key(aus_an.pdf_catalog(), "FolienKommentar/QuelleSHA256")
    quelle_sha = sha256(a.folien)
    if typ != "string":
        fehler.append("Die PDF trägt keine Build-Metadaten (nicht mit kommentar_bauen.py erzeugt?)")
    elif wert != quelle_sha:
        fehler.append("Die PDF wurde aus einer anderen Folien-PDF gebaut als der hier geprüften")
    typ, entwurf = aus_an.xref_get_key(aus_an.pdf_catalog(), "FolienKommentar/Entwurf")
    if entwurf == "true" and not a.entwurf_ok:
        fehler.append("Entwurfsfassung (--entwurf/--nur) – vor der Auslieferung ohne diese Optionen bauen")
    if a.original:
        if Path(a.original).suffix.lower() == ".pdf":
            if sha256(a.original) == quelle_sha:
                hinweise.append("Folien-PDF ist byteidentisch mit dem Original-Upload")
            else:
                # z. B. normalisierte Seitendrehung: dann muss wenigstens jede Seite gleich aussehen
                orig = pymupdf.open(a.original)
                if len(orig) != n:
                    fehler.append(f"Original hat {len(orig)} Seiten, folien.pdf {n}")
                else:
                    abweichend = []
                    for k in range(n):
                        z = 1.5
                        _, ant, lok = vergleich(pixel(orig[k], pymupdf.Matrix(z, z)), pixel(src[k], pymupdf.Matrix(z, z)))
                        if ant > ANTEIL_MAX or lok > LOKAL_MAX:
                            abweichend.append(k + 1)
                    if abweichend:
                        fehler.append("folien.pdf sieht auf Folie " + ", ".join(map(str, abweichend)) +
                                      " anders aus als der Original-Upload")
                    else:
                        hinweise.append("Folien-PDF ist nicht byteidentisch, aber auf allen Folien pixelgleich "
                                        "mit dem Original-Upload (z. B. normalisierte Seitendrehung)")
        else:
            hinweise.append("Original ist keine PDF – verglichen wird mit dem LibreOffice-Export (folien.pdf)")

    # Markierungsebene ausblenden (zweite Instanz)
    # (set_layer aendert nur das PDF-Objekt; die Live-Konfiguration schaltet die Ebene beim Rendern ab)
    ebenen = [c for c in aus_aus.layer_ui_configs() if c.get("text") == "Markierungen"]
    for c in ebenen:
        aus_aus.set_layer_ui_config(c["number"], action=2)
    if not ebenen:
        hinweise.append("Keine Markierungsebene gefunden (keine Schritt-Seiten?)")

    zeilen = []
    seiten_je_folie = defaultdict(list)
    folge, zf_seiten = [], []
    for i in range(len(aus_an)):
        p_an, p_aus = aus_an[i], aus_aus[i]
        nr_s = i + 1
        if abs(p_an.rect.width - A4_B) > 1 or abs(p_an.rect.height - A4_H) > 1:
            fehler.append(f"Seite {nr_s}: kein A4-Hochformat ({p_an.rect.width:.0f}×{p_an.rect.height:.0f} pt)")
        info = privat(aus_an, p_an)
        if info is None:
            fehler.append(f"Seite {nr_s}: keine Zuordnung zu einer Folie (Metadaten fehlen)")
            continue
        if info["art"] == "Zusammenfassung":
            zf_seiten.append(nr_s)
            folge.append("Z")
            continue
        folie, r = info["folie"], info["rect"]
        if not 1 <= folie <= n:
            fehler.append(f"Seite {nr_s}: verweist auf Folie {folie}, Foliensatz hat {n}")
            continue
        q = src[folie - 1]
        seiten_je_folie[folie].append((nr_s, info))
        folge.append(folie)
        # Geometrie
        if r.y1 > A4_H / 2 + 1 or r.y0 < 0 or r.x0 < 0 or r.x1 > A4_B:
            fehler.append(f"Seite {nr_s}: Folie {folie} liegt nicht vollständig in der oberen Hälfte")
        if abs(r.width / r.height - q.rect.width / q.rect.height) > 0.002 * (q.rect.width / q.rect.height):
            fehler.append(f"Seite {nr_s}: Seitenverhältnis von Folie {folie} verändert")
        # Pixelvergleich ohne Markierungsebene
        s = r.width / q.rect.width
        a_px = pixel(p_aus, pymupdf.Matrix(ZOOM, ZOOM), clip=r)
        b_px = pixel(q, pymupdf.Matrix(ZOOM * s, ZOOM * s))
        mittel, anteil, lokal = vergleich(a_px, b_px)
        unveraendert = mittel <= MITTEL_MAX and anteil <= ANTEIL_MAX and lokal <= LOKAL_MAX
        if not unveraendert:
            fehler.append(f"Seite {nr_s}: Folie {folie} weicht vom Original ab "
                          f"(Ø {mittel:.2f}, Anteil {anteil:.4f}, lokal {lokal:.0f})")
        # Textvergleich
        if woerter(p_an, clip=r) != woerter(q):
            fehler.append(f"Seite {nr_s}: Text von Folie {folie} stimmt nicht mit dem Original überein")
            text_ok = False
        else:
            text_ok = True
        # Markierungen sichtbar?
        an_px = pixel(p_an, pymupdf.Matrix(ZOOM, ZOOM), clip=r)
        diff = np.abs(an_px - a_px).max(axis=2) if an_px.shape == a_px.shape else None
        markiert = diff is not None and float((diff > 25).mean()) > 0.0005
        if info["art"] == "Ueberblick" and markiert:
            fehler.append(f"Seite {nr_s}: Gesamtansicht von Folie {folie} enthält Markierungen")
        if info["art"] == "Schritt" and not markiert:
            fehler.append(f"Seite {nr_s}: Schritt {info['schritt']} von Folie {folie} zeigt keine sichtbare Markierung")
        zeilen.append((nr_s, folie, info, mittel, anteil, text_ok, markiert, unveraendert))

    # Vollstaendigkeit und Reihenfolge
    fehlend = [k for k in range(1, n + 1) if k not in seiten_je_folie]
    if fehlend:
        fehler.append("Folien fehlen im Ergebnis: " + ", ".join(map(str, fehlend)))
    if zf_seiten:
        if any(f != "Z" for f in folge[folge.index("Z"):]):
            fehler.append("Die Zusammenfassung steht nicht am Ende (nach ihr folgen noch Folienseiten)")
    elif entwurf != "true" or not a.entwurf_ok:
        fehler.append("Zusammenfassung am Ende fehlt")
    folge = [f for f in folge if f != "Z"]
    erste = []
    for f in folge:
        if not erste or erste[-1] != f:
            erste.append(f)
    if erste != sorted(set(erste)) or len(erste) != len(set(erste)):
        fehler.append("Reihenfolge gestört oder Seiten einer Folie nicht zusammenhängend: " + " ".join(map(str, erste)))
    for folie, seiten in seiten_je_folie.items():
        if seiten[0][1]["art"] != "Ueberblick":
            fehler.append(f"Folie {folie}: erste Seite ist nicht die unmarkierte Gesamtansicht")
        schritte = [x[1]["schritt"] for x in seiten if x[1]["art"] == "Schritt" and not x[1]["fortsetzung"]]
        if schritte != list(range(1, len(schritte) + 1)):
            fehler.append(f"Folie {folie}: Schritte nicht lückenlos nummeriert ({schritte})")
        if any(x[1]["fortsetzung"] for x in seiten):
            hinweise.append(f"Folie {folie}: Kommentar läuft auf eine Fortsetzungsseite über")

    ok = not fehler
    kopf = "BESTANDEN" if ok else "NICHT BESTANDEN"
    print(f"PRÜFUNG {kopf}: {len(seiten_je_folie)}/{n} Folien auf {len(aus_an)} Seiten"
          + (f", Zusammenfassung auf Seite {', '.join(map(str, zf_seiten))}" if zf_seiten else ""))
    if zeilen:
        max_mittel = max(z[3] for z in zeilen)
        print(f"  Originaltreue: {sum(1 for z in zeilen if z[7])}/{len(zeilen)} "
              f"Seiten pixelgleich (größte mittlere Abweichung {max_mittel:.3f} von 255), "
              f"Text {sum(1 for z in zeilen if z[5])}/{len(zeilen)} identisch")
        print(f"  Markierungen: {sum(1 for z in zeilen if z[2]['art'] == 'Schritt')} Schritt-Seiten markiert, "
              f"{sum(1 for z in zeilen if z[2]['art'] == 'Ueberblick')} Gesamtansichten unmarkiert")
    for f in fehler:
        print("  FEHLER: " + f)
    for h in hinweise:
        print("  Hinweis: " + h)

    if a.bericht:
        b = [f"# Prüfbericht: {Path(a.pdf).name}", "", f"**Ergebnis: {kopf}**", "",
             f"- Folien: {len(seiten_je_folie)} von {n}, Seiten: {len(aus_an)}",
             f"- Zusammenfassung: Seite {', '.join(map(str, zf_seiten)) if zf_seiten else 'fehlt'}",
             f"- Quelle: {Path(a.folien).name} (SHA-256 {quelle_sha[:16]}…)", ""]
        b += ["| Folie | Seiten | Art | Abweichung Ø | Text | Markierung |", "|---|---|---|---|---|---|"]
        for folie in sorted(seiten_je_folie):
            for nr_s, info in seiten_je_folie[folie]:
                z = next(x for x in zeilen if x[0] == nr_s)
                art = "Gesamtansicht" if info["art"] == "Ueberblick" else f"Schritt {info['schritt']}/{info['schritte']}"
                if info["fortsetzung"]:
                    art += " (Forts.)"
                b.append(f"| {folie} | {nr_s} | {art} | {z[3]:.3f} | {'gleich' if z[5] else 'ABWEICHEND'} | "
                         f"{'ja' if z[6] else '–'} |")
        if fehler:
            b += ["", "## Fehler", *[f"- {f}" for f in fehler]]
        if hinweise:
            b += ["", "## Hinweise", *[f"- {h}" for h in hinweise]]
        Path(a.bericht).write_text("\n".join(b) + "\n", encoding="utf-8")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
