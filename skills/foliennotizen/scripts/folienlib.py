"""Gemeinsame Bausteine fuer den Skill foliennotizen.

Enthaelt die TUDa-Farbpalette, die Umwandlung von Praesentationen in PDF,
die deterministische Zerlegung einer Folie in adressierbare Elemente
(Textbloecke b1, Zeilen b1.2, Bilder i1, Grafiken g1) und kleine Helfer.
Analyse- und Build-Skript nutzen dieselben Funktionen, damit eine ID wie
"b3" in beiden Schritten dasselbe Element bezeichnet.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover - Hinweis fuer die Umgebung
    sys.exit("PyMuPDF fehlt: pip install --break-system-packages pymupdf")

SKILL_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = SKILL_DIR / "assets" / "fonts"

# ---------------------------------------------------------------------------
# TUDa-Farbpalette (tuda-ci, tudacolors.def v4.06; HEX-Werte wie im CD-Manual)
# ---------------------------------------------------------------------------
TUDA = {
    "0a": "#DCDCDC", "0b": "#B5B5B5", "0c": "#898989", "0d": "#535353",
    "1a": "#5D85C3", "2a": "#009CDA", "3a": "#50B695", "4a": "#AFCC50",
    "5a": "#DDDF48", "6a": "#FFE05C", "7a": "#F8BA3C", "8a": "#EE7A34",
    "9a": "#E9503E", "10a": "#C9308E", "11a": "#804597",
    "1b": "#005AA9", "2b": "#0083CC", "3b": "#009D81", "4b": "#99C000",
    "5b": "#C9D400", "6b": "#FDCA00", "7b": "#F5A300", "8b": "#EC6500",
    "9b": "#E6001A", "10b": "#A60084", "11b": "#721085",
    "1c": "#004E8A", "2c": "#00689D", "3c": "#008877", "4c": "#7FAB16",
    "5c": "#B1BD00", "6c": "#D7AC00", "7c": "#D28700", "8c": "#CC4C03",
    "9c": "#B90F22", "10c": "#951169", "11c": "#611C73",
    "1d": "#243572", "2d": "#004E73", "3d": "#00715E", "4d": "#6A8B22",
    "5d": "#99A604", "6d": "#AE8E00", "7d": "#BE6F00", "8d": "#A94913",
    "9d": "#961C26", "10d": "#732054", "11d": "#4C226A",
}
# Laut tuda-ci duerfen diese (zu blassen) Farben nicht als Textfarbe dienen.
KEIN_TEXTAKZENT = {"0a", "5a", "6a", "6b", "7a"}
# Standard-Akzent von tuda-ci, falls aus den Folien nichts erkennbar ist.
STANDARD_AKZENT = "0b"
STANDARD_MARKER = "6a"


def hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tuda_hex(code: str) -> str:
    """'9c', 'TUDa-9c' oder '#B90F22' -> HEX-Wert einer Palettenfarbe."""
    c = code.strip()
    if c.lower().startswith("tuda-"):
        c = c[5:]
    c = c.lower()
    if c in TUDA:
        return TUDA[c]
    if re.fullmatch(r"#?[0-9a-f]{6}", c):
        return "#" + c.lstrip("#").upper()
    raise ValueError(f"Unbekannte Farbe '{code}'. Erlaubt: TUDa-Codes 0a-0d, 1a-11d")


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def leuchtdichte(rgb) -> float:
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(rgb1, rgb2) -> float:
    l1, l2 = sorted((leuchtdichte(rgb1), leuchtdichte(rgb2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def _lab(rgb):
    r, g, b = (_lin(x) for x in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def naechste_tuda(rgb) -> tuple[str, float]:
    """Naechste Palettenfarbe (ohne Grautoene) und Delta-E (CIE76)."""
    l1 = _lab(rgb)
    best = None
    for code, hx in TUDA.items():
        if code.startswith("0"):
            continue
        d = math.dist(l1, _lab(hex_rgb(hx)))
        if best is None or d < best[1]:
            best = (code, d)
    return best


def akzent_rollen(code: str) -> dict:
    """Leitet aus dem Akzent die Farben fuer Balken, Akzenttext und Schrift auf Akzent ab."""
    hx = tuda_hex(code)
    rgb = hex_rgb(hx)
    weiss, schwarz = (1, 1, 1), (0, 0, 0)
    text_ok = code not in KEIN_TEXTAKZENT and kontrast(rgb, weiss) >= 3.0
    return {
        "code": code,
        "balken": hx,
        "text": hx if text_ok else "#000000",
        "auf_akzent": "#FFFFFF" if kontrast(rgb, weiss) >= kontrast(rgb, schwarz) else "#000000",
        "rahmen": hx if kontrast(rgb, weiss) >= 3.0 else TUDA["0d"],
    }


# ---------------------------------------------------------------------------
# Eingabe: PDF direkt, Praesentationen ueber LibreOffice
# ---------------------------------------------------------------------------
PRAESENTATION = {".pptx", ".ppt", ".pptm", ".odp", ".key", ".pps", ".ppsx"}


def sha256(pfad) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for teil in iter(lambda: f.read(1 << 20), b""):
            h.update(teil)
    return h.hexdigest()


def zu_pdf(eingabe: Path, ziel_pdf: Path) -> str:
    """Legt eine PDF-Fassung der Folien unter ziel_pdf ab.

    PDFs werden byteidentisch kopiert. Praesentationen werden mit LibreOffice
    exportiert; Rueckgabe beschreibt die Herkunft fuer den Bericht.
    """
    eingabe = Path(eingabe)
    ziel_pdf.parent.mkdir(parents=True, exist_ok=True)
    endung = eingabe.suffix.lower()
    if endung == ".pdf":
        if eingabe.resolve() != ziel_pdf.resolve():
            shutil.copyfile(eingabe, ziel_pdf)
        return "PDF (unverändert übernommen)"
    if endung not in PRAESENTATION:
        raise SystemExit(f"Nicht unterstütztes Format: {eingabe.suffix} (erwartet PDF oder PPTX/ODP)")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise SystemExit("LibreOffice (soffice) fehlt. Bitte die Folien als PDF exportieren und erneut hochladen.")
    with tempfile.TemporaryDirectory() as tmp:
        profil = Path(tmp) / "profil"
        cmd = [soffice, f"-env:UserInstallation=file://{profil}", "--headless",
               "--convert-to", "pdf", "--outdir", tmp, str(eingabe)]
        try:
            subprocess.run(cmd, check=True, timeout=600,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            raise SystemExit("LibreOffice-Export hat zu lange gedauert. Bitte die Folien als PDF hochladen.")
        except subprocess.CalledProcessError as e:
            raise SystemExit("LibreOffice-Export fehlgeschlagen: " + e.stderr.decode(errors="replace")[-500:])
        erzeugt = Path(tmp) / (eingabe.stem + ".pdf")
        if not erzeugt.exists():
            raise SystemExit("LibreOffice hat keine PDF erzeugt. Bitte die Folien als PDF hochladen.")
        shutil.copyfile(erzeugt, ziel_pdf)
    return f"{endung[1:].upper()} → PDF per LibreOffice (Schriften können vom Original abweichen)"


def pptx_notizen(pfad: Path) -> list[str] | None:
    """Sprechernotizen der sichtbaren Folien in Exportreihenfolge (nur PPTX)."""
    if Path(pfad).suffix.lower() not in {".pptx", ".pptm", ".ppsx"}:
        return None
    try:
        from pptx import Presentation
    except ImportError:
        return None
    notizen = []
    for folie in Presentation(str(pfad)).slides:
        if folie._element.get("show") == "0":  # ausgeblendete Folien exportiert LibreOffice nicht
            continue
        text = ""
        if folie.has_notes_slide:
            text = folie.notes_slide.notes_text_frame.text.strip()
        notizen.append(text)
    return notizen


# ---------------------------------------------------------------------------
# Zerlegung einer Folie in adressierbare Elemente
# ---------------------------------------------------------------------------
def norm(rect, seite: pymupdf.Rect, nd: int = 5) -> list[float]:
    w, h = seite.width, seite.height
    return [round((rect[0] - seite.x0) / w, nd), round((rect[1] - seite.y0) / h, nd),
            round((rect[2] - seite.x0) / w, nd), round((rect[3] - seite.y0) / h, nd)]


def denorm(box, seite: pymupdf.Rect) -> pymupdf.Rect:
    w, h = seite.width, seite.height
    return pymupdf.Rect(seite.x0 + box[0] * w, seite.y0 + box[1] * h,
                        seite.x0 + box[2] * w, seite.y0 + box[3] * h)


def _zeilentext(zeile) -> str:
    t = "".join(s["text"] for s in zeile["spans"])
    t = t.replace("\x00", " ").replace("\x01", " ")
    t = "".join(ch if ch.isprintable() else " " for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def _schluessel(text: str) -> str:
    t = re.sub(r"\d+", "#", text.lower())
    return re.sub(r"\s+", " ", t).strip()


def roh_elemente(page: pymupdf.Page) -> dict:
    """Rohdaten einer Seite: Textbloecke mit Zeilen, Bilder und Grafikcluster."""
    seite = page.rect
    flaeche = seite.width * seite.height
    td = page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)
    bloecke = []
    for b in td["blocks"]:
        if b.get("type", 0) != 0:
            continue
        zeilen = []
        for z in b["lines"]:
            t = _zeilentext(z)
            if not t:
                continue
            groessen = [s["size"] for s in z["spans"] if s["text"].strip()]
            farben = [s["color"] for s in z["spans"] if s["text"].strip()]
            zeilen.append({"rect": pymupdf.Rect(z["bbox"]), "text": t,
                           "groesse": max(groessen) if groessen else 0,
                           "farben": farben, "zeichen": len(t)})
        if not zeilen:
            continue
        r = pymupdf.Rect(zeilen[0]["rect"])
        for z in zeilen[1:]:
            r |= z["rect"]
        bloecke.append({"rect": r, "zeilen": zeilen})
    # Lesereihenfolge: oben nach unten in 4%-Baendern, darin links nach rechts
    bloecke.sort(key=lambda b: (int((b["rect"].y0 - seite.y0) / seite.height * 25), b["rect"].x0))
    for b in bloecke:
        b["zeilen"].sort(key=lambda z: (round(z["rect"].y0, 0), z["rect"].x0))

    bilder = []
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"]) & seite
        if r.is_empty or r.width * r.height < 0.002 * flaeche:
            continue
        bilder.append({"rect": r, "hintergrund": r.width * r.height > 0.85 * flaeche})
    bilder.sort(key=lambda b: (int((b["rect"].y0 - seite.y0) / seite.height * 25), b["rect"].x0))

    zeichnungen = []
    try:
        for p in page.get_drawings():
            r = pymupdf.Rect(p["rect"])
            if r.width * r.height >= 0.85 * flaeche:  # Seitenhintergrund
                continue
            zeichnungen.append(p)
    except Exception:
        zeichnungen = []
    grafiken = []
    if zeichnungen:
        try:
            cluster = page.cluster_drawings(drawings=zeichnungen)
        except Exception:
            cluster = []
        for r in cluster:
            r = pymupdf.Rect(r) & seite
            if r.is_empty or r.width * r.height < 0.003 * flaeche:
                continue
            grafiken.append({"rect": r})
    grafiken.sort(key=lambda g: (int((g["rect"].y0 - seite.y0) / seite.height * 25), g["rect"].x0))
    return {"bloecke": bloecke, "bilder": bilder, "grafiken": grafiken, "zeichnungen": zeichnungen}


def vorlagen_schluessel(doc: pymupdf.Document, rohdaten: list[dict]) -> tuple[set, set]:
    """Findet wiederkehrende Elemente (Kopf-/Fusszeilen, Logos, Balken) ueber alle Folien."""
    n = len(rohdaten)
    if n < 4:
        return set(), set()
    schwelle = max(3, math.ceil(0.4 * n))
    zeilen_zaehler, form_zaehler = Counter(), Counter()
    for pno, roh in enumerate(rohdaten):
        seite = doc[pno].rect
        gesehen, formen = set(), set()
        for b in roh["bloecke"]:
            for z in b["zeilen"]:
                nb = norm(z["rect"], seite, 2)
                gesehen.add((_schluessel(z["text"]), nb[0], nb[1]))
        for art in ("bilder", "grafiken"):
            for e in roh[art]:
                formen.add((art, *norm(e["rect"], seite, 2)))
        zeilen_zaehler.update(gesehen)
        form_zaehler.update(formen)
    zeilen = {k for k, c in zeilen_zaehler.items() if c >= schwelle}
    formen = {k for k, c in form_zaehler.items() if c >= schwelle}
    return zeilen, formen


def elemente(page: pymupdf.Page, roh: dict, vorlage_zeilen: set, vorlage_formen: set) -> dict:
    """Vergibt IDs. Vorlagenelemente behalten ihre ID, werden aber markiert."""
    seite = page.rect
    out = {"bloecke": [], "bilder": [], "grafiken": []}
    for i, b in enumerate(roh["bloecke"], 1):
        zeilen = []
        alle_vorlage = True
        for j, z in enumerate(b["zeilen"], 1):
            nb = norm(z["rect"], seite, 2)
            ist_vorlage = (_schluessel(z["text"]), nb[0], nb[1]) in vorlage_zeilen
            alle_vorlage &= ist_vorlage
            zeilen.append({"id": f"b{i}.{j}", "box": norm(z["rect"], seite), "text": z["text"],
                           "groesse": round(z["groesse"], 1)})
        out["bloecke"].append({
            "id": f"b{i}", "box": norm(b["rect"], seite),
            "text": " ".join(z["text"] for z in zeilen),
            "groesse": round(max(z["groesse"] for z in zeilen), 1),
            "vorlage": alle_vorlage, "zeilen": zeilen})
    for art, praefix in (("bilder", "i"), ("grafiken", "g")):
        for k, e in enumerate(roh[art], 1):
            nb = norm(e["rect"], seite, 2)
            eintrag = {"id": f"{praefix}{k}", "box": norm(e["rect"], seite),
                       "vorlage": (art, *nb) in vorlage_formen}
            if art == "bilder":
                eintrag["hintergrund"] = e["hintergrund"]
            out[art].append(eintrag)
    return out


def titel_raten(el: dict) -> str:
    kandidaten = []
    for b in el["bloecke"]:
        if b["vorlage"]:
            continue
        for z in b["zeilen"]:
            if z["box"][1] < 0.45 and len(z["text"]) > 1:
                kandidaten.append((z["groesse"], -z["box"][1], z, b))
    if not kandidaten:
        return ""
    kandidaten.sort(key=lambda k: (k[0], k[1]), reverse=True)
    groesse, _, zeile, block = kandidaten[0]
    teile = [z["text"] for z in block["zeilen"] if abs(z["groesse"] - groesse) < 0.6]
    titel = " ".join(teile) if len(" ".join(teile)) < 140 else zeile["text"]
    return titel.strip()


def element_index(el: dict) -> dict:
    """ID -> Liste normierter Boxen (Zeilenboxen fuer Textbloecke)."""
    idx = {}
    for b in el["bloecke"]:
        idx[b["id"]] = {"art": "text", "boxen": [z["box"] for z in b["zeilen"]], "text": b["text"]}
        for z in b["zeilen"]:
            idx[z["id"]] = {"art": "text", "boxen": [z["box"]], "text": z["text"]}
    for e in el["bilder"]:
        idx[e["id"]] = {"art": "bild", "boxen": [e["box"]]}
    for e in el["grafiken"]:
        idx[e["id"]] = {"art": "grafik", "boxen": [e["box"]]}
    return idx


def analysiere_dokument(doc: pymupdf.Document) -> list[dict]:
    """Elemente aller Seiten mit konsistenten IDs und Vorlagenerkennung."""
    roh = [roh_elemente(p) for p in doc]
    vz, vf = vorlagen_schluessel(doc, roh)
    ergebnis = []
    for pno, p in enumerate(doc):
        el = elemente(p, roh[pno], vz, vf)
        el["titel"] = titel_raten(el)
        el["_roh"] = roh[pno]
        ergebnis.append(el)
    return ergebnis


def lesbarer_text(el: dict) -> list[str]:
    return [b["text"] for b in el["bloecke"] if not b["vorlage"]]


def einrast_elemente(el: dict, seite: pymupdf.Rect) -> list:
    """Zeilen und Bilder einer Folie (ohne Vorlagen, Hintergruende und Linien) als Rechtecke."""
    aus = []
    for b in el["bloecke"]:
        if b.get("vorlage"):
            continue
        aus.extend(denorm(z["box"], seite) for z in b["zeilen"])
    for e in el["bilder"]:
        if not e.get("vorlage") and not e.get("hintergrund"):
            aus.append(denorm(e["box"], seite))
    # duenne, lange Elemente (Trennlinien, Pfeile) muss ein Rahmen nicht umgehen
    return [r for r in aus if r.width > 0 and r.height > 0
            and not (min(r.width, r.height) < 14 and max(r.width, r.height) > 6 * min(r.width, r.height))]


def einrasten(r: pymupdf.Rect, elemente: list, pad: float) -> pymupdf.Rect:
    """Passt einen grob gewaehlten Bereich an die Folienelemente an.

    Elemente, die zu mindestens 40 % im Bereich liegen, werden ganz aufgenommen. Elemente,
    die nur angeschnitten werden, schiebt die naechstgelegene Kante aus dem Rahmen heraus
    (inklusive Rahmenabstand pad), sofern der Bereich dadurch um hoechstens ein Viertel
    schrumpft und dabei kein aufgenommenes Element angeschnitten wird. So schneidet ein
    Rahmen moeglichst keine Schrift an.
    """
    r = pymupdf.Rect(r)
    grenze = r.get_area()   # nur Elemente aufnehmen, die kleiner sind als der Bereich selbst
    for _ in range(2):
        alt = pymupdf.Rect(r)
        for e in elemente:
            schnitt = e & r
            if (not schnitt.is_empty and e.get_area() <= grenze
                    and schnitt.get_area() >= 0.4 * e.get_area()):
                r |= e
        if r == alt:
            break
    drin = [e for e in elemente if r.contains(e)]

    def schneidet_drinnen(kante: str, wert: float) -> bool:
        for e in drin:
            if kante in ("x0", "x1") and e.x0 - pad < wert < e.x1 + pad:
                return True
            if kante in ("y0", "y1") and e.y0 - pad < wert < e.y1 + pad:
                return True
        return False

    for e in elemente:
        rp = pymupdf.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad)
        if (e & rp).is_empty or e.contains(rp) or rp.contains(e):
            continue
        if (e & r).get_area() >= 0.4 * e.get_area():
            continue
        kandidaten = []
        if e.x0 > r.x0 and e.x0 - pad - 1 > r.x0:
            kandidaten.append(("x1", e.x0 - pad - 1, r.x1 - (e.x0 - pad - 1), r.width))
        if e.x1 < r.x1 and e.x1 + pad + 1 < r.x1:
            kandidaten.append(("x0", e.x1 + pad + 1, (e.x1 + pad + 1) - r.x0, r.width))
        if e.y0 > r.y0 and e.y0 - pad - 1 > r.y0:
            kandidaten.append(("y1", e.y0 - pad - 1, r.y1 - (e.y0 - pad - 1), r.height))
        if e.y1 < r.y1 and e.y1 + pad + 1 < r.y1:
            kandidaten.append(("y0", e.y1 + pad + 1, (e.y1 + pad + 1) - r.y0, r.height))
        kandidaten = [k for k in kandidaten if 0 < k[2] <= 0.25 * k[3] and not schneidet_drinnen(k[0], k[1])]
        if kandidaten:
            kante, wert, _, _ = min(kandidaten, key=lambda k: k[2] / k[3])
            setattr(r, kante, wert)
    return r


def schreibe_sortiert_ids(ids):
    def k(x):
        m = re.match(r"([a-z])(\d+)(?:\.(\d+))?", x)
        return (m.group(1), int(m.group(2)), int(m.group(3) or 0)) if m else (x, 0, 0)
    return sorted(ids, key=k)


def mm(x: float) -> float:
    return x * 72 / 25.4
