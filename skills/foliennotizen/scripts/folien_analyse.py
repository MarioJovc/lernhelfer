#!/usr/bin/env python3
"""Schritt 1: Foliensatz einlesen und fuer das Kommentieren aufbereiten.

    python3 folien_analyse.py <foliensatz.pdf|pptx> --out arbeit

Legt in <out> ab:
  folien.pdf          die Folien als PDF (Quelle fuer Build und Pruefung)
  analyse.json        Elemente je Folie mit IDs (b3, b3.2, i1, g1), Titel, Notizen
  folien_text.md      kompakter Text aller Folien mit IDs, ohne Kopf-/Fusszeilen
  bilder/uebersicht_NN.png  je 4 Folien, zum schnellen Durchsehen
  bilder/folie_NNN.png      einzelne Folie in Lesegroesse
  bilder/karte_NNN.png      Lagekarte: Elemente mit IDs und Koordinatenraster
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import folienlib as fl  # noqa: E402
import pymupdf  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


def schrift(groesse: int, fett: bool = False):
    name = "Roboto-Bold.ttf" if fett else "Roboto-Regular.ttf"
    try:
        return ImageFont.truetype(str(fl.FONT_DIR / name), groesse)
    except OSError:
        return ImageFont.load_default()


def rendern(page: pymupdf.Page, breite_px: int) -> Image.Image:
    zoom = breite_px / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def format_name(w: float, h: float) -> str:
    v = w / h
    for name, wert in (("16:9", 16 / 9), ("16:10", 1.6), ("4:3", 4 / 3), ("3:2", 1.5), ("A4 quer", 297 / 210)):
        if abs(v - wert) < 0.02:
            return name
    return f"{v:.2f}:1" if v >= 1 else f"Hochformat {v:.2f}:1"


def akzent_erkennen(doc, analyse) -> dict:
    gewichte, summen = Counter(), {}
    for pno, page in enumerate(doc):
        seite = page.rect
        flaeche = seite.width * seite.height
        roh = analyse[pno]["_roh"]
        beitraege = []
        for p in roh["zeichnungen"]:
            r = pymupdf.Rect(p["rect"]) & seite
            if r.is_empty and not (r.width or r.height):
                continue
            if p.get("fill") and len(p["fill"]) == 3 and (p.get("fill_opacity") or 1) > 0.5:
                beitraege.append((p["fill"], r.width * r.height / flaeche))
            if p.get("color") and len(p["color"]) == 3:
                laenge = max(r.width, r.height)
                beitraege.append((p["color"], (p.get("width") or 1) * laenge / flaeche * 0.5))
        for b in roh["bloecke"]:
            for z in b["zeilen"]:
                for c in z["farben"]:
                    rgb = (((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255)
                    w = z["zeichen"] * (z["groesse"] / seite.height) ** 2 * 0.6 / max(1, len(z["farben"]))
                    beitraege.append((rgb, w))
        for rgb, w in beitraege:
            h, s, v = colorsys.rgb_to_hsv(*rgb)
            if s < 0.35 or v < 0.25 or w <= 0:
                continue
            k = tuple(round(x * 31) for x in rgb)
            gewichte[k] += w
            alt = summen.get(k, (0, 0, 0, 0))
            summen[k] = (alt[0] + rgb[0] * w, alt[1] + rgb[1] * w, alt[2] + rgb[2] * w, alt[3] + w)
    if not gewichte:
        return {"code": fl.STANDARD_AKZENT, "hex": fl.TUDA[fl.STANDARD_AKZENT], "quelle": "Standard (tuda-ci)",
                "delta_e": None}
    k, _ = gewichte.most_common(1)[0]
    s = summen[k]
    rgb = (s[0] / s[3], s[1] / s[3], s[2] / s[3])
    code, de = fl.naechste_tuda(rgb)
    return {"code": code, "hex": fl.TUDA[code], "quelle": "aus den Folien erkannt", "delta_e": round(de, 1),
            "folienfarbe": "#%02X%02X%02X" % tuple(round(x * 255) for x in rgb)}


def aufbau_erkennen(analyse) -> list[dict]:
    """Findet Beamer-/Animationsaufbauten: Folie i ist Teilmenge von Folie i+1."""
    def inhalt(el):
        zeilen = {fl._schluessel(z["text"]) for b in el["bloecke"] if not b["vorlage"] for z in b["zeilen"]}
        return zeilen, len([e for e in el["bilder"] if not e["vorlage"]]), len([g for g in el["grafiken"] if not g["vorlage"]])

    stufe_von = {}
    for i in range(len(analyse) - 1):
        a, b = analyse[i], analyse[i + 1]
        if not a["titel"] or a["titel"] != b["titel"]:
            continue
        (ta, ia, ga), (tb, ib, gb) = inhalt(a), inhalt(b)
        if ta and ta <= tb and (len(tb) > len(ta) or ib > ia or gb > ga):
            stufe_von[i] = i + 1
    gruppen, i = [], 0
    while i < len(analyse):
        if i in stufe_von:
            kette = [i]
            while kette[-1] in stufe_von:
                kette.append(stufe_von[kette[-1]])
            gruppen.append({"folien": [k + 1 for k in kette], "endstand": kette[-1] + 1})
            i = kette[-1] + 1
        else:
            i += 1
    return gruppen


def lagekarte(page, el, pfad: Path, breite_px: int = 1400):
    bild = rendern(page, breite_px)
    rand = 46
    w, h = bild.size
    karte = Image.new("RGB", (w + 2 * rand, h + 2 * rand), "white")
    karte.paste(bild, (rand, rand))
    zeichnen = ImageDraw.Draw(karte, "RGBA")
    f_klein, f_id = schrift(15), schrift(16, fett=True)
    # Koordinatenraster in Zehnteln, damit Bereiche (bereich=x0,y0,x1,y1) ablesbar sind
    for k in range(11):
        x = rand + k * w / 10
        y = rand + k * h / 10
        zeichnen.line([(x, rand), (x, rand + h)], fill=(120, 120, 120, 70), width=1)
        zeichnen.line([(rand, y), (rand + w, y)], fill=(120, 120, 120, 70), width=1)
        t = f"{k / 10:.1f}".replace("1.0", "1")
        zeichnen.text((x - 10, 8), t, fill=(90, 90, 90), font=f_klein)
        zeichnen.text((x - 10, rand + h + 14), t, fill=(90, 90, 90), font=f_klein)
        zeichnen.text((4, y - 9), t, fill=(90, 90, 90), font=f_klein)
        zeichnen.text((rand + w + 6, y - 9), t, fill=(90, 90, 90), font=f_klein)

    def box(b, farbe, label):
        x0, y0 = rand + b[0] * w, rand + b[1] * h
        x1, y1 = rand + b[2] * w, rand + b[3] * h
        zeichnen.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], outline=farbe + (230,), width=2)
        tb = zeichnen.textbbox((0, 0), label, font=f_id)
        lw, lh = tb[2] - tb[0] + 8, tb[3] - tb[1] + 6
        lx, ly = x0 - 2, y0 - lh - 2
        if ly < rand - lh:
            ly = y0
        zeichnen.rectangle([lx, ly, lx + lw, ly + lh], fill=farbe + (235,))
        zeichnen.text((lx + 4, ly + 1), label, fill=(255, 255, 255), font=f_id)

    for g in el["grafiken"]:
        if not g["vorlage"]:
            box(g["box"], (226, 120, 0), g["id"])
    for b in el["bilder"]:
        if not b["vorlage"] and not b.get("hintergrund"):
            box(b["box"], (0, 140, 90), b["id"])
    for b in el["bloecke"]:
        if not b["vorlage"]:
            box(b["box"], (0, 90, 169), b["id"])
    karte.save(pfad)


def uebersichten(doc, analyse, ordner: Path) -> list[str]:
    namen = []
    breite = 780
    for start in range(0, len(doc), 4):
        bilder = []
        for pno in range(start, min(start + 4, len(doc))):
            bilder.append((pno, rendern(doc[pno], breite)))
        hoehe = max(b.height for _, b in bilder)
        kopf = 30
        bogen = Image.new("RGB", (2 * breite + 30, 2 * (hoehe + kopf) + 30), (205, 205, 205))
        zeichnen = ImageDraw.Draw(bogen)
        f = schrift(19, fett=True)
        for k, (pno, b) in enumerate(bilder):
            x = 10 + (k % 2) * (breite + 10)
            y = 10 + (k // 2) * (hoehe + kopf + 10)
            titel = analyse[pno]["titel"]
            if len(titel) > 60:
                titel = titel[:58] + "…"
            zeichnen.rectangle([x, y, x + breite, y + kopf], fill=(40, 40, 40))
            zeichnen.text((x + 8, y + 4), f"Folie {pno + 1}  {titel}", fill="white", font=f)
            bogen.paste(b, (x, y + kopf))
        name = f"uebersicht_{start // 4 + 1:02d}.png"
        bogen.save(ordner / name)
        namen.append(name)
    return namen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eingabe", help="Foliensatz als PDF oder PPTX/ODP")
    ap.add_argument("--out", default="arbeit", help="Arbeitsordner (Standard: arbeit)")
    ap.add_argument("--karten", default="alle", help="Lagekarten: alle | keine | Liste wie 3,5,7-9")
    ap.add_argument("--keine-bilder", action="store_true", help="nur Text und JSON erzeugen")
    a = ap.parse_args()

    eingabe = Path(a.eingabe)
    if not eingabe.exists():
        sys.exit(f"Datei nicht gefunden: {eingabe}")
    out = Path(a.out)
    (out / "bilder").mkdir(parents=True, exist_ok=True)
    pdf_pfad = out / "folien.pdf"
    herkunft = fl.zu_pdf(eingabe, pdf_pfad)
    notizen = fl.pptx_notizen(eingabe)

    doc = pymupdf.open(pdf_pfad)
    if doc.needs_pass:
        sys.exit("Die PDF ist passwortgeschützt. Bitte eine ungeschützte Fassung hochladen.")
    if len(doc) == 0:
        sys.exit("Die PDF enthält keine Seiten.")
    gedreht = [i + 1 for i, p in enumerate(doc) if p.rotation]
    if gedreht:
        # Gedrehte Seiten: Drehung in den Inhalt uebernehmen, damit Text- und Seitenkoordinaten
        # zusammenpassen. Die Darstellung bleibt pixelgleich (prueft kommentar_pruefen.py --original).
        for nr in gedreht:
            doc[nr - 1].remove_rotation()
        tmp = pdf_pfad.with_name("folien_tmp.pdf")
        doc.save(tmp)
        doc.close()
        tmp.replace(pdf_pfad)
        doc = pymupdf.open(pdf_pfad)
        herkunft += f"; Seitendrehung auf {len(gedreht)} Folie(n) normalisiert, Darstellung unverändert"
    analyse = fl.analysiere_dokument(doc)
    akzent = akzent_erkennen(doc, analyse)
    aufbau = aufbau_erkennen(analyse)
    stufen = {}
    for g in aufbau:
        for k, nr in enumerate(g["folien"], 1):
            stufen[nr] = (k, len(g["folien"]), g["endstand"])

    if notizen is not None and len(notizen) != len(doc):
        print(f"Hinweis: {len(notizen)} Notizen für {len(doc)} Seiten – Zuordnung unsicher, Notizen werden ignoriert.")
        notizen = None

    vorlagen_text = Counter()
    folien = []
    for pno, page in enumerate(doc):
        el = analyse[pno]
        for b in el["bloecke"]:
            if b["vorlage"]:
                vorlagen_text[re.sub(r"\d+", "#", b["text"])] += 1
        zeichen = sum(len(t) for t in fl.lesbarer_text(el))
        eintrag = {
            "nr": pno + 1, "breite": round(page.rect.width, 3), "hoehe": round(page.rect.height, 3),
            "drehung": page.rotation, "titel": el["titel"], "zeichen": zeichen,
            "kein_text": zeichen == 0 and not any(b for b in el["bloecke"]),
            "bloecke": el["bloecke"], "bilder": el["bilder"], "grafiken": el["grafiken"],
        }
        if notizen:
            eintrag["notizen"] = notizen[pno]
        if pno + 1 in stufen:
            k, n, end = stufen[pno + 1]
            eintrag["aufbau"] = {"stufe": k, "von": n, "endstand": end}
        folien.append(eintrag)

    w0, h0 = doc[0].rect.width, doc[0].rect.height
    formate = Counter(format_name(f["breite"], f["hoehe"]) for f in folien)
    ergebnis = {
        "quelle": {"datei": eingabe.name, "pdf": pdf_pfad.name, "sha256": fl.sha256(pdf_pfad),
                   "herkunft": herkunft},
        "seiten": len(doc), "format": formate.most_common(1)[0][0],
        "akzent": akzent, "aufbau": aufbau, "folien": folien,
    }
    (out / "analyse.json").write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1), encoding="utf-8")

    # Kompakter Text fuer das Lesen im Chat
    zeilen = [f"# Folientext: {eingabe.name} ({len(doc)} Folien, {ergebnis['format']})", ""]
    if vorlagen_text:
        zeilen.append("Wiederkehrende Kopf-/Fußzeilen (unten weggelassen): " +
                      " | ".join(f"„{t[:70]}“" for t, _ in vorlagen_text.most_common(4)))
        zeilen.append("")
    for f in folien:
        kopf = f"## Folie {f['nr']}" + (f" · {f['titel']}" if f["titel"] else "")
        zeilen.append(kopf)
        if "aufbau" in f:
            ab = f["aufbau"]
            zeilen.append(f"(Aufbaustufe {ab['stufe']}/{ab['von']}, Endstand: Folie {ab['endstand']})")
        if f["kein_text"]:
            zeilen.append("(keine Textebene – Inhalt nur im Bild sichtbar, ggf. gescannt)")
        for b in f["bloecke"]:
            if b["vorlage"]:
                continue
            if len(b["zeilen"]) > 1:
                zeilen.append(f"{b['id']}  " + " / ".join(f"[{z['id'].split('.')[1]}] {z['text']}" for z in b["zeilen"]))
            else:
                zeilen.append(f"{b['id']}  {b['text']}")
        for e in f["bilder"]:
            if not e["vorlage"]:
                zeilen.append(f"{e['id']}  Bild {[round(v, 2) for v in e['box']]}" + (" (Hintergrund)" if e.get("hintergrund") else ""))
        for e in f["grafiken"]:
            if not e["vorlage"]:
                zeilen.append(f"{e['id']}  Grafik {[round(v, 2) for v in e['box']]}")
        if f.get("notizen"):
            zeilen.append("Notizen: " + re.sub(r"\s+", " ", f["notizen"]))
        zeilen.append("")
    (out / "folien_text.md").write_text("\n".join(zeilen), encoding="utf-8")

    bild_info = ""
    if not a.keine_bilder:
        ordner = out / "bilder"
        namen = uebersichten(doc, analyse, ordner)
        for pno, page in enumerate(doc):
            rendern(page, 1400).save(ordner / f"folie_{pno + 1:03d}.png")
        if a.karten != "keine":
            wahl = set(range(1, len(doc) + 1))
            if a.karten != "alle":
                wahl = set()
                for teil in a.karten.split(","):
                    if "-" in teil:
                        x, y = teil.split("-")
                        wahl.update(range(int(x), int(y) + 1))
                    elif teil.strip():
                        wahl.add(int(teil))
            for nr in sorted(wahl):
                if 1 <= nr <= len(doc):
                    lagekarte(doc[nr - 1], analyse[nr - 1], ordner / f"karte_{nr:03d}.png")
        bild_info = f"{out}/bilder/ ({len(namen)} Übersichtsbögen, folie_NNN.png, karte_NNN.png)"

    print(f"Analyse fertig: {len(doc)} Folien, Format {ergebnis['format']} ({w0:.0f}×{h0:.0f} pt)")
    print(f"  Quelle: {eingabe.name} – {herkunft}")
    print(f"  Folien-PDF: {pdf_pfad}")
    if akzent["delta_e"] is None:
        print(f"  Akzentfarbe: {akzent['code']} {akzent['hex']} – {akzent['quelle']}")
    else:
        print(f"  Akzentfarbe: {akzent['code']} {akzent['hex']} – {akzent['quelle']} "
              f"(Folienfarbe {akzent['folienfarbe']}, ΔE {akzent['delta_e']})")
    if aufbau:
        print("  Aufbaustufen: " + "; ".join(f"Folien {g['folien'][0]}–{g['folien'][-1]} (Endstand {g['endstand']})" for g in aufbau))
    ohne = [f["nr"] for f in folien if f["kein_text"]]
    if ohne:
        print(f"  Ohne Textebene (Scan/Bild): Folien {', '.join(map(str, ohne))} – Markierungen nur über bereich=")
    if notizen:
        mit = [str(i + 1) for i, n in enumerate(notizen) if n]
        print(f"  Sprechernotizen: {'Folien ' + ', '.join(mit) if mit else 'keine'}")
    if len(formate) > 1:
        print(f"  Achtung: gemischte Seitenformate {dict(formate)}")
    print(f"  Text: {out}/folien_text.md")
    if bild_info:
        print(f"  Bilder: {bild_info}")


if __name__ == "__main__":
    main()
