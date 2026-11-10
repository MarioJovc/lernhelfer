#!/usr/bin/env python3
"""Schritt 3: Kommentierten Foliensatz bauen (A4 Hochformat, TUDa-Gestaltung).

    python3 kommentar_bauen.py --folien arbeit/folien.pdf --kommentar kommentar/ \\
        --out "VL04_kommentiert.pdf"

Je Folie entsteht mindestens eine Seite: oben die Originalfolie (als Vektorgrafik
eingebettet, unveraendert), darunter der Kommentar. Schritt-Seiten zeigen
dieselbe Folie mit einer Markierung auf einer eigenen PDF-Ebene
("Markierungen"), die das Original nur ueberlagert und nicht veraendert.

Optionen:
  --analyse PFAD   analyse.json (Standard: neben folien.pdf)
  --akzent CODE    TUDa-Akzentfarbe (z. B. 9c), ueberschreibt die Kommentardatei
  --entwurf        fehlende Folien erlaubt (Platzhalter), fuer Zwischenstaende
  --nur 5-8        nur diese Folien bauen (Vorschau, impliziert --entwurf)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import folienlib as fl  # noqa: E402
import pymupdf  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, FrameBreak, Image,  # noqa: E402
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer)

MM = 72 / 25.4
SEITE_B, SEITE_H = 210 * MM, 297 * MM
RAND_L = RAND_R = 15 * MM          # TUDa A4: links/oben/rechts 15 mm, unten 20 mm
RAND_O, RAND_U = 15 * MM, 20 * MM
TEXT_B = SEITE_B - RAND_L - RAND_R
BALKEN_H, BALKEN_ABSTAND, LINIE_H = 4 * MM, 1.4 * MM, 1.2   # Identitaetsbalken A4
ABSCHLUSS_H = 0.6                                             # Abschlusslinie
SPALTE_ABSTAND = 6 * MM                                       # Spalten <= 90 mm
SPALTE_B = (TEXT_B - SPALTE_ABSTAND) / 2
FOLIE_OBEN = 28 * MM
FOLIE_MAX_UNTEN = SEITE_H / 2                                 # Folie bleibt in der oberen Haelfte
KOMMENTAR_ABSTAND = 6.5 * MM
TEXT_UNTEN = RAND_U + 4.5 * MM

GRUNDSCHRIFT = 9.6
ZEILENABSTAND = 13.0


# ---------------------------------------------------------------------------
# Schriften (Charter-Ersatz Charis SIL, Frontpage-Ersatz Roboto, Stafford-Ersatz Roboto Condensed)
# ---------------------------------------------------------------------------
def schriften_registrieren() -> dict:
    import matplotlib
    from fontTools.ttLib import TTFont as FTFont
    mpl = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
    eigene = {
        "Charis": "CharisSIL-Regular.ttf", "Charis-Bold": "CharisSIL-Bold.ttf",
        "Charis-Italic": "CharisSIL-Italic.ttf", "Charis-BoldItalic": "CharisSIL-BoldItalic.ttf",
        "Roboto": "Roboto-Regular.ttf", "Roboto-Medium": "Roboto-Medium.ttf",
        "Roboto-Bold": "Roboto-Bold.ttf", "Roboto-Italic": "Roboto-Italic.ttf",
        "RobotoCond": "RobotoCondensed-Regular.ttf", "RobotoCond-Bold": "RobotoCondensed-Bold.ttf",
    }
    ersatz = {
        "DVSerif": "DejaVuSerif.ttf", "DVSerif-Bold": "DejaVuSerif-Bold.ttf",
        "DVSerif-Italic": "DejaVuSerif-Italic.ttf", "DVSerif-BoldItalic": "DejaVuSerif-BoldItalic.ttf",
        "DVSans": "DejaVuSans.ttf", "DVSans-Bold": "DejaVuSans-Bold.ttf",
        "DVSans-Italic": "DejaVuSans-Oblique.ttf", "DVSans-BoldItalic": "DejaVuSans-BoldOblique.ttf",
        "DVMono": "DejaVuSansMono.ttf", "DVMono-Bold": "DejaVuSansMono-Bold.ttf",
        "DVMono-Italic": "DejaVuSansMono-Oblique.ttf", "DVMono-BoldItalic": "DejaVuSansMono-BoldOblique.ttf",
        "STIX": "STIXGeneral.ttf", "STIX-Bold": "STIXGeneralBol.ttf",
        "STIX-Italic": "STIXGeneralItalic.ttf", "STIX-BoldItalic": "STIXGeneralBolIta.ttf",
    }
    for name, datei in eigene.items():
        pfad = fl.FONT_DIR / datei
        if not pfad.exists():
            sys.exit(f"Schrift fehlt: {pfad}")
        pdfmetrics.registerFont(TTFont(name, str(pfad)))
    for name, datei in ersatz.items():
        pdfmetrics.registerFont(TTFont(name, str(mpl / datei)))
    for fam in ("Charis", "DVSerif", "DVSans", "DVMono", "STIX"):
        pdfmetrics.registerFontFamily(fam, normal=fam, bold=f"{fam}-Bold",
                                      italic=f"{fam}-Italic", boldItalic=f"{fam}-BoldItalic")
    pdfmetrics.registerFontFamily("Roboto", normal="Roboto", bold="Roboto-Bold",
                                  italic="Roboto-Italic", boldItalic="Roboto-Bold")
    pdfmetrics.registerFontFamily("RobotoCond", normal="RobotoCond", bold="RobotoCond-Bold",
                                  italic="RobotoCond", boldItalic="RobotoCond-Bold")
    pdfmetrics.registerFontFamily("Roboto-Medium", normal="Roboto-Medium", bold="Roboto-Bold",
                                  italic="Roboto-Medium", boldItalic="Roboto-Bold")
    cmaps = {}
    for fam, datei in (("serif", "CharisSIL-Regular.ttf"), ("sans", "Roboto-Regular.ttf")):
        cmaps[fam] = set(FTFont(str(fl.FONT_DIR / datei), lazy=True).getBestCmap())
    cmaps["DVSerif"] = set(FTFont(str(mpl / "DejaVuSerif.ttf"), lazy=True).getBestCmap())
    cmaps["DVSans"] = set(FTFont(str(mpl / "DejaVuSans.ttf"), lazy=True).getBestCmap())
    return cmaps


CMAPS: dict = {}


def schutz(text: str, art: str = "serif") -> str:
    """XML-Escaping plus Ersatzschrift fuer Zeichen, die Charis/Roboto nicht kennen."""
    haupt = CMAPS[art]
    ersatz1 = "DVSerif" if art == "serif" else "DVSans"
    aus = []
    for ch in text:
        e = ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if ord(ch) < 128 or ord(ch) in haupt or ch in "\n\t":
            aus.append(e)
        elif ord(ch) in CMAPS[ersatz1]:
            aus.append(f'<font face="{ersatz1}">{e}</font>')
        else:
            aus.append(f'<font face="STIX">{e}</font>')
    return "".join(aus)


# ---------------------------------------------------------------------------
# Formeln ($...$, $$...$$) ueber matplotlib-mathtext
# ---------------------------------------------------------------------------
class Formeln:
    def __init__(self, ordner: Path):
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["mathtext.fontset"] = "stix"
        self.ordner = ordner
        self.cache = {}

    def bild(self, ausdruck: str, groesse: float):
        from matplotlib import mathtext
        from matplotlib.font_manager import FontProperties
        from PIL import Image as PILImage
        schl = (ausdruck, groesse)
        if schl in self.cache:
            return self.cache[schl]
        name = hashlib.md5(f"{ausdruck}|{groesse}".encode()).hexdigest()[:16] + ".png"
        pfad = self.ordner / name
        dpi = 600
        try:
            tiefe = mathtext.math_to_image(f"${ausdruck}$", str(pfad), prop=FontProperties(size=groesse),
                                           dpi=dpi, format="png")
        except Exception as e:  # ungueltige Formel
            raise ValueError(f"Formel nicht darstellbar: ${ausdruck}$ ({e})")
        with PILImage.open(pfad) as im:
            w, h = im.size
        erg = (str(pfad), w / dpi * 72, h / dpi * 72, float(tiefe or 0))
        self.cache[schl] = erg
        return erg


FORMELN: Formeln | None = None


# ---------------------------------------------------------------------------
# Kommentardatei lesen
# ---------------------------------------------------------------------------
@dataclass
class Ziel:
    stil: str           # "marker" oder "rahmen"
    ausdruck: str       # z. B. b3, b4.2-4, i1, g2, text="..."#2, bereich=...
    quelle: str


@dataclass
class Schritt:
    titel: str
    ziele: list = field(default_factory=list)
    text: str = ""
    quelle: str = ""


@dataclass
class FolienKommentar:
    nr: int
    titel: str = ""
    text: str = ""
    schritte: list = field(default_factory=list)
    quelle: str = ""


KOPF_FOLIE = re.compile(r"^#\s+Folie\s+(\d+)\s*(?:[:|–—-]\s*(.*?))?\s*$", re.I)
KOPF_ZF = re.compile(r"^#\s+(?:Zusammenfassung|Fazit|Summary)\b\s*(?:[:|–—-]\s*(.*?))?\s*$", re.I)
KOPF_SCHRITT = re.compile(r"^##\s+(?:Schritt\s*\d*\s*[:|–—-]?\s*)?(.*?)\s*$", re.I)
DIREKTIVE = re.compile(r"^@(markiere|marker|rahmen)\s*:\s*(.+?)\s*$", re.I)


def lese_kommentare(pfad: Path):
    dateien = sorted(pfad.glob("*.md")) if pfad.is_dir() else [pfad]
    if not dateien:
        sys.exit(f"Keine Kommentardateien (*.md) in {pfad}")
    meta, folien, fehler = {}, {}, []
    zf = None   # Zusammenfassung am Ende: {"titel", "text", "quelle"}
    for datei in dateien:
        text = datei.read_text(encoding="utf-8")
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        zeilen = text.splitlines()
        i = 0
        if zeilen and zeilen[0].strip() == "---":
            j = 1
            while j < len(zeilen) and zeilen[j].strip() != "---":
                m = re.match(r"^\s*([A-Za-zäöüÄÖÜß_]+)\s*:\s*(.*?)\s*$", zeilen[j])
                if m:
                    meta[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")
                j += 1
            i = j + 1
        aktuell, schritt, in_zf = None, None, False
        for k in range(i, len(zeilen)):
            z = zeilen[k]
            ort = f"{datei.name}:{k + 1}"
            m = KOPF_FOLIE.match(z)
            if m:
                nr = int(m.group(1))
                if nr in folien:
                    fehler.append(f"{ort}: Folie {nr} ist doppelt kommentiert (auch {folien[nr].quelle})")
                aktuell = FolienKommentar(nr=nr, titel=(m.group(2) or "").strip(), quelle=ort)
                folien[nr] = aktuell
                schritt, in_zf = None, False
                continue
            m = KOPF_ZF.match(z)
            if m:
                if zf is not None:
                    fehler.append(f"{ort}: zweite Zusammenfassung (erste in {zf['quelle']})")
                zf = {"titel": (m.group(1) or "").strip(), "text": "", "quelle": ort}
                aktuell, schritt, in_zf = None, None, True
                continue
            if in_zf:
                if DIREKTIVE.match(z.strip()):
                    fehler.append(f"{ort}: In der Zusammenfassung gibt es keine Markierungen")
                    continue
                # "## Takeaways" ist hier eine Zwischenueberschrift, kein Schritt
                zf["text"] += (re.sub(r"^##\s+", "### ", z) if re.match(r"^##\s", z) else z) + "\n"
                continue
            if z.startswith("# ") and aktuell is None:
                continue  # Dokumenttitel o. Ae. vor der ersten Folie
            if re.match(r"^##\s", z):
                if aktuell is None:
                    fehler.append(f"{ort}: Schritt ohne vorangehende '# Folie N'-Überschrift")
                    continue
                m = KOPF_SCHRITT.match(z)
                schritt = Schritt(titel=m.group(1).strip(), quelle=ort)
                aktuell.schritte.append(schritt)
                continue
            m = DIREKTIVE.match(z.strip())
            if m:
                if schritt is None:
                    fehler.append(f"{ort}: Markierungen gehören in einen Schritt (## …), nicht auf die Überblicksseite")
                    continue
                stil = "rahmen" if m.group(1).lower() == "rahmen" else "marker"
                schritt.ziele.append(Ziel(stil=stil, ausdruck=m.group(2), quelle=ort))
                continue
            if aktuell is None:
                if z.strip():
                    fehler.append(f"{ort}: Text vor der ersten '# Folie N'-Überschrift wird ignoriert")
                continue
            if schritt is None:
                aktuell.text += z + "\n"
            else:
                schritt.text += z + "\n"
    return meta, folien, zf, fehler


# ---------------------------------------------------------------------------
# Markierungsziele aufloesen
# ---------------------------------------------------------------------------
ZIEL_TOKEN = re.compile(
    r"""\s*(?:
        (?P<text>text\s*=\s*(?:"(?P<t1>[^"]+)"|„(?P<t2>[^“”"]+)[“”"]|'(?P<t3>[^']+)')(?:\s*\#\s*(?P<nr>\d+))?)
      | (?P<bereich>bereich\s*=\s*(?P<b>[0-9.]+\s*,\s*[0-9.]+\s*,\s*[0-9.]+\s*,\s*[0-9.]+))
      | (?P<id>(?P<p1>[bgi])(?P<n1>\d+)(?:\.(?P<z1>\d+))?(?:\s*[-–]\s*(?P<p2>[bgi])?(?P<n2>\d+)(?:\.(?P<z2>\d+))?)?)
    )\s*[,;+]?""", re.X)


def ziele_aufloesen(ausdruck: str, page: pymupdf.Page, el: dict):
    """Gibt Liste (art, [Rects in Folienkoordinaten], beschreibung) zurueck."""
    seite = page.rect
    idx = fl.element_index(el)
    erg, pos, hinweise = [], 0, []
    rest = ausdruck.strip()
    while pos < len(rest):
        m = ZIEL_TOKEN.match(rest, pos)
        if not m or m.end() == pos:
            raise ValueError(f"Unverständliches Ziel ab '{rest[pos:]}'. Erlaubt: b3, b3.2, b3-b5, b4.2-4, i1, g2, "
                             f'text="…", text="…"#2, bereich=x0,y0,x1,y1')
        pos = m.end()
        if m.group("text"):
            suche = m.group("t1") or m.group("t2") or m.group("t3")
            flags = (pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP)
            treffer = page.search_for(suche, flags=flags)
            treffer = sorted(treffer, key=lambda r: (round(r.y0, 0), r.x0))
            if not treffer:
                raise ValueError(f'text="{suche}" kommt auf der Folie nicht vor (Textebene prüfen, sonst b-ID oder bereich= nutzen)')
            if m.group("nr"):
                n = int(m.group("nr"))
                if not 1 <= n <= len(treffer):
                    raise ValueError(f'text="{suche}"#{n}: nur {len(treffer)} Treffer')
                treffer = [treffer[n - 1]]
            elif len(treffer) > 1:
                hinweise.append(f'text="{suche}" hat {len(treffer)} Treffer, alle markiert (mit #n eingrenzen)')
            erg.append(("text", list(treffer), f'„{suche}“'))
        elif m.group("bereich"):
            werte = [float(v) for v in m.group("b").split(",")]
            x0, y0, x1, y1 = werte
            if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
                raise ValueError(f"bereich={m.group('b')}: Werte müssen 0 ≤ x0 < x1 ≤ 1 und 0 ≤ y0 < y1 ≤ 1 erfüllen")
            erg.append(("bereich", [fl.denorm(werte, seite)], f"Bereich {m.group('b')}"))
        else:
            p1, n1, z1 = m.group("p1"), int(m.group("n1")), m.group("z1")
            p2, n2, z2 = m.group("p2"), m.group("n2"), m.group("z2")
            ids = []
            if n2 is None:
                ids = [f"{p1}{n1}" + (f".{z1}" if z1 else "")]
            elif z1 is not None:
                # b4.2-4 oder b4.2-b4.4: Zeilen innerhalb eines Blocks
                if z2 is not None:
                    if int(n2) != n1:
                        raise ValueError(f"{m.group('id')}: Zeilenbereiche nur innerhalb eines Blocks")
                    ende = int(z2)
                else:
                    if p2 is not None:
                        raise ValueError(f"{m.group('id')}: unklar – Zeilenbereich als b4.2-4 oder b4.2-b4.4 angeben")
                    ende = int(n2)
                ids = [f"{p1}{n1}.{k}" for k in range(int(z1), ende + 1)]
            else:
                if p2 and p2 != p1:
                    raise ValueError(f"{m.group('id')}: Bereich über verschiedene Elementarten")
                ids = [f"{p1}{k}" for k in range(n1, int(n2) + 1)]
            boxen, art = [], "text"
            for i in ids:
                if i not in idx:
                    vorhanden = ", ".join(fl.schreibe_sortiert_ids([k for k in idx if "." not in k])[:40])
                    raise ValueError(f"{i} gibt es auf dieser Folie nicht (vorhanden: {vorhanden})")
                art = idx[i]["art"]
                boxen.extend(fl.denorm(b, seite) for b in idx[i]["boxen"])
            erg.append((art, boxen, ",".join(ids)))
    return erg, hinweise


# ---------------------------------------------------------------------------
# Markdown-Teilmenge -> Flowables
# ---------------------------------------------------------------------------
class Stile:
    def __init__(self, akzent: dict, sprache: str):
        silbentrennung = {}
        try:
            import pyphen  # noqa: F401
            silbentrennung = dict(hyphenationLang={"de": "de_DE", "en": "en_US"}.get(sprache, sprache),
                                  embeddedHyphenation=1, uriWasteReduce=0.3)
        except ImportError:
            print("Hinweis: pyphen fehlt – ohne Silbentrennung (pip install --break-system-packages pyphen)")
        self.akzent_text = colors.HexColor(akzent["text"])
        self.akzent_balken = colors.HexColor(akzent["balken"])
        self.text = ParagraphStyle("text", fontName="Charis", fontSize=GRUNDSCHRIFT, leading=ZEILENABSTAND,
                                   alignment=TA_LEFT, spaceAfter=4.2, textColor=colors.black, **silbentrennung)
        self.liste = ParagraphStyle("liste", parent=self.text, leftIndent=11, bulletIndent=1.5, spaceAfter=2.2,
                                    bulletFontName="Charis", bulletColor=self.akzent_text)
        self.liste2 = ParagraphStyle("liste2", parent=self.liste, leftIndent=22, bulletIndent=12.5)
        self.zwischen = ParagraphStyle("zwischen", fontName="Roboto-Medium", fontSize=9.8, leading=12.5,
                                       spaceBefore=3, spaceAfter=2.2, textColor=colors.black, keepWithNext=1)
        self.merke = ParagraphStyle("merke", parent=self.text, spaceAfter=0)
        self.titel = ParagraphStyle("titel", fontName="Roboto-Medium", fontSize=13, leading=16,
                                    textColor=colors.black, spaceAfter=5.5)
        self.platzhalter = ParagraphStyle("platz", parent=self.text, fontName="Charis-Italic",
                                          textColor=colors.HexColor(fl.TUDA["0d"]))


SPRACHE = "de"
SCHUTZ_TOKEN = re.compile(r"(\$[^$\n]+?\$|`[^`\n]+`)")


def typografie(text: str) -> str:
    """Gerade Anfuehrungszeichen -> „…“ (de) bzw. “…” (en), ' - ' -> ' – ', '...' -> '…'."""
    teile = SCHUTZ_TOKEN.split(text)
    auf, zu = ("„", "“") if SPRACHE == "de" else ("“", "”")
    for i in range(0, len(teile), 2):
        t = teile[i]
        t = re.sub(r'„([^"“”\n]*)"', lambda m: f"„{m.group(1)}“", t)
        t = re.sub(r'(^|[\s(\[/–-])"([^"\n]+?)"', lambda m: f"{m.group(1)}{auf}{m.group(2)}{zu}", t)
        t = re.sub(r"(?<=\S[ \t])-(?=[ \t])", "–", t)   # nicht am Zeilenanfang (Listen)
        t = t.replace("...", "…")
        t = re.sub(r"\b(Folien?|S\.|Seite|Schritt|Abb\.|Kap\.) (?=\d)", "\\1\u00a0", t)   # „Folie 8“ nicht trennen
        teile[i] = t
    return "".join(teile)


INLINE_HOEHE = [0.0]   # hoechste Inline-Formel des zuletzt gesetzten Absatzes


def absatz(markup: str, stil: ParagraphStyle, **kw) -> Paragraph:
    """Paragraph mit festem Zeilenabstand; nur bei hohen Inline-Formeln waechst die Zeile mit."""
    if INLINE_HOEHE[0] > ZEILENABSTAND * 0.95:
        stil = ParagraphStyle(stil.name + "_auto", parent=stil, autoLeading="max")
    INLINE_HOEHE[0] = 0.0
    return Paragraph(markup, stil, **kw)


INLINE = re.compile(r"(\$[^$\n]+?\$|`[^`\n]+`|\*\*[^*\n]+?\*\*|(?<![\w*])\*[^*\n]+?\*(?!\w)|(?<![\w_])_[^_\n]+?_(?![\w_]))")


def inline(text: str, groesse: float = GRUNDSCHRIFT, art: str = "serif") -> str:
    """Wandelt **fett**, *kursiv*, `code` und $Formel$ in ReportLab-Markup."""
    aus, pos = [], 0
    for m in INLINE.finditer(text):
        aus.append(schutz(text[pos:m.start()], art))
        t = m.group(0)
        if t.startswith("$"):
            pfad, w, h, tiefe = FORMELN.bild(t[1:-1], groesse)
            INLINE_HOEHE[0] = max(INLINE_HOEHE[0], h)
            aus.append(f'<img src="{pfad}" width="{w:.2f}" height="{h:.2f}" valign="{-tiefe:.2f}"/>')
        elif t.startswith("`"):
            aus.append(f'<font face="DVMono" size="{groesse * 0.88:.1f}">{schutz(t[1:-1], "sans")}</font>')
        elif t.startswith("**"):
            aus.append(f"<b>{inline(t[2:-2], groesse, art)}</b>")
        else:
            aus.append(f"<i>{inline(t[1:-1], groesse, art)}</i>")
        pos = m.end()
    aus.append(schutz(text[pos:], art))
    return "".join(aus)


class Merkekasten(Flowable):
    """Kernaussage mit Akzentlinie links (Charter-Text bleibt schwarz)."""

    def __init__(self, inhalt: list, farbe, breite_linie=2.2, abstand=7):
        super().__init__()
        self.inhalt, self.farbe, self.lw, self.abstand = inhalt, farbe, breite_linie, abstand

    def wrap(self, aw, ah):
        self._w = aw
        h = 0
        self._teile = []
        for f in self.inhalt:
            w, fh = f.wrap(aw - self.abstand - self.lw, ah)
            self._teile.append((f, fh))
            h += fh + f.getSpaceAfter()
        self._h = h - (self.inhalt[-1].getSpaceAfter() if self.inhalt else 0) + 4
        return aw, self._h

    def draw(self):
        c = self.canv
        c.setFillColor(self.farbe)
        c.rect(0, 0, self.lw, self._h, stroke=0, fill=1)
        y = self._h - 2
        for f, fh in self._teile:
            y -= fh
            f.drawOn(c, self.lw + self.abstand, y)
            y -= f.getSpaceAfter()

    def getSpaceBefore(self):
        return 3

    def getSpaceAfter(self):
        return 6


def markdown_flowables(text: str, stile: Stile, breite: float) -> list:
    zeilen = typografie(text.strip("\n")).splitlines()
    flows, puffer, i = [], [], 0
    listenpunkt = re.compile(r"^(\s*)([-*•–]|\d+[.)])\s+(.*)$")

    def puffer_leeren():
        if puffer:
            flows.append(absatz(inline(" ".join(t.strip() for t in puffer)), stile.text))
            puffer.clear()

    while i < len(zeilen):
        z = zeilen[i]
        s = z.strip()
        if not s:
            puffer_leeren()
            i += 1
            continue
        if s.startswith("$$"):
            puffer_leeren()
            inhalt = s[2:]
            while not inhalt.rstrip().endswith("$$") and i + 1 < len(zeilen):
                i += 1
                inhalt += " " + zeilen[i].strip()
            inhalt = inhalt.rstrip()[:-2].strip()
            pfad, w, h, _ = FORMELN.bild(inhalt, GRUNDSCHRIFT * 1.12)
            if w > breite:
                h, w = h * breite / w, breite
            bild = Image(pfad, width=w, height=h)
            bild.hAlign = "CENTER"
            flows.extend([Spacer(1, 2), bild, Spacer(1, 5)])
            i += 1
            continue
        if s.startswith("### "):
            puffer_leeren()
            flows.append(Paragraph(inline(s[4:], 9.8, "sans"), stile.zwischen))
            i += 1
            continue
        if s.startswith(">"):
            puffer_leeren()
            teile = []
            while i < len(zeilen) and zeilen[i].strip().startswith(">"):
                teile.append(zeilen[i].strip()[1:].strip())
                i += 1
            flows.append(Merkekasten([absatz(inline(" ".join(t for t in teile if t)), stile.merke)],
                                     stile.akzent_balken))
            continue
        m = listenpunkt.match(z)
        if m:
            puffer_leeren()
            einzug = len(m.group(1).replace("\t", "    "))
            marke, inhalt = m.group(2), m.group(3)
            i += 1
            while (i < len(zeilen) and zeilen[i].strip() and not listenpunkt.match(zeilen[i])
                   and zeilen[i][:1] in (" ", "\t")):
                inhalt += " " + zeilen[i].strip()
                i += 1
            stil = stile.liste2 if einzug >= 2 else stile.liste
            if i >= len(zeilen) or not listenpunkt.match(zeilen[i]):
                stil = ParagraphStyle(stil.name + "_ende", parent=stil, spaceAfter=stile.text.spaceAfter)
            bullet = "•" if not marke[0].isdigit() else marke.rstrip(".)") + "."
            flows.append(absatz(inline(inhalt), stil, bulletText=bullet))
            continue
        puffer.append(z)
        i += 1
    puffer_leeren()
    return flows


# ---------------------------------------------------------------------------
# Seitenaufbau
# ---------------------------------------------------------------------------
class Zustand:
    def __init__(self):
        self.aktuell = None
        self.marke_auf_seite = False
        self.seitenplan = []


ZUSTAND = Zustand()


class SeitenMarke(Flowable):
    def __init__(self, info: dict):
        super().__init__()
        self.info = info

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        ZUSTAND.aktuell = self.info
        ZUSTAND.marke_auf_seite = True


class Kennung(Flowable):
    """Kleine Zeile 'FOLIE 5 · SCHRITT 2 VON 4' mit Fortschrittspunkten."""

    def __init__(self, text: str, farbe, punkte: int = 0, aktiv: int = 0):
        super().__init__()
        self.text, self.farbe, self.punkte, self.aktiv = text, farbe, punkte, aktiv

    def wrap(self, aw, ah):
        return aw, 11

    def draw(self):
        c = self.canv
        c.setFillColor(self.farbe)
        c.setFont("RobotoCond-Bold", 7.6)
        t = c.beginText(0, 2.2)
        t.setCharSpace(0.55)
        t.textOut(self.text.upper())
        c.drawText(t)
        breite = pdfmetrics.stringWidth(self.text.upper(), "RobotoCond-Bold", 7.6) + 0.55 * len(self.text)
        x = breite + 7
        for k in range(1, self.punkte + 1):
            c.setStrokeColor(self.farbe)
            c.setLineWidth(0.7)
            c.circle(x + 2.3, 4.6, 2.3, stroke=1, fill=1 if k == self.aktiv else 0)
            x += 7.2


def folien_rechteck(w: float, h: float) -> tuple[float, float, float, float]:
    """Groesstmoegliche Folie in der oberen Haelfte, auf 0,5-pt-Raster ausgerichtet."""
    max_h = FOLIE_MAX_UNTEN - FOLIE_OBEN
    s = min(TEXT_B / w, max_h / h)
    bw, bh = w * s, h * s
    x0 = round((RAND_L + (TEXT_B - bw) / 2) * 2) / 2
    y0 = round(FOLIE_OBEN * 2) / 2
    return x0, y0, bw, bh


ZF_OBEN = 30 * MM     # Zusammenfassungsseite: Titel beginnt unter der Kopfzeile
ZF_TITEL_H = 13 * MM  # volle Breite fuer Kennung und Titel, darunter die Spalten


def spalten_rahmen(oben: float, gid: str, spalten: int) -> list:
    """Textrahmen unter der Folie. Zwei Spalten (je <= 90 mm, TUDa) werden nacheinander
    gefuellt: Der Text laeuft die linke Spalte hinab und wechselt erst in die rechte,
    wenn links kein Platz mehr ist – es wird nicht ausgeglichen."""
    hoehe = SEITE_H - oben - TEXT_UNTEN
    kw = dict(leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    if spalten == 1:
        return [Frame(RAND_L, TEXT_UNTEN, TEXT_B, hoehe, id=f"t_{gid}", **kw)]
    return [Frame(RAND_L, TEXT_UNTEN, SPALTE_B, hoehe, id=f"l_{gid}", **kw),
            Frame(RAND_L + SPALTE_B + SPALTE_ABSTAND, TEXT_UNTEN, SPALTE_B, hoehe, id=f"r_{gid}", **kw)]


class KommentarDokument(BaseDocTemplate):
    def __init__(self, pfad, geometrien: dict, erste: str, kopf_links: str, fuss: str,
                 folienzahl: int, akzent: dict, spalten: int = 2, **kw):
        super().__init__(str(pfad), pagesize=(SEITE_B, SEITE_H), leftMargin=RAND_L, rightMargin=RAND_R,
                         topMargin=RAND_O, bottomMargin=RAND_U, **kw)
        self.kopf_links, self.fuss, self.folienzahl = kopf_links, fuss, folienzahl
        self.akzent = akzent
        vorlagen = []
        for gid, (x0, y0, bw, bh) in geometrien.items():
            oben = y0 + bh + KOMMENTAR_ABSTAND
            vorlagen.append(PageTemplate(id=gid, frames=spalten_rahmen(oben, gid, spalten),
                                         onPageEnd=self.seitenende))
        titelrahmen = Frame(RAND_L, SEITE_H - ZF_OBEN - ZF_TITEL_H, TEXT_B, ZF_TITEL_H, id="zf_titel",
                            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        vorlagen.append(PageTemplate(id="zusammenfassung",
                                     frames=[titelrahmen] + spalten_rahmen(ZF_OBEN + ZF_TITEL_H, "zf", spalten),
                                     onPageEnd=self.seitenende))
        vorlagen.sort(key=lambda v: v.id != erste)
        self.addPageTemplates(vorlagen)

    def seitenende(self, c, doc):
        info = ZUSTAND.aktuell
        fortsetzung = not ZUSTAND.marke_auf_seite
        ZUSTAND.marke_auf_seite = False
        seite = c.getPageNumber()
        rest_rechts = 0.0
        rahmen = getattr(doc, "frame", None)
        if rahmen is not None and rahmen.id.startswith("r_"):
            rest_rechts = (rahmen._y1 + rahmen._height) - rahmen._y   # belegte Hoehe rechts
        ZUSTAND.seitenplan.append({**info, "seite": seite, "fortsetzung": fortsetzung,
                                   "rechts_belegt": rest_rechts})
        c.saveState()
        # Identitaetsbalken: Balken in Akzentfarbe, Abstand, schwarze Linie
        oben = SEITE_H - RAND_O
        c.setFillColor(colors.HexColor(self.akzent["balken"]))
        c.rect(RAND_L, oben - BALKEN_H, TEXT_B, BALKEN_H, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.rect(RAND_L, oben - BALKEN_H - BALKEN_ABSTAND - LINIE_H, TEXT_B, LINIE_H, stroke=0, fill=1)
        # Infozeile (Stafford-Ersatz)
        c.setFont("RobotoCond", 7.6)
        grund = SEITE_H - 24.6 * MM
        if info["art"] == "zusammenfassung":
            rechts = "Zusammenfassung"
        else:
            rechts = f"Folie {info['folie']} von {self.folienzahl}"
        if fortsetzung:
            rechts += " · Fortsetzung"
        platz = TEXT_B - pdfmetrics.stringWidth(rechts, "RobotoCond", 7.6) - 8 * MM
        links = self.kopf_links
        while links and pdfmetrics.stringWidth(links, "RobotoCond", 7.6) > platz:
            links = links[:-2].rstrip() + "…"
        c.drawString(RAND_L, grund, links)
        c.drawRightString(RAND_L + TEXT_B, grund, rechts)
        # Feiner Rahmen um die Folie, ausserhalb der Folienflaeche
        if info.get("rect"):
            x0, y0, bw, bh = info["rect"]
            c.setStrokeColor(colors.HexColor(fl.TUDA["0b"]))
            c.setLineWidth(0.5)
            c.rect(x0 - 0.85, SEITE_H - y0 - bh - 0.85, bw + 1.7, bh + 1.7, stroke=1, fill=0)
        # Abschlusslinie und Paginierung
        c.setFillColor(colors.black)
        c.rect(RAND_L, RAND_U - ABSCHLUSS_H, TEXT_B, ABSCHLUSS_H, stroke=0, fill=1)
        c.setFont("Roboto-Medium", 8)
        c.drawRightString(RAND_L + TEXT_B, RAND_U - 4.6 * MM, str(seite))
        c.setFont("RobotoCond", 7)
        c.drawString(RAND_L, RAND_U - 4.6 * MM, self.fuss)
        c.restoreState()


# ---------------------------------------------------------------------------
# Markierungen als eigene Ebene (Optional Content), Multiplikationsmodus
# ---------------------------------------------------------------------------
def _rund_rect_pfad(x0, y0, x1, y1, r, seiten_h) -> str:
    """Abgerundetes Rechteck als PDF-Pfad (PDF-Koordinaten, y nach oben)."""
    Y0, Y1 = seiten_h - y1, seiten_h - y0
    r = max(0.0, min(r, (x1 - x0) / 2, (Y1 - Y0) / 2))
    k = 0.5523 * r
    return (f"{x0 + r:.3f} {Y0:.3f} m {x1 - r:.3f} {Y0:.3f} l "
            f"{x1 - r + k:.3f} {Y0:.3f} {x1:.3f} {Y0 + r - k:.3f} {x1:.3f} {Y0 + r:.3f} c "
            f"{x1:.3f} {Y1 - r:.3f} l {x1:.3f} {Y1 - r + k:.3f} {x1 - r + k:.3f} {Y1:.3f} {x1 - r:.3f} {Y1:.3f} c "
            f"{x0 + r:.3f} {Y1:.3f} l {x0 + r - k:.3f} {Y1:.3f} {x0:.3f} {Y1 - r + k:.3f} {x0:.3f} {Y1 - r:.3f} c "
            f"{x0:.3f} {Y0 + r:.3f} l {x0:.3f} {Y0 + r - k:.3f} {x0 + r - k:.3f} {Y0:.3f} {x0 + r:.3f} {Y0:.3f} c h ")


def _ressource_setzen(doc: pymupdf.Document, page: pymupdf.Page, kategorie: str, name: str, wert: str):
    """Traegt einen Eintrag in /Resources/<kategorie> ein, auch wenn Teile indirekt sind."""
    typ, val = doc.xref_get_key(page.xref, "Resources")
    if typ == "xref":
        basis, praefix = int(val.split()[0]), ""
    else:
        basis, praefix = page.xref, "Resources/"
    t2, v2 = doc.xref_get_key(basis, praefix + kategorie)
    if t2 == "xref":
        doc.xref_set_key(int(v2.split()[0]), name, wert)
    else:
        doc.xref_set_key(basis, praefix + kategorie + "/" + name, wert)


def kanten_farbe(code: str) -> str:
    """Kraeftigere Stufe desselben Farbtons fuer die Kante eines Kastens (6a -> 6b)."""
    stufe = {"a": "b", "b": "c", "c": "d", "d": "d"}
    kante = code[:-1] + stufe.get(code[-1], "b")
    return fl.TUDA.get(kante, fl.TUDA[code])


KASTEN_DECKKRAFT = 0.45   # Flaeche eines Kastens: Marker-Gelb, halb deckend, multiplizierend
KASTEN_ABSTAND = 5.0      # Abstand des Kastens zum markierten Element (pt auf der Seite)


def markierungen_zeichnen(doc: pymupdf.Document, page: pymupdf.Page, ocg: int, formen: list,
                          marker_code: str):
    """formen: Liste (stil, art, Rect in Seitenkoordinaten, zeilenhoehe).

    Beide Stile sind gelb wie ein Textmarker: "marker" deckt Text zeilenweise voll ein,
    "rahmen" legt einen hellgelben Kasten mit kraeftigerer gelber Kante um ein Element.
    Alles liegt in der Ebene "Markierungen"; die Folie darunter bleibt unveraendert.
    """
    if not formen:
        return
    h = page.rect.height
    gelb = fl.hex_rgb(fl.TUDA[marker_code])
    kante = fl.hex_rgb(kanten_farbe(marker_code))
    teile = ["/OC /FkMark BDC q"]
    marker = [f for f in formen if f[0] == "marker"]
    kaesten = [f for f in formen if f[0] == "rahmen"]
    if kaesten:
        flaeche = "".join(_rund_rect_pfad(r.x0 - KASTEN_ABSTAND, r.y0 - KASTEN_ABSTAND, r.x1 + KASTEN_ABSTAND,
                                          r.y1 + KASTEN_ABSTAND, 3.5, h) for _, _, r, _ in kaesten)
        teile.append(f"/FkKasten gs {gelb[0]:.4f} {gelb[1]:.4f} {gelb[2]:.4f} rg {flaeche}f")
    if marker:
        pfad = []
        for _, art, rect, zh in marker:
            if art == "text":
                px, py = 0.14 * zh + 0.6, 0.08 * zh + 0.4
                rad = min(2.2, zh * 0.18)
            else:
                px = py = 2.0
                rad = 2.5
            pfad.append(_rund_rect_pfad(rect.x0 - px, rect.y0 - py, rect.x1 + px, rect.y1 + py, rad, h))
        teile.append(f"/FkMul gs {gelb[0]:.4f} {gelb[1]:.4f} {gelb[2]:.4f} rg " + "".join(pfad) + "f")
    if kaesten:
        teile.append(f"/FkNorm gs {kante[0]:.4f} {kante[1]:.4f} {kante[2]:.4f} RG 1.4 w 1 j")
        for _, _, r, _ in kaesten:
            teile.append(_rund_rect_pfad(r.x0 - KASTEN_ABSTAND, r.y0 - KASTEN_ABSTAND, r.x1 + KASTEN_ABSTAND,
                                         r.y1 + KASTEN_ABSTAND, 3.5, h) + "S")
    teile.append("Q EMC")
    if not page.is_wrapped:
        page.wrap_contents()
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, "\n".join(teile).encode())
    inhalte = page.get_contents() + [xref]
    doc.xref_set_key(page.xref, "Contents", "[" + " ".join(f"{x} 0 R" for x in inhalte) + "]")
    _ressource_setzen(doc, page, "ExtGState", "FkMul", "<</Type/ExtGState/BM/Multiply/ca 1/CA 1>>")
    _ressource_setzen(doc, page, "ExtGState", "FkKasten",
                      f"<</Type/ExtGState/BM/Multiply/ca {KASTEN_DECKKRAFT}/CA 1>>")
    _ressource_setzen(doc, page, "ExtGState", "FkNorm", "<</Type/ExtGState/BM/Normal/ca 1/CA 1>>")
    _ressource_setzen(doc, page, "Properties", "FkMark", f"{ocg} 0 R")


# ---------------------------------------------------------------------------
# Hauptablauf
# ---------------------------------------------------------------------------
def bereich_liste(text: str, n: int) -> tuple[set, bool]:
    """'5-8,12,zf' -> ({5,6,7,8,12}, True); 'zf' steht fuer die Zusammenfassung."""
    aus, mit_zf = set(), False
    for teil in text.split(","):
        teil = teil.strip().lower()
        if teil in ("zf", "zusammenfassung"):
            mit_zf = True
        elif "-" in teil:
            a, b = teil.split("-")
            aus.update(range(int(a), int(b) + 1))
        elif teil:
            aus.add(int(teil))
    return {x for x in aus if 1 <= x <= n}, mit_zf


def fett_mehrfach(kommentare: dict) -> dict:
    """Begriffe, die auf mehreren Folien fett gesetzt sind (Hinweis auf Wiederholungen)."""
    fett = {}
    for nr, k in kommentare.items():
        for t in [k.text] + [s.text for s in k.schritte]:
            t = "\n".join(z for z in t.splitlines() if not z.lstrip().startswith(">"))   # Merke-Kaesten
            for m in re.finditer(r"\*\*([^*\n]+?)\*\*", t):
                begriff = m.group(1).strip().rstrip(":").lower()
                if len(begriff) > 2:
                    fett.setdefault(begriff, set()).add(nr)
    return {b: sorted(v) for b, v in fett.items() if len(v) > 1}


def woerter(text: str) -> int:
    return len(re.findall(r"\w+", re.sub(r"\$[^$]*\$", " x ", text)))


def main():
    global FORMELN, CMAPS, SPRACHE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folien", required=True, help="Folien-PDF (aus der Analyse: arbeit/folien.pdf)")
    ap.add_argument("--kommentar", required=True, help="Kommentardatei .md oder Ordner mit *.md")
    ap.add_argument("--out", required=True, help="Ausgabe-PDF")
    ap.add_argument("--analyse", help="analyse.json (Standard: neben der Folien-PDF)")
    ap.add_argument("--akzent", help="TUDa-Akzentfarbe, z. B. 9c (Standard: Kommentardatei, sonst erkannt)")
    ap.add_argument("--entwurf", action="store_true", help="fehlende Folien mit Platzhalter füllen")
    ap.add_argument("--nur", help="nur diese Folien bauen, z. B. 5-8 oder 5-8,zf (zf = Zusammenfassung)")
    a = ap.parse_args()

    folien_pfad = Path(a.folien)
    src = pymupdf.open(folien_pfad)
    n = len(src)
    analyse_pfad = Path(a.analyse) if a.analyse else folien_pfad.parent / "analyse.json"
    analyse = None
    if analyse_pfad.exists():
        analyse = json.loads(analyse_pfad.read_text(encoding="utf-8"))
        if analyse.get("quelle", {}).get("sha256") != fl.sha256(folien_pfad):
            print("Hinweis: analyse.json gehört zu einer anderen PDF – Elemente werden neu bestimmt.")
            analyse = None
    if analyse is None:
        el_alle = fl.analysiere_dokument(src)
        folien_el = [{"bloecke": e["bloecke"], "bilder": e["bilder"], "grafiken": e["grafiken"],
                      "titel": e["titel"]} for e in el_alle]
        akzent_erkannt = fl.STANDARD_AKZENT
    else:
        folien_el = analyse["folien"]
        akzent_erkannt = analyse.get("akzent", {}).get("code", fl.STANDARD_AKZENT)

    meta, kommentare, zf, fehler = lese_kommentare(Path(a.kommentar))
    if a.nur:
        auswahl, mit_zf = bereich_liste(a.nur, n)
    else:
        auswahl, mit_zf = set(range(1, n + 1)), True
    entwurf = a.entwurf or bool(a.nur)
    if zf is None and not entwurf:
        fehler.append("Zusammenfassung fehlt: am Ende einen Abschnitt '# Zusammenfassung' mit Kurzfassung, "
                      "Takeaways und Kernbegriffen anlegen")
    spalten = 1 if str(meta.get("spalten", "2")).strip() == "1" else 2
    for nr in sorted(kommentare):
        if not 1 <= nr <= n:
            fehler.append(f"{kommentare[nr].quelle}: Folie {nr} existiert nicht (Foliensatz hat {n} Folien)")
    fehlend = [nr for nr in range(1, n + 1) if nr not in kommentare and nr in auswahl]
    if fehlend and not entwurf:
        fehler.append("Ohne Kommentar: Folie " + ", ".join(map(str, fehlend)) +
                      " – jede Folie braucht mindestens eine Seite (für Zwischenstände --entwurf)")

    akzent_code = (a.akzent or meta.get("akzent") or "auto").lower().replace("tuda-", "")
    if akzent_code in ("", "auto"):
        akzent_code = akzent_erkannt
    if akzent_code not in fl.TUDA:
        fehler.append(f"Akzentfarbe '{akzent_code}' ist keine TUDa-Farbe (0a–0d, 1a–11d)")
        akzent_code = fl.STANDARD_AKZENT
    marker_code = meta.get("marker", fl.STANDARD_MARKER).lower().replace("tuda-", "")
    if marker_code not in fl.TUDA:
        fehler.append(f"Markerfarbe '{marker_code}' ist keine TUDa-Farbe")
        marker_code = fl.STANDARD_MARKER
    akzent = fl.akzent_rollen(akzent_code)
    sprache = meta.get("sprache", "de").lower()[:2]
    SPRACHE = sprache

    CMAPS = schriften_registrieren()
    from reportlab import rl_config
    rl_config.canvas_basefontname = "Charis"   # sonst verweist jede Seite auf ein nicht eingebettetes Helvetica
    tmp = Path(tempfile.mkdtemp(prefix="folienkommentar_"))
    FORMELN = Formeln(tmp)
    stile = Stile(akzent, sprache)

    # Markierungen aufloesen (vor dem Layout, damit Fehler frueh auffallen)
    hinweise = []
    markierungen = {}   # (folie, schritt) -> Liste (stil, art, Rect Folienkoordinaten, zeilenhoehe)
    for nr, k in sorted(kommentare.items()):
        if not 1 <= nr <= n or nr not in auswahl:
            continue
        page = src[nr - 1]
        if page.rotation:
            fehler.append(f"Folie {nr}: Seite ist gedreht – bitte die folien.pdf aus folien_analyse.py verwenden")
        el = folien_el[nr - 1]
        einrast = fl.einrast_elemente(el, page.rect)
        massstab = folien_rechteck(page.rect.width, page.rect.height)[2] / page.rect.width
        if k.schritte and not k.text.strip():
            hinweise.append(f"Folie {nr}: Überblicksseite ohne Text – kurz einordnen, was die Schritte zeigen")
        for si, s in enumerate(k.schritte, 1):
            if not s.ziele:
                fehler.append(f"{s.quelle}: Schritt „{s.titel}“ hat keine Markierung (@markiere: … oder @rahmen: …)")
                continue
            formen = []
            for z in s.ziele:
                try:
                    teile, hw = ziele_aufloesen(z.ausdruck, page, el)
                except ValueError as e:
                    fehler.append(f"{z.quelle}: Folie {nr}: {e}")
                    continue
                hinweise.extend(f"{z.quelle}: {x}" for x in hw)
                for art, rects, _ in teile:
                    if z.stil == "rahmen" or art != "text":
                        # ein umschliessendes Rechteck je Element (Rahmen um den ganzen Block)
                        u = pymupdf.Rect(rects[0])
                        for r in rects[1:]:
                            u |= r
                        if art == "bereich" or z.stil == "rahmen":
                            pad_aus = KASTEN_ABSTAND if z.stil == "rahmen" else 2.0
                            u = fl.einrasten(u, einrast, pad_aus / massstab + 0.5)
                        rects = [u]
                    for r in rects:
                        formen.append((z.stil, art, pymupdf.Rect(r), pymupdf.Rect(r).height))
            markierungen[(nr, si)] = formen
            if not s.text.strip():
                fehler.append(f"{s.quelle}: Schritt „{s.titel}“ ohne Kommentartext")

    if fehler:
        print("FEHLER – nichts gebaut:")
        for f in fehler:
            print("  - " + f)
        sys.exit(1)

    # Geometrie je Folie und Seitenvorlagen
    geometrien, folien_geo = {}, {}
    for nr in range(1, n + 1):
        r = src[nr - 1].rect
        g = folien_rechteck(r.width, r.height)
        gid = f"g{g[2]:.2f}x{g[3]:.2f}"
        geometrien[gid] = g
        folien_geo[nr] = (gid, g)

    titel = meta.get("titel", "")
    veranstaltung = meta.get("veranstaltung", "")
    kopf_links = " · ".join(t for t in (veranstaltung, titel) if t) or folien_pfad.stem
    fuss = meta.get("fusszeile", "Kommentierter Foliensatz · Erläuterungen KI-generiert, nicht vom Lehrstuhl geprüft")

    story, erste, statistik = [], None, []
    spaltenbreite = SPALTE_B if spalten == 2 else TEXT_B
    for nr in sorted(auswahl):
        k = kommentare.get(nr)
        gid, g = folien_geo[nr]
        folientitel = (k.titel if k and k.titel else "") or folien_el[nr - 1].get("titel", "") or f"Folie {nr}"
        seiten = [("ueberblick", 0, folientitel, k.text if k else "")]
        if k:
            seiten += [("schritt", si, s.titel or f"Schritt {si}", s.text) for si, s in enumerate(k.schritte, 1)]
        anzahl_schritte = len(seiten) - 1
        for art, si, ueberschrift, text in seiten:
            info = {"folie": nr, "art": art, "schritt": si, "schritte": anzahl_schritte,
                    "titel": ueberschrift, "folientitel": folientitel, "rect": g, "gid": gid}
            if erste is None:
                erste = gid
            else:
                story.append(NextPageTemplate(gid))
                story.append(PageBreak())
            story.append(SeitenMarke(info))
            if art == "ueberblick":
                zusatz = " · Überblick" if anzahl_schritte else ""
                aufbau = folien_el[nr - 1].get("aufbau")
                if aufbau and not anzahl_schritte:
                    zusatz = f" · Aufbaustufe {aufbau['stufe']} von {aufbau['von']}"
                kennung = Kennung(f"Folie {nr}{zusatz}", stile.akzent_text, anzahl_schritte, 0)
            else:
                kennung = Kennung(f"Folie {nr} · Schritt {si} von {anzahl_schritte}", stile.akzent_text,
                                  anzahl_schritte, si)
            kopf = [kennung, Paragraph(inline(typografie(ueberschrift), 13, "sans"), stile.titel)]
            if text.strip():
                flows = markdown_flowables(text, stile, spaltenbreite)
            else:
                flows = [Paragraph("Kommentar folgt.", stile.platzhalter)]
            story.extend(kopf)   # steht immer oben auf einer frischen Seite
            story.extend(flows)  # fliesst erst die linke Spalte hinab, dann in die rechte
            statistik.append((nr, art, si, woerter(text)))

    if zf is not None and mit_zf:
        info = {"folie": None, "art": "zusammenfassung", "schritt": 0, "schritte": 0,
                "titel": zf["titel"] or "Das Wichtigste in Kürze", "folientitel": "", "rect": None,
                "gid": "zusammenfassung"}
        if erste is None:
            erste = "zusammenfassung"
        else:
            story.append(NextPageTemplate("zusammenfassung"))
            story.append(PageBreak())
        story.append(SeitenMarke(info))
        story.append(Kennung("Zusammenfassung der Vorlesung", stile.akzent_text))
        story.append(Paragraph(inline(typografie(info["titel"]), 13, "sans"), stile.titel))
        story.append(FrameBreak())
        # Die Kernbegriffe beginnen die rechte Spalte, Kurzfassung und Takeaways stehen links
        teile = re.split(r"(?m)^(?=###\s+(?:Kern)?[Bb]egriffe)", zf["text"], maxsplit=1)
        if not zf["text"].strip():
            story.append(Paragraph("Zusammenfassung folgt.", stile.platzhalter))
        for k, teil in enumerate(teile):
            if k and spalten == 2:
                story.append(FrameBreak())
            story.extend(markdown_flowables(teil, stile, spaltenbreite))
        statistik.append((0, "zusammenfassung", 0, woerter(zf["text"])))

    layout_pfad = tmp / "layout.pdf"
    ZUSTAND.seitenplan = []
    doc = KommentarDokument(layout_pfad, geometrien, erste, kopf_links, fuss, n, akzent, spalten=spalten,
                            title=f"Kommentierter Foliensatz – {titel or folien_pfad.stem}",
                            author="Kommentare: KI-generiert", creator="foliennotizen")
    doc.build(story)

    # Folien einbetten und Markierungen setzen
    out = pymupdf.open(layout_pfad)
    if len(out) != len(ZUSTAND.seitenplan):
        sys.exit(f"Interner Fehler: {len(out)} Seiten, aber {len(ZUSTAND.seitenplan)} Planeinträge")
    ocg = out.add_ocg("Markierungen", on=True)
    quelle_sha = fl.sha256(folien_pfad)
    marker_hex = fl.TUDA[marker_code]
    toc, fortsetzungen = [], []
    jetzt = dt.datetime.now().strftime("D:%Y%m%d%H%M%S")
    for idx, eintrag in enumerate(ZUSTAND.seitenplan):
        page = out[idx]
        if eintrag["art"] == "zusammenfassung":
            privat = f"<</Art/Zusammenfassung/Fortsetzung {'true' if eintrag['fortsetzung'] else 'false'}>>"
            out.xref_set_key(page.xref, "PieceInfo",
                             f"<</FolienKommentar<</LastModified({jetzt})/Private{privat}>>>>")
            if not eintrag["fortsetzung"]:
                toc.append([1, eintrag["titel"], idx + 1])
            continue
        x0, y0, bw, bh = eintrag["rect"]
        ziel = pymupdf.Rect(x0, y0, x0 + bw, y0 + bh)
        nr = eintrag["folie"]
        page.show_pdf_page(ziel, src, nr - 1, keep_proportion=True, overlay=True)
        quelle = src[nr - 1].rect
        s = bw / quelle.width
        formen = []
        if eintrag["art"] == "schritt":
            for stil, art, r, zh in markierungen.get((nr, eintrag["schritt"]), []):
                rr = pymupdf.Rect(x0 + (r.x0 - quelle.x0) * s, y0 + (r.y0 - quelle.y0) * s,
                                  x0 + (r.x1 - quelle.x0) * s, y0 + (r.y1 - quelle.y0) * s)
                formen.append((stil, art, rr, zh * s))
            markierungen_zeichnen(out, page, ocg, formen, marker_code)
        if eintrag["fortsetzung"]:
            fortsetzungen.append((nr, eintrag["art"], eintrag["schritt"], idx + 1))
        art_name = {"ueberblick": "Ueberblick", "schritt": "Schritt"}[eintrag["art"]]
        privat = (f"<</Folie {nr}/Art/{art_name}/Schritt {eintrag['schritt']}/Schritte {eintrag['schritte']}"
                  f"/Fortsetzung {'true' if eintrag['fortsetzung'] else 'false'}"
                  f"/Markierungen {len(formen)}"
                  f"/Rect[{ziel.x0:.4f} {ziel.y0:.4f} {ziel.x1:.4f} {ziel.y1:.4f}]>>")
        out.xref_set_key(page.xref, "PieceInfo", f"<</FolienKommentar<</LastModified({jetzt})/Private{privat}>>>>")
        if not eintrag["fortsetzung"]:
            if eintrag["art"] == "ueberblick":
                toc.append([1, f"Folie {nr}: {eintrag['folientitel']}", idx + 1])
            else:
                toc.append([2, f"Schritt {eintrag['schritt']}: {eintrag['titel']}", idx + 1])
    katalog = out.pdf_catalog()
    out.xref_set_key(katalog, "FolienKommentar",
                     f"<</QuelleSHA256({quelle_sha})/Folien {n}/Auswahl[{' '.join(map(str, sorted(auswahl)))}]"
                     f"/Entwurf {'true' if entwurf else 'false'}>>")
    out.set_toc(toc)
    out.set_metadata({"title": f"Kommentierter Foliensatz – {titel or folien_pfad.stem}",
                      "author": "Kommentare: KI-generiert (Claude)", "subject": veranstaltung,
                      "creator": "Skill foliennotizen", "producer": "ReportLab + PyMuPDF",
                      "keywords": "Foliensatz, Kommentar, TUDa"})
    ziel_pfad = Path(a.out)
    ziel_pfad.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(ziel_pfad), garbage=3, deflate=True)

    # Bericht
    seiten_je_folie, zf_seiten = {}, 0
    for e in ZUSTAND.seitenplan:
        if e["art"] == "zusammenfassung":
            zf_seiten += 1
            continue
        seiten_je_folie.setdefault(e["folie"], []).append(e["seite"])
    print(f"Gebaut: {ziel_pfad} – {len(out)} Seiten für {len(auswahl)} Folien"
          + (" (ENTWURF)" if entwurf else ""))
    print(f"  Akzent {akzent_code} {akzent['balken']}, Marker {marker_code} {marker_hex}")
    mehrseitig = [f"{nr} ({len(s)} S.)" for nr, s in sorted(seiten_je_folie.items()) if len(s) > 1]
    if mehrseitig:
        print("  Mehrseitig: Folie " + ", ".join(mehrseitig))
    if zf_seiten:
        print(f"  Zusammenfassung: {zf_seiten} Seite(n) am Ende" + (" – bitte auf eine Seite kürzen" if zf_seiten > 1 else ""))
    for e in ZUSTAND.seitenplan:
        belegt = e.get("rechts_belegt", 0)
        if e["art"] != "zusammenfassung" and 0 < belegt < 3.5 * ZEILENABSTAND:
            zeilen = max(1, round(belegt / ZEILENABSTAND))
            teil = "Überblick" if e["art"] == "ueberblick" else f"Schritt {e['schritt']}"
            print(f"  Hinweis: Folie {e['folie']}, {teil}: nur {zeilen} Zeile(n) in der rechten Spalte – "
                  f"leicht kürzen, dann bleibt der Kommentar in einer Spalte")
    for nr, art, si, seite in fortsetzungen:
        if art == "zusammenfassung":
            continue
        teil = "Überblick" if art == "ueberblick" else f"Schritt {si}"
        print(f"  ACHTUNG Überlauf: Folie {nr}, {teil} läuft auf Seite {seite} weiter – kürzen oder in Schritte teilen")
    for nr, art, si, w in statistik:
        if art != "zusammenfassung" and w > 480:
            print(f"  Hinweis: Folie {nr} {'Überblick' if art == 'ueberblick' else 'Schritt ' + str(si)}: {w} Wörter (lang)")
    mehrfach = fett_mehrfach(kommentare)
    if mehrfach:
        liste = "; ".join(f"„{b}“ (Folien {', '.join(map(str, v))})" for b, v in sorted(mehrfach.items(), key=lambda x: x[1]))
        print("  Hinweis: auf mehreren Folien fett – prüfen, dass jeder Begriff nur beim ersten Mal erklärt wird: " + liste)
    for h in hinweise:
        print("  Hinweis: " + h)
    if fehlend:
        print("  Platzhalter für Folie " + ", ".join(map(str, fehlend)))


if __name__ == "__main__":
    main()
