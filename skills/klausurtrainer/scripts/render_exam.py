#!/usr/bin/env python3
"""
render_exam.py - Erzeugt aus einer klausur.json zwei PDFs:
  <praefix>_Aufgabenblatt.pdf   Deckblatt, Aufgaben, optional Antwortfelder
  <praefix>_Loesungen.pdf       Musterloesung mit Bewertungsschema und Belegen

Aufruf:
    python3 render_exam.py klausur.json --out DIR   (ohne --out: /mnt/user-data/outputs, falls vorhanden, sonst .)
    python3 render_exam.py klausur.json --out DIR --vorlage vorlage_GPUM.json
    python3 render_exam.py klausur.json --out DIR --nur aufgaben|loesung

Gestaltung:
    Die generische Vorlage folgt dem Design System TUDa UI, uebersetzt fuer
    Papier: Archivo und JetBrains Mono (assets/fonts), Tinte fuer Text und
    Aufgabentitel, TU-Blau fuer TU-Balken, Zeichen und Musterloesungen,
    Linien-Icons im 24er-Raster, Hinweiskaesten als getoente Flaechen.
    Alle Farbwerte stehen gesammelt in TUDA (unten).

Vorlage:
    Ohne Angabe gilt die generische Vorlage. Liegt neben der klausur.json eine
    Datei vorlage_<MODULKUERZEL>.json (erzeugt von analyse_altklausur.py), wird
    sie automatisch verwendet. meta.vorlage in der JSON hat Vorrang, --vorlage
    auf der Kommandozeile hat hoechsten Vorrang. "generisch" erzwingt die
    Standardvorlage.

Der KI-Hinweis (Deckblatt + jede Fusszeile) wird in jeder Vorlage gesetzt und
laesst sich nicht abschalten. Logos von Universitaet oder Lehrstuhl werden nie
uebernommen; an ihrer Stelle steht das eigene Zeichen (Fuenffingerturm).
"""

import argparse
import copy
import json
import math
import os
import re
import sys
from collections import defaultdict
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Flowable, Frame, Image, KeepTogether,
    NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
    TableStyle,
)

# ==========================================================================
# Design-Tokens aus TUDa UI (helles Theme), fuer den Druck
# ==========================================================================
TUDA = {
    "ink": "#111113",             # text-primary: Text, Titel, Aufgabenkoepfe
    "text2": "#5B5B60",           # text-secondary: Beschriftungen, Kopf und Fuss
    "text3": "#6C6C70",           # text-tertiary: Zusaetze
    "linie": "#D1D1D6",           # border-subtle: Haarlinien, Antwortlinien
    "linie_stark": "#86868B",     # border-strong: Tabellenkoepfe, Ankreuzfelder
    "papier": "#F2F2F5",          # paper (surface-page): Tabellenkoepfe, Summenspalte
    "marke": "#005AA9",           # brand-primary = primary: Balken, Zeichen, Loesungen
    "markiert_linie": "#8DADD7",  # mark-line: Linie neben den Loesungsbloecken
    "info": "#00689D",            # info-fg
    "info_flaeche": "#E7F5FF",    # info-bg
    "info_rand": "#A5CDEB",       # info-border
    "fehler": "#B90F22",          # error-fg (TUDa 9c): KI-Hinweis
    "fehler_flaeche": "#FFECEB",  # error-bg
    "fehler_rand": "#F5B9B6",     # error-border
}

# Lage der Kopfzone (Abstand von der oberen Blattkante, mm)
BALKEN_OBEN_MM = 10.0     # TU-Balken
BALKEN_MM = 0.8           # Hoehe des TU-Balkens
KOPF_MITTE_MM = 16.4      # Mitte der Kopfzeile mit Zeichen
DECK_OBEN_MM = 16.0       # Deckblatt: Beginn des Satzspiegels unter dem Balken

# ==========================================================================
# Generische Vorlage
# ==========================================================================
STANDARD = {
    "name": "generisch",
    "gestaltung": "tuda",                        # tuda | schlicht (Altklausur)
    "rand_mm": [22, 22, 25, 22],                 # links, rechts, oben, unten
    "schrift_text": "archivo",
    "schrift_titel": "archivo",
    "schrift_hilfe": "archivo",                  # Kopf-/Fusszeile, Tabellen
    "groesse_text": 10.0,
    "groesse_aufgabe": 12.5,
    "groesse_titel": 25,
    "tinte": TUDA["ink"],
    "akzent": TUDA["marke"],
    "grau": TUDA["text2"],
    "haarlinie": TUDA["linie"],
    "flaeche": TUDA["papier"],
    "logo": "eigen",                              # eigen | keins
    "markenbalken": True,                         # TU-Balken oben auf jeder Seite
    "zeichen_name": "Probeklausur",               # Name neben dem Zeichen
    "zeichen_zeile": "zur Selbstkontrolle",       # Zeile darunter (meta.byline)
    "kopfzeile": {"links": "{modulkuerzel} · {modul}", "rechts": "{variante}"},
    "fusszeile": {"links": "{semester}", "rechts": "Seite {seite} von {seiten}"},
    "aufgabe_titel": "Aufgabe {nr}: {titel}",
    "aufgabe_titel_ohne": "Aufgabe {nr}",
    "aufgabe_punkte": "{punkte} Punkte",          # rechts neben dem Titel
    "aufgabe_linie": True,
    "punktekasten": True,
    "teilaufgabe_format": "({nr})",
    "teilpunkte_format": "{punkte} P.",
    "neue_seite_je_aufgabe": False,
    "antwortraum_stil": "linien",
    "symbole": True,                              # Symbole an Ueberschriften
    "kopflinie": "keine",                         # haar | kraeftig | keine
    "teilpunkte_position": "rechts",              # rechts | inline
    "logo_mm": 16,                                # Kantenlaenge des Zeichens
    "groesse_kopf": 7.6,
    "deckblatt": {
        "ausrichtung": "links",                   # links | zentriert
        "titelzeilen": [],                        # leer: Standardaufbau
        "personalien": [],                        # leer: stattdessen Materialuebersicht
        "grundlagen": True,                       # Arten des verwendeten Materials
        "punktetabelle": "horizontal",            # horizontal | vertikal | keine
        "hinweise_stil": "nummeriert",            # nummeriert | punkte
        "hinweise_titel": "Hinweise zur Bearbeitung",
        "hinweise_ausrichtung": "links",
        "eckdaten": True,
        "linie": True,
        "institution": True,
        "variante_zeile": True,
        "personalien_stil": "unterzeile",         # unterzeile | zeile
        "punktetabelle_titel": None,              # None = Standardtitel, "" = keiner
        "punktetabelle_zeilen": ["max.", "erreicht"],
    },
}

# Fruehere Namen der generischen Gestaltung
GESTALTUNG_ALIAS = {"minimal": "tuda", "betont": "tuda"}

KI_HINWEIS = (
    "Diese Probeklausur wurde mit Hilfe von KI aus dem bereitgestellten "
    "Lehrmaterial erstellt. Sie ist <b>keine offizielle Prüfungsleistung</b> und "
    "wurde weder vom Lehrstuhl gestellt noch geprüft oder freigegeben. "
    "Aufgabenauswahl, Schwierigkeitsgrad, Punkteverteilung und Lösungen sind "
    "unverbindlich und können Fehler enthalten. Maßgeblich sind allein die "
    "Angaben des Lehrstuhls.")
KI_FUSS = "KI-generierte Probeklausur – nicht vom Lehrstuhl gestellt"


def tief_mischen(basis, zusatz):
    out = copy.deepcopy(basis)
    for k, v in (zusatz or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = tief_mischen(out[k], v)
        else:
            out[k] = v
    return out


def hx(farbe):
    return colors.HexColor(farbe)


# ==========================================================================
# Schriften
# ==========================================================================
FONT_ORDNER = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "assets", "fonts"))
FAMILIEN = {
    "archivo": (FONT_ORDNER,
                ["Archivo-Regular.ttf", "Archivo-Bold.ttf",
                 "Archivo-Italic.ttf", "Archivo-BoldItalic.ttf"]),
    "caladea": ("/usr/share/fonts/truetype/crosextra",
                ["Caladea-Regular.ttf", "Caladea-Bold.ttf",
                 "Caladea-Italic.ttf", "Caladea-BoldItalic.ttf"]),
    "carlito": ("/usr/share/fonts/truetype/crosextra",
                ["Carlito-Regular.ttf", "Carlito-Bold.ttf",
                 "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf"]),
    "freeserif": ("/usr/share/fonts/truetype/freefont",
                  ["FreeSerif.ttf", "FreeSerifBold.ttf",
                   "FreeSerifItalic.ttf", "FreeSerifBoldItalic.ttf"]),
    "freesans": ("/usr/share/fonts/truetype/freefont",
                 ["FreeSans.ttf", "FreeSansBold.ttf",
                  "FreeSansOblique.ttf", "FreeSansBoldOblique.ttf"]),
    "dejavuserif": ("/usr/share/fonts/truetype/dejavu",
                    ["DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf",
                     "DejaVuSerif-Italic.ttf", "DejaVuSerif-BoldItalic.ttf"]),
    "dejavusans": ("/usr/share/fonts/truetype/dejavu",
                   ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf",
                    "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"]),
}
_REG = {}
_CMAPS = {}


def _cmap_merken(name, pfad):
    try:
        from fontTools.ttLib import TTFont as FT
        _CMAPS[name] = set(FT(pfad).getBestCmap())
    except Exception:
        pass


def familie(name):
    """Registriert eine Familie und gibt (normal, fett, kursiv) zurueck."""
    name = (name or "archivo").lower()
    if name not in FAMILIEN:
        name = "archivo"
    if name in _REG:
        return _REG[name]
    ordner, dateien = FAMILIEN[name]
    namen = [name + s for s in ("", "-B", "-I", "-BI")]
    try:
        for n, d in zip(namen, dateien):
            pdfmetrics.registerFont(TTFont(n, os.path.join(ordner, d)))
    except Exception:
        _REG[name] = familie("dejavusans") if name != "dejavusans" else (
            "Helvetica", "Helvetica-Bold", "Helvetica-Oblique")
        return _REG[name]
    pdfmetrics.registerFontFamily(name, normal=namen[0], bold=namen[1],
                                  italic=namen[2], boldItalic=namen[3])
    for n, d in zip(namen, dateien):
        _cmap_merken(n, os.path.join(ordner, d))
    _REG[name] = (namen[0], namen[1], namen[2])
    return _REG[name]


def einzelschnitt(name, datei, ersatz):
    """Registriert einen einzelnen Schnitt aus assets/fonts; sonst Ersatz."""
    if name in _REG:
        return _REG[name]
    try:
        pfad = os.path.join(FONT_ORDNER, datei)
        pdfmetrics.registerFont(TTFont(name, pfad))
        _cmap_merken(name, pfad)
        _REG[name] = name
    except Exception:
        _REG[name] = ersatz
    return _REG[name]


def tuda_schnitte():
    """Schnitte der TUDa-Gestaltung: Archivo 400/600/700/800, kursiv, Mono 500."""
    r, b, i = familie("archivo")
    return {"r": r, "b": b, "i": i,
            "sb": einzelschnitt("Archivo-SemiBold", "Archivo-SemiBold.ttf", b),
            "xb": einzelschnitt("Archivo-ExtraBold", "Archivo-ExtraBold.ttf", b),
            "mono": einzelschnitt("JetBrainsMono-Medium", "JetBrainsMono-Medium.ttf", r)}


try:
    pdfmetrics.registerFont(TTFont("Sym", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    _SYM = True
except Exception:
    _SYM = False

ERLAUBTE_TAGS = ["b", "i", "u", "sub", "super", "br/", "br"]
LOESUNG_BLAU = TUDA["marke"]  # Loesungen und punktegebende Teilsaetze (primary)
LUECKE_ZEICHEN = 26           # Laenge jeder Luecke im Aufgabenblatt


def textblock(text, schrift, stil, S):
    """Loesungs-/Erlaeuterungstext in Flowables. Zeilen, die mit "- " beginnen,
    werden zu Stichpunkten; zusammenhaengender Text bleibt ein Absatz.
    Auch eine Liste von Strings ist erlaubt (jedes Element ein Stichpunkt)."""
    if isinstance(text, (list, tuple)):
        text = "\n".join("- " + str(x).strip() for x in text if str(x).strip())
    out, absatz = [], []

    def flush():
        if absatz:
            out.append(Paragraph(rt(" ".join(absatz), schrift), stil))
            absatz.clear()
    for zeile in str(text).splitlines():
        z = zeile.strip()
        if not z:
            flush()
            continue
        m = re.match(r"^[-•*]\s+(.*)$", z)
        if m:
            flush()
            bs = ParagraphStyle("stichpunkt_" + stil.name, parent=stil,
                                leftIndent=stil.leftIndent + 4.5 * mm,
                                bulletIndent=stil.leftIndent + 0.8 * mm,
                                bulletFontName=stil.fontName,
                                spaceBefore=0.6, spaceAfter=1.2)
            out.append(Paragraph(rt(m.group(1), schrift), bs, bulletText="•"))
        else:
            absatz.append(z)
    flush()
    return out


def rt(text, schrift=None, luecken="leer"):
    """Escaped Text, kleine Tag-Whitelist, Rueckfallschrift fuer fehlende Zeichen.
    luecken: wie [[Loesung]] dargestellt wird.
    "leer" = unterstrichene Luecke (Aufgabenblatt), "zelle" = leere Tabellenzelle,
    "loesung" = Loesung in Blau und fett. Standard ist leer, damit nie
    versehentlich eine Loesung im Aufgabenblatt landet."""
    if text is None:
        return ""
    s = xml_escape(str(text))
    for tag in ERLAUBTE_TAGS:
        s = s.replace("&lt;%s&gt;" % tag, "<%s>" % tag)
        s = s.replace("&lt;/%s&gt;" % tag.rstrip("/"), "</%s>" % tag.rstrip("/"))
    s = s.replace("&lt;br/&gt;", "<br/>")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

    def _marker(m):
        teil = '<font color="%s"><b>%s</b></font>' % (LOESUNG_BLAU, m.group(1))
        if m.group(2):
            teil += ('<super><font size="6.5" color="%s">&#160;%s&#160;P.</font></super>'
                     % (LOESUNG_BLAU, m.group(2).replace(".", ",")))
        return teil
    s = re.sub(r"==(.+?)==(?:\[(\d+(?:[.,]\d+)?)\])?", _marker, s)

    def _luecke(m):
        inhalt = m.group(1)
        if luecken == "loesung":
            return '<font color="%s"><b>%s</b></font>' % (LOESUNG_BLAU, inhalt)
        if luecken == "zelle":
            return ""
        # einheitliche Laenge: die Luecke darf nichts ueber die Antwort verraten
        return "<u>" + "&#160;" * LUECKE_ZEICHEN + "</u>"
    s = re.sub(r"\[\[(.+?)\]\]", _luecke, s)
    cmap = _CMAPS.get(schrift) if schrift else None
    if cmap and _SYM:
        out, tag = [], False
        for ch in s:
            if ch == "<":
                tag = True
            elif ch == ">":
                tag = False
            if not tag and ch not in "<>" and ord(ch) > 127 and ord(ch) not in cmap:
                out.append('<font name="Sym">%s</font>' % ch)
            else:
                out.append(ch)
        s = "".join(out)
    return s


def _laeufe(text, schrift):
    """Zerlegt Text in Laeufe (teil, schrift); Zeichen, die der Schrift fehlen,
    kommen aus der Ersatzschrift (z. B. griechische Buchstaben bei Archivo)."""
    cmap = _CMAPS.get(schrift)
    if not cmap or not _SYM:
        return [(text, schrift)]
    out = []
    for ch in text:
        f = schrift if (ord(ch) < 128 or ord(ch) in cmap) else "Sym"
        if out and out[-1][1] == f:
            out[-1] = (out[-1][0] + ch, f)
        else:
            out.append((ch, f))
    return out


def text_breite(text, schrift, gr):
    return sum(pdfmetrics.stringWidth(t, f, gr) for t, f in _laeufe(text, schrift))


def zeichne_text(c, x, y, text, schrift, gr, ausrichtung="links"):
    """drawString mit Ersatzschrift fuer fehlende Zeichen (Kopf- und Fusszeilen)."""
    if ausrichtung == "rechts":
        x -= text_breite(text, schrift, gr)
    elif ausrichtung == "mitte":
        x -= text_breite(text, schrift, gr) / 2.0
    for t, f in _laeufe(text, schrift):
        c.setFont(f, gr)
        c.drawString(x, y, t)
        x += pdfmetrics.stringWidth(t, f, gr)


def de(x):
    """Punktzahl mit deutschem Dezimalkomma: 1.5 -> 1,5"""
    return ("%g" % float(x)).replace(".", ",")


def fmt(vorlage, **werte):
    d = defaultdict(str, {k: ("" if v is None else v) for k, v in werte.items()})
    t = vorlage.format_map(d)
    t = re.sub(r"\(\s*\)|\[\s*\]", "", t)          # leere Klammern
    t = re.sub(r"\s+([–\-·|:])\s*$", "", t.strip())    # verwaiste Trenner am Ende
    t = re.sub(r"^\s*[–\-·|:]\s+", "", t)              # ... und am Anfang
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


# ==========================================================================
# Vektorpfade (SVG-Syntax) fuer Icons und Zeichen
# ==========================================================================
_PFAD_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _bogen(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """SVG-Bogen als Folge kubischer Kurven [(c1x, c1y, c2x, c2y, x, y), ...]."""
    if (x1, y1) == (x2, y2):
        return []
    if rx == 0 or ry == 0:
        return [(x1, y1, x2, y2, x2, y2)]
    rx, ry = abs(rx), abs(ry)
    p = math.radians(phi)
    cp, sp = math.cos(p), math.sin(p)
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    zaehler = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    nenner = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    k = math.sqrt(max(0.0, zaehler / nenner)) if nenner else 0.0
    if fa == fs:
        k = -k
    cxp, cyp = k * rx * y1p / ry, -k * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2.0
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2.0

    def winkel(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    vx, vy = (-x1p - cxp) / rx, (-y1p - cyp) / ry
    t1 = winkel(1, 0, ux, uy)
    dt = winkel(ux, uy, vx, vy)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    n = max(1, int(math.ceil(abs(dt) / (math.pi / 2) - 1e-9)))
    seg = dt / n
    kk = 4.0 / 3.0 * math.tan(seg / 4.0)

    def auf_ellipse(px, py):
        return (cx + rx * cp * px - ry * sp * py, cy + rx * sp * px + ry * cp * py)
    out, t = [], t1
    for _ in range(n):
        c1, s1 = math.cos(t), math.sin(t)
        c2, s2 = math.cos(t + seg), math.sin(t + seg)
        out.append(auf_ellipse(c1 - kk * s1, s1 + kk * c1) +
                   auf_ellipse(c2 + kk * s2, s2 - kk * c2) + auf_ellipse(c2, s2))
        t += seg
    return out


def _pfad_segmente(d):
    """Zerlegt einen SVG-Pfad in absolute Segmente ("M"|"L", x, y),
    ("C", x1, y1, x2, y2, x, y) und ("Z",)."""
    tok = _PFAD_RE.findall(d)
    i, n = 0, len(tok)
    out = []
    x = y = sx = sy = 0.0
    cmd, lc, lq = None, None, None

    def zahl():
        nonlocal i
        v = float(tok[i])
        i += 1
        return v

    def quad(x0, y0, qx, qy, ex, ey):
        return ("C", x0 + 2 / 3.0 * (qx - x0), y0 + 2 / 3.0 * (qy - y0),
                ex + 2 / 3.0 * (qx - ex), ey + 2 / 3.0 * (qy - ey), ex, ey)
    while i < n:
        if tok[i].isalpha():
            cmd = tok[i]
            i += 1
            if cmd in "Zz":
                out.append(("Z",))
                x, y = sx, sy
                lc = lq = None
                continue
        if cmd is None:
            break
        rel, C = cmd.islower(), cmd.upper()
        if C == "M":
            nx, ny = zahl(), zahl()
            if rel:
                nx, ny = nx + x, ny + y
            out.append(("M", nx, ny))
            x, y = sx, sy = nx, ny
            cmd = "l" if rel else "L"
            lc = lq = None
        elif C == "L":
            nx, ny = zahl(), zahl()
            if rel:
                nx, ny = nx + x, ny + y
            out.append(("L", nx, ny))
            x, y, lc, lq = nx, ny, None, None
        elif C == "H":
            nx = zahl() + (x if rel else 0)
            out.append(("L", nx, y))
            x, lc, lq = nx, None, None
        elif C == "V":
            ny = zahl() + (y if rel else 0)
            out.append(("L", x, ny))
            y, lc, lq = ny, None, None
        elif C == "C":
            a = [zahl() for _ in range(6)]
            if rel:
                a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y, a[4] + x, a[5] + y]
            out.append(("C",) + tuple(a))
            lc, lq, x, y = (a[2], a[3]), None, a[4], a[5]
        elif C == "S":
            a = [zahl() for _ in range(4)]
            if rel:
                a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y]
            c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
            out.append(("C", c1[0], c1[1], a[0], a[1], a[2], a[3]))
            lc, lq, x, y = (a[0], a[1]), None, a[2], a[3]
        elif C == "Q":
            a = [zahl() for _ in range(4)]
            if rel:
                a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y]
            out.append(quad(x, y, a[0], a[1], a[2], a[3]))
            lq, lc, x, y = (a[0], a[1]), None, a[2], a[3]
        elif C == "T":
            ex, ey = zahl(), zahl()
            if rel:
                ex, ey = ex + x, ey + y
            q = (2 * x - lq[0], 2 * y - lq[1]) if lq else (x, y)
            out.append(quad(x, y, q[0], q[1], ex, ey))
            lq, lc, x, y = q, None, ex, ey
        elif C == "A":
            rx, ry, phi, fa, fs, nx, ny = [zahl() for _ in range(7)]
            if rel:
                nx, ny = nx + x, ny + y
            for s in _bogen(x, y, rx, ry, phi, int(fa), int(fs), nx, ny):
                out.append(("C",) + s)
            x, y, lc, lq = nx, ny, None, None
        else:
            break
    return out


def _pfad_bauen(c, d, abb, p=None):
    """Haengt einen SVG-Pfad an ein ReportLab-Pfadobjekt an. abb bildet
    Rasterkoordinaten (y nach unten) auf die Zeichenflaeche ab."""
    p = p or c.beginPath()
    for s in _pfad_segmente(d):
        if s[0] == "M":
            p.moveTo(*abb(s[1], s[2]))
        elif s[0] == "L":
            p.lineTo(*abb(s[1], s[2]))
        elif s[0] == "C":
            p.curveTo(*(abb(s[1], s[2]) + abb(s[3], s[4]) + abb(s[5], s[6])))
        else:
            p.close()
    return p


# ==========================================================================
# Icons (TUDa UI: 24er-Raster, Strich 1,75, runde Enden, keine Fuellung)
# ==========================================================================
ICONS = {
    "clock": [("circle", 12, 12, 8.5), ("path", "M12 7.5V12l3 2")],
    "check-circle": [("circle", 12, 12, 8.5), ("path", "M8.5 12.3l2.5 2.5 4.5-5")],
    "file": [("path", "M14 3.5H7.5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8z"),
             ("path", "M14 3.5V8h4.5M9 13h6M9 16.5h4")],
    "edit": [("path", "M4.5 19.5l1-4.2L15.8 5a1.9 1.9 0 0 1 2.7 0l.5.5a1.9 1.9 0 0 1 0 "
                      "2.7L8.7 18.5z"),
             ("path", "M13.5 7.5l3 3")],
    "book": [("path", "M12 6.5C10.5 5 8 4.5 4 4.5v14c4 0 6.5.5 8 2 1.5-1.5 4-2 8-2v-14c-4 "
                      "0-6.5.5-8 2z"),
             ("path", "M12 6.5v14")],
    "info": [("circle", 12, 12, 8.5), ("path", "M12 11v5.5M12 7.6v.15")],
    "alert-triangle": [("path", "M10.3 4.6L3 17.5a2 2 0 0 0 1.7 3h14.6a2 2 0 0 0 1.7-3L13.7 "
                                "4.6a2 2 0 0 0-3.4 0z"),
                       ("path", "M12 9.5v4M12 16.9v.1")],
    "list": [("path", "M9 6.5h11M9 12h11M9 17.5h11M4 6.5h1M4 12h1M4 17.5h1")],
    "clipboard-check": [("rect", 5, 4.5, 14, 16, 2), ("path", "M9 4.5v-1h6v1M9 13l2 2 4-4")],
}
# Motive, die TUDa UI nicht enthaelt: aus Lucide 1.49.0 (ISC-Lizenz,
# Copyright (c) Lucide Contributors), wie im Design System vorgesehen mit
# Strich 1,75 und auf den 20er-Live-Bereich gesetzt.
LUCIDE = {
    "key": [("path", "m2 21 9.6-9.6"),
            ("path", "m7.5 15.5 2.3 2.3a1 1 0 0 1 0 1.4l-2.1 2.1a1 1 0 0 1-1.4 0L4 19"),
            ("circle", 15.5, 7.5, 5.5)],
    "lightbulb": [("path", "M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 "
                           "1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"),
                  ("path", "M9 18h6"), ("path", "M10 22h4")],
    "list-checks": [("path", "M13 5h8"), ("path", "M13 12h8"), ("path", "M13 19h8"),
                    ("path", "m3 17 2 2 4-4"), ("path", "m3 7 2 2 4-4")],
}
# Symbolnamen der Probeklausur -> Icon
SYMBOLE = {
    "uhr": "clock", "punkte": "check-circle", "blaetter": "file", "stift": "edit",
    "buch": "book", "schluessel": "key", "liste": "list-checks", "lampe": "lightbulb",
    "hinweis": "alert-triangle", "info": "info",
}


def zeichne_symbol(c, name, x, y, g, farbe, strich=None):
    """Zeichnet ein Icon der Kantenlaenge g mit linker unterer Ecke (x, y)."""
    icon = SYMBOLE.get(name, name)
    if icon in LUCIDE:
        teile, sk = LUCIDE[icon], 20.0 / 22.0
    else:
        teile, sk = ICONS.get(icon, ICONS["info"]), 1.0
    f = g / 24.0

    def abb(px, py):
        return (x + (12 + (px - 12) * sk) * f, y + g - (12 + (py - 12) * sk) * f)
    c.saveState()
    c.setStrokeColor(farbe)
    c.setFillColor(farbe)
    c.setLineWidth(strich or 1.75 * f)
    c.setLineCap(1)
    c.setLineJoin(1)
    p = c.beginPath()
    for teil in teile:
        if teil[0] == "path":
            _pfad_bauen(c, teil[1], abb, p)
        elif teil[0] == "circle":
            px, py = abb(teil[1], teil[2])
            p.circle(px, py, teil[3] * f * sk)
        elif teil[0] == "rect":
            px, py = abb(teil[1], teil[2] + teil[4])
            p.roundRect(px, py, teil[3] * f * sk, teil[4] * f * sk, teil[5] * f * sk)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


class Symbol(Flowable):
    def __init__(self, name, groesse=3.4 * mm, farbe=colors.black, versatz=0.6):
        super().__init__()
        self.name, self.g, self.farbe, self.versatz = name, groesse, farbe, versatz

    def wrap(self, aw, ah):
        self.width, self.height = self.g, self.g + self.versatz
        return self.width, self.height

    def draw(self):
        zeichne_symbol(self.canv, self.name, 0, self.versatz, self.g, self.farbe)


# ==========================================================================
# Zeichen Fuenffingerturm (TUDa UI, Asset-Gruppe Logos)
# ==========================================================================
# Fuenf Rundboegen mit je einem Streifen im 48er-Raster
ZEICHEN_BOEGEN = (
    "M7 38V26A3 3 0 0 1 13 26V38H12V26A2 2 0 0 0 8 26V38ZM9 38V26A1 1 0 0 1 11 26V38Z"
    "M14 38V19A3 3 0 0 1 20 19V38H19V19A2 2 0 0 0 15 19V38ZM16 38V19A1 1 0 0 1 18 19V38Z"
    "M21 38V12A3 3 0 0 1 27 12V38H26V12A2 2 0 0 0 22 12V38ZM23 38V12A1 1 0 0 1 25 12V38Z"
    "M28 38V19A3 3 0 0 1 34 19V38H33V19A2 2 0 0 0 29 19V38ZM30 38V19A1 1 0 0 1 32 19V38Z"
    "M35 38V26A3 3 0 0 1 41 26V38H40V26A2 2 0 0 0 36 26V38ZM37 38V26A1 1 0 0 1 39 26V38Z")
# Kleinformat bis etwa 6 mm: nur die fuenf Streifen. In TUDa UI beginnen sie bei
# x = 12 und enden bei 39, liegen also 1,5u rechts der Mitte (im 16er-Raster 0,5u).
# Hier mittig: 27u breit, 10,5u Rand auf beiden Seiten.
ZEICHEN_STREIFEN = ("M10.5 24H13.5V42H10.5ZM16.5 15H19.5V42H16.5ZM22.5 6H25.5V42H22.5Z"
                    "M28.5 15H31.5V42H28.5ZM34.5 24H37.5V42H34.5Z")


def zeichne_zeichen(c, x, y, g, art="kachel", farbe=None):
    """Zeichen mit linker unterer Ecke (x, y).
    art "kachel": Boegen weiss auf TU-Blau, Kante g.
    art "klein":  Kleinformat (Streifen) auf TU-Blau, Kante g.
    art "tinte":  freistehende Boegen einfarbig, Breite g (Hoehe g * 29/34)."""
    c.saveState()
    if art == "tinte":
        f = g / 34.0
        h = 29 * f
        c.setFillColor(farbe or hx(TUDA["ink"]))
        p = _pfad_bauen(c, ZEICHEN_BOEGEN, lambda px, py: (x + (px - 7) * f, y + h - (py - 9) * f))
        c.drawPath(p, stroke=0, fill=1)
    else:
        f = g / 48.0
        c.setFillColor(farbe or hx(TUDA["marke"]))
        c.roundRect(x, y, g, g, 10 * f, stroke=0, fill=1)
        c.setFillColor(colors.white)
        p = _pfad_bauen(c, ZEICHEN_STREIFEN if art == "klein" else ZEICHEN_BOEGEN,
                        lambda px, py: (x + px * f, y + g - py * f))
        c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


class Zeichen(Flowable):
    def __init__(self, groesse, art="kachel"):
        super().__init__()
        self.g, self.art = groesse, art

    def wrap(self, aw, ah):
        self.width = self.g
        self.height = self.g * 29.0 / 34.0 if self.art == "tinte" else self.g
        return self.width, self.height

    def draw(self):
        zeichne_zeichen(self.canv, 0, 0, self.g, self.art)


# ==========================================================================
# Gestaltungselemente
# ==========================================================================
class Infokasten(Flowable):
    """Hinweiskasten wie die Alerts in TUDa UI: getoente Flaeche, feiner Rahmen,
    abgerundete Ecken, Icon in der Statusfarbe, Titel und Inhalt rechts daneben."""
    PL, PR, PT, PB = 4.0 * mm, 4.6 * mm, 3.3 * mm, 3.5 * mm
    G, ABSTAND, LUECKE = 4.2 * mm, 2.6 * mm, 1.6 * mm

    def __init__(self, symbol, titel, inhalt, breite, farbe, flaeche, rand,
                 titel_schrift, titel_farbe=None, radius=2.4 * mm):
        super().__init__()
        self.symbol, self.titel, self.inhalt = symbol, titel, inhalt
        self.w, self.farbe, self.flaeche, self.rand = breite, farbe, flaeche, rand
        self.titel_schrift, self.r = titel_schrift, radius
        self.titel_farbe = titel_farbe or farbe

    @classmethod
    def innenbreite(cls, breite):
        return breite - cls.PL - cls.G - cls.ABSTAND - cls.PR

    def wrap(self, aw, ah):
        h = self.PT + self.G + self.LUECKE + self.PB
        for f in self.inhalt:
            h += f.wrap(self.innenbreite(self.w), ah)[1]
        self.width, self.height = self.w, h
        return self.w, h

    def draw(self):
        c = self.canv
        w, h, r = self.width, self.height, self.r
        c.saveState()
        c.setFillColor(self.flaeche)
        if self.rand:
            c.setStrokeColor(self.rand)
            c.setLineWidth(0.6)
        c.roundRect(0, 0, w, h, r, stroke=1 if self.rand else 0, fill=1)
        c.restoreState()
        ytop = h - self.PT
        zeichne_symbol(c, self.symbol, self.PL, ytop - self.G, self.G, self.farbe)
        xt = self.PL + self.G + self.ABSTAND
        c.saveState()
        c.setFillColor(self.titel_farbe)
        c.setFont(self.titel_schrift, 9.2)
        c.drawString(xt, ytop - self.G / 2.0 - 9.2 * 0.34, self.titel)
        c.restoreState()
        y = ytop - self.G - self.LUECKE
        for f in self.inhalt:
            fw, fh = f.wrap(self.innenbreite(self.w), h)
            f.drawOn(c, xt, y - fh)
            y -= fh


class Grosstitel(Flowable):
    """Grosser Titel wie display in TUDa UI: Archivo ExtraBold, enge Laufweite.
    Lange Titel brechen um; passt ein Wort nicht oder werden es mehr als drei
    Zeilen, wird der Grad schrittweise verkleinert."""

    def __init__(self, text, schrift, groesse, farbe, laufweite=-0.025,
                 zeilen_max=3, min_groesse=16):
        super().__init__()
        self.text = " ".join(str(text or "").split())
        self.schrift, self.groesse, self.farbe = schrift, groesse, farbe
        self.laufweite, self.zeilen_max, self.min_groesse = laufweite, zeilen_max, min_groesse

    def _breite(self, s, g):
        return pdfmetrics.stringWidth(s, self.schrift, g) + g * self.laufweite * max(0, len(s) - 1)

    def _umbruch(self, breite, g):
        zeilen, akt = [], ""
        for wort in self.text.split(" "):
            probe = (akt + " " + wort).strip()
            if akt and self._breite(probe, g) > breite:
                zeilen.append(akt)
                akt = wort
            else:
                akt = probe
        if akt:
            zeilen.append(akt)
        laengstes = max([self._breite(w, g) for w in self.text.split(" ")] or [0])
        return zeilen, laengstes

    def wrap(self, aw, ah):
        g = self.groesse
        while True:
            zeilen, laengstes = self._umbruch(aw, g)
            if (len(zeilen) <= self.zeilen_max and laengstes <= aw) or g <= self.min_groesse:
                break
            g -= 1
        self.g, self.zeilen, self.zab = g, zeilen, g * 1.1
        self.width = aw
        self.height = (len(zeilen) - 1) * self.zab + g * 1.08
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.farbe)
        for i, z in enumerate(self.zeilen):
            t = c.beginText(0, self.height - self.g * 0.86 - i * self.zab)
            t.setFont(self.schrift, self.g)
            t.setCharSpace(self.g * self.laufweite)
            t.textOut(z)
            c.drawText(t)
        c.restoreState()


# ==========================================================================
# Antwortraum
# ==========================================================================
class AntwortLinien(Flowable):
    def __init__(self, zeilen, farbe, abstand=8.5 * mm):
        super().__init__()
        self.zeilen, self.farbe, self.abstand = max(1, int(zeilen)), farbe, abstand

    def wrap(self, aw, ah):
        self.width, self.height = aw, self.zeilen * self.abstand
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.farbe)
        c.setLineWidth(0.4)
        for i in range(self.zeilen):
            y = self.height - (i + 1) * self.abstand + 1.5
            c.line(0, y, self.width, y)


class AntwortKasten(Flowable):
    def __init__(self, hoehe_mm, farbe, raster=False):
        super().__init__()
        self.h, self.farbe, self.raster = hoehe_mm * mm, farbe, raster

    def wrap(self, aw, ah):
        self.width, self.height = aw, self.h
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.farbe)
        c.setLineWidth(0.6)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=0)
        if self.raster:
            c.setLineWidth(0.2)
            s = 5 * mm
            x = s
            while x < self.width:
                c.line(x, 0, x, self.height)
                x += s
            y = s
            while y < self.height:
                c.line(0, y, self.width, y)
                y += s


class Linie(Flowable):
    def __init__(self, dicke, farbe, vor=0, nach=0, doppelt=False, farbe2=None):
        super().__init__()
        self.dicke, self.farbe, self.vor, self.nach = dicke, farbe, vor, nach
        self.doppelt, self.farbe2 = doppelt, farbe2 or farbe

    def wrap(self, aw, ah):
        self.width = aw
        self.height = self.vor + self.nach + self.dicke + (3 if self.doppelt else 0)
        return self.width, self.height

    def draw(self):
        c = self.canv
        y = self.nach + (3 if self.doppelt else 0)
        c.setStrokeColor(self.farbe)
        c.setLineWidth(self.dicke)
        c.line(0, y, self.width, y)
        if self.doppelt:
            c.setStrokeColor(self.farbe2)
            c.setLineWidth(0.45)
            c.line(0, y - 2.6, self.width, y - 2.6)


# ==========================================================================
# Dokument
# ==========================================================================
class ZaehlCanvas(rl_canvas.Canvas):
    ctx = {}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._seiten = []

    def showPage(self):
        self._seiten.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        gesamt = len(self._seiten)
        for zustand in self._seiten:
            self.__dict__.update(zustand)
            self._fuss(gesamt)
            super().showPage()
        super().save()

    def _fuss(self, gesamt):
        ctx = self.ctx
        stil, werte = ctx["stil"], ctx["werte"]
        l, r, o, u = [x * mm for x in stil["rand_mm"]]
        breite = A4[0]
        tuda = stil.get("gestaltung") == "tuda"
        hilfe = familie(stil["schrift_hilfe"])
        self.saveState()
        y = u - 10 * mm
        self.setStrokeColor(hx(stil["haarlinie"]))
        self.setLineWidth(0.4)
        self.line(l, y + 4.6 * mm, breite - r, y + 4.6 * mm)
        self.setFillColor(hx(stil["grau"]))
        gr = 7.4 if tuda else 7.6
        w = dict(werte, seite=self._pageNumber, seiten=gesamt)
        zeichne_text(self, l, y, fmt(stil["fusszeile"].get("links", ""), **w), hilfe[0], gr)
        zeichne_text(self, breite - r, y, fmt(stil["fusszeile"].get("rechts", ""), **w),
                     hilfe[0], gr, "rechts")
        # KI-Hinweis mittig, immer
        txt = ctx.get("ki_fuss") or KI_FUSS
        tb = text_breite(txt, hilfe[0], 7.0)
        g = 2.7 * mm
        x0 = breite / 2.0 - (tb + g + 1.2 * mm) / 2.0
        zeichne_symbol(self, "hinweis", x0, y - 0.7, g, hx(TUDA["fehler"]))
        zeichne_text(self, x0 + g + 1.2 * mm, y, txt, hilfe[0], 7.0)
        self.restoreState()


class KlausurDoc(BaseDocTemplate):
    def __init__(self, pfad, stil, werte, modus):
        l, r, o, u = [x * mm for x in stil["rand_mm"]]
        super().__init__(pfad, pagesize=A4, leftMargin=l, rightMargin=r,
                         topMargin=o, bottomMargin=u,
                         title="%s – %s%s" % (werte.get("modul", ""),
                                              werte.get("variante", ""),
                                              " (Lösung)" if modus == "loesung" else ""),
                         author="KI-generiert",
                         subject="KI-generierte Probeklausur, nicht vom Lehrstuhl gestellt",
                         initialFontName=familie(stil["schrift_hilfe"])[0], lang="de-DE")
        self.stil, self.werte, self.modus = stil, werte, modus
        self.tuda = stil.get("gestaltung") == "tuda"
        f = Frame(l, u, self.width, self.height, id="n", leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)
        if self.tuda:
            fd = Frame(l, u, self.width, A4[1] - DECK_OBEN_MM * mm - u, id="d",
                       leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
            deck = PageTemplate(id="deck", frames=[fd], onPage=self._balken)
        else:
            deck = PageTemplate(id="deck", frames=[f])
        self.addPageTemplates([deck, PageTemplate(id="inhalt", frames=[f],
                                                  onPage=self._kopf)])

    def _balken(self, c, doc):
        """TU-Balken: schmale Flaeche in TU-Blau ueber dem Satzspiegel."""
        stil = self.stil
        if not (self.tuda and stil.get("markenbalken", True)):
            return
        l, r, o, u = [x * mm for x in stil["rand_mm"]]
        c.saveState()
        c.setFillColor(hx(TUDA["marke"]))
        c.rect(l, A4[1] - (BALKEN_OBEN_MM + BALKEN_MM) * mm, A4[0] - l - r, BALKEN_MM * mm,
               stroke=0, fill=1)
        c.restoreState()

    def _kopf(self, c, doc):
        stil = self.stil
        l, r, o, u = [x * mm for x in stil["rand_mm"]]
        hilfe = familie(stil["schrift_hilfe"])
        gk = stil.get("groesse_kopf", 7.8)
        links = fmt(stil["kopfzeile"].get("links", ""), **self.werte)
        rechts = fmt(stil["kopfzeile"].get("rechts", ""), **self.werte)
        if self.modus == "loesung":
            rechts = (rechts + "  ·  Musterlösung").strip(" ·")
        c.saveState()
        if self.tuda:
            self._balken(c, doc)
            T = tuda_schnitte()
            ym = A4[1] - KOPF_MITTE_MM * mm
            g = 5.6 * mm
            x_links = l
            if stil.get("logo") == "eigen":
                zeichne_zeichen(c, l, ym - g / 2.0, g, "klein")
                x_links = l + g + 2.6 * mm
            y = ym - gk * 0.34
            c.setFillColor(hx(TUDA["text2"]))
            zeichne_text(c, x_links, y, links, T["r"], gk)
            schrift_r = T["r"]
            if self.modus == "loesung":
                schrift_r = T["sb"]
                c.setFillColor(hx(TUDA["marke"]))
            zeichne_text(c, A4[0] - r, y, rechts, schrift_r, gk, "rechts")
            art = stil.get("kopflinie", "keine")
            if art != "keine":
                c.setStrokeColor(hx(stil["tinte"] if art == "kraeftig" else stil["haarlinie"]))
                c.setLineWidth(0.8 if art == "kraeftig" else 0.4)
                c.line(l, ym - g / 2.0 - 1.8 * mm, A4[0] - r, ym - g / 2.0 - 1.8 * mm)
            c.restoreState()
            return
        y = A4[1] - o + 8 * mm
        c.setFillColor(hx(stil["grau"] if stil["name"] == "generisch" else stil["tinte"]))
        zeichne_text(c, l, y, links, hilfe[0], gk)
        schrift_r = hilfe[0]
        if self.modus == "loesung":
            schrift_r = hilfe[1]
            c.setFillColor(hx(stil["akzent"]))
        zeichne_text(c, A4[0] - r, y, rechts, schrift_r, gk, "rechts")
        art = stil.get("kopflinie", "haar")
        if art != "keine":
            c.setStrokeColor(hx(stil["tinte"] if art == "kraeftig" else stil["haarlinie"]))
            c.setLineWidth(0.8 if art == "kraeftig" else 0.4)
            c.line(l, y - 2.6 * mm, A4[0] - r, y - 2.6 * mm)
        c.restoreState()


# ==========================================================================
# Stile
# ==========================================================================
def baue_stile(stil):
    t = familie(stil["schrift_text"])
    h = familie(stil["schrift_titel"])
    x = familie(stil["schrift_hilfe"])
    T = tuda_schnitte()
    tuda = stil.get("gestaltung") == "tuda"
    sb = T["sb"] if tuda else x[1]          # Beschriftungen, Tabellenkoepfe
    mono = T["mono"] if tuda else x[0]      # Kennungen: Quellanker, Modulkuerzel
    tinte = hx(stil["tinte"])
    akz = hx(stil["akzent"])
    grau = hx(stil["grau"])
    ink, text2 = hx(TUDA["ink"]), hx(TUDA["text2"])
    fs = stil["groesse_text"]
    ld = fs * (1.45 if tuda else 1.42)

    def st(name, **kw):
        b = dict(fontName=t[0], fontSize=fs, leading=ld, textColor=tinte)
        b.update(kw)
        return ParagraphStyle(name, **b)

    zentriert = stil["deckblatt"]["ausrichtung"] == "zentriert"
    mitte = TA_CENTER if zentriert else TA_LEFT
    return {
        "_t": t, "_h": h, "_x": x, "_sb": sb, "_mono": mono, "_T": T, "_tuda": tuda,
        "body": st("body", spaceAfter=2),
        "einleitung": st("einleitung", spaceAfter=2),
        "titel": st("titel", fontName=h[1], fontSize=stil["groesse_titel"],
                    leading=stil["groesse_titel"] * 1.18, textColor=akz, alignment=mitte),
        "titel2": st("titel2", fontName=h[1], fontSize=stil["groesse_titel"] * 0.72,
                     leading=stil["groesse_titel"] * 0.9, textColor=tinte, alignment=mitte),
        "untertitel": st("untertitel", fontName=x[0], fontSize=10.5, leading=14,
                         textColor=grau, alignment=mitte),
        "variante": st("variante", fontName=T["b"] if tuda else h[1],
                       fontSize=13 if tuda else 13.5, leading=17, alignment=mitte),
        "kopfzeile_deck": st("kopfzeile_deck", fontName=x[0], fontSize=8.8,
                             leading=11.5, textColor=grau),
        "kopfzeile_deck_r": st("kopfzeile_deck_r", fontName=x[0],
                               fontSize=8.4 if tuda else 8.8, leading=11.5,
                               textColor=grau, alignment=TA_RIGHT),
        "marke": st("marke", fontName=h[1], fontSize=11, leading=13.5, textColor=akz),
        "zeile_z": st("zeile_z", fontName=h[0], fontSize=12, leading=16, alignment=mitte),
        "zeile_mitte_klein": st("zeile_mitte_klein", fontName=x[0], fontSize=9,
                                leading=12, textColor=grau, alignment=TA_CENTER),
        # Deckblatt in TUDa-Gestaltung
        "kicker": st("kicker", fontName=T["sb"], fontSize=8.8, leading=11.5, textColor=akz),
        "lead": st("lead", fontName=T["r"], fontSize=10.5, leading=14, textColor=text2),
        "lockup_name": st("lockup_name", fontName=T["b"], fontSize=15, leading=17.5,
                          textColor=ink),
        "lockup_zeile": st("lockup_zeile", fontName=T["r"], fontSize=9.6, leading=12.2,
                           textColor=text2),
        "label": st("label", fontName=x[0], fontSize=7.8 if tuda else 8, leading=10.5,
                    textColor=grau),
        "wert": st("wert", fontName=sb if tuda else t[0], fontSize=11.5 if tuda else fs,
                   leading=14 if tuda else fs * 1.3),
        "h_abschnitt": st("h_abschnitt", fontName=sb, fontSize=8.6 if tuda else 8.8,
                          leading=11.5, textColor=tinte if tuda else akz),
        "klein": st("klein", fontSize=fs * (0.94 if tuda else 0.9),
                    leading=fs * (0.94 if tuda else 0.9) * 1.42),
        "hinweis_nr": st("hinweis_nr", fontName=sb if tuda else t[0],
                         fontSize=fs * (0.94 if tuda else 0.9),
                         leading=fs * (0.94 if tuda else 0.9) * 1.42,
                         textColor=grau if tuda else tinte),
        # KI-Hinweis und Materialkasten sehen in jeder Vorlage gleich aus
        "ki": st("ki", fontName=T["r"], fontSize=8.6, leading=12.2, textColor=ink),
        "gl_art": st("gl_art", fontName=T["sb"], fontSize=8.8, leading=12.4, textColor=ink),
        "gl_umfang": st("gl_umfang", fontName=T["r"], fontSize=8.8, leading=12.4,
                        textColor=ink),
        # Aufgaben
        "aufgabe": st("aufgabe", fontName=h[1], fontSize=stil["groesse_aufgabe"],
                      leading=stil["groesse_aufgabe"] * 1.25, textColor=tinte),
        "aufgabe_p": st("aufgabe_p", fontName=x[0], fontSize=8.6 if tuda else 9,
                        leading=12, textColor=grau, alignment=TA_RIGHT),
        "ta_label": st("ta_label", fontName=sb if tuda else t[1], textColor=tinte),
        "ta_punkte": st("ta_punkte", fontName=x[0], fontSize=8.4 if tuda else 8.6,
                        leading=12, textColor=grau, alignment=TA_RIGHT),
        "kasten_r": st("kasten_r", fontName=x[0], fontSize=9.2 if tuda else 9.4,
                       leading=12, alignment=TA_RIGHT),
        "kasten": st("kasten", fontName=x[0], fontSize=9.4, leading=12, alignment=TA_CENTER),
        "th": st("th", fontName=sb, fontSize=8.2 if tuda else 8.4, leading=11,
                 textColor=grau if tuda else tinte),
        "th_c": st("th_c", fontName=sb, fontSize=8.2 if tuda else 8.4, leading=11,
                   textColor=grau if tuda else tinte, alignment=TA_CENTER),
        "td": st("td", fontName=x[0], fontSize=8.8 if tuda else 9, leading=12),
        "td_c": st("td_c", fontName=x[0], fontSize=8.8 if tuda else 9, leading=12,
                   alignment=TA_CENTER),
        "beleg": st("beleg", fontName=x[2], fontSize=8, leading=10.5, textColor=grau),
        "lueckentext": st("lueckentext", leading=fs * 1.9),
        "mc_buchstabe": st("mc_buchstabe", fontName=sb, fontSize=9.2 if tuda else 9.4,
                           leading=fs * (1.4 if tuda else 1.36),
                           textColor=grau if tuda else akz),
        "mc_text": st("mc_text", fontSize=fs * 0.98, leading=fs * (1.4 if tuda else 1.36)),
        "mc_falsch": st("mc_falsch", fontName=x[0], fontSize=8.6 if tuda else 8.8,
                        leading=12, textColor=grau),
        "erlaeuterung": st("erlaeuterung", fontSize=fs * 0.95, leading=fs * 0.95 * 1.42),
        "quelle_n": st("quelle_n", fontName=mono, fontSize=8.2 if tuda else 8.8, leading=12,
                       textColor=tinte),
        "schluss": st("schluss", fontName=x[0], fontSize=8.4 if tuda else 8.6, leading=11,
                      textColor=grau, alignment=TA_CENTER),
    }


def _pad(l=0, r=0, o=0, u=0):
    return [("LEFTPADDING", (0, 0), (-1, -1), l), ("RIGHTPADDING", (0, 0), (-1, -1), r),
            ("TOPPADDING", (0, 0), (-1, -1), o), ("BOTTOMPADDING", (0, 0), (-1, -1), u)]


def einruecken(flowables, ein, breite):
    t = Table([[flowables]], colWidths=[breite])
    t.setStyle(TableStyle(_pad(ein, 0, 0, 0)))
    return t


SYMBOLE_AN = [True]


def mit_symbol(name, inhalt, farbe, breite, g=3.3 * mm, abstand=2.2 * mm, versatz=0.6):
    if not SYMBOLE_AN[0] and name != "info":
        return inhalt
    t = Table([[Symbol(name, g, farbe, versatz), inhalt]],
              colWidths=[g + abstand, breite - g - abstand])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad()))
    return t


# ==========================================================================
# Deckblatt
# ==========================================================================
EINHEIT_RE = re.compile(r"\b([A-ZÄÖÜ]{2,5}\d{1,3})\b")   # VL02, UE04, KE3 - nicht F11

MATERIALARTEN = [
    (r"^(VL|VO|V)$", "Vorlesungsfolien"),
    (r"^(UE|UEB|UB|U)$", "Übungen"),
    (r"^(TU|TUT)$", "Tutorien"),
    (r"^(AK|KL|ALT)$", "Altklausuren"),
    (r"^(GP|GD|GDP|PROT)$", "Gedächtnisprotokolle"),
    (r"^(SK|SKR|SC)$", "Skript"),
    (r"^(FS|CASE)$", "Fallstudien"),
    (r"^(LIT|LB)$", "Literatur"),
]


def einheiten_von(a):
    """Materialeinheiten, auf die eine Aufgabe samt Teilaufgaben verweist."""
    gefunden = []
    for ta in teilaufgaben(a):
        for kz in EINHEIT_RE.findall(ta.get("quelle") or a.get("quelle") or ""):
            if kz not in gefunden:
                gefunden.append(kz)
    return sorted(gefunden, key=lambda k: (re.sub(r"\d", "", k), int(re.sub(r"\D", "", k) or 0)))


def grundlagen(daten, stil):
    """Welche Arten von Material der Klausur zugrunde liegen.
    Vorrang hat meta.grundlagen; sonst aus den Quellankern abgeleitet."""
    meta = daten.get("meta", {})
    angabe = meta.get("grundlagen")
    if angabe:
        aus = []
        for g in angabe:
            if isinstance(g, dict):
                aus.append((g.get("art", ""), g.get("umfang", "")))
            else:
                teile = re.split(r"\s*[:–]\s*", str(g), 1)
                aus.append((teile[0], teile[1] if len(teile) > 1 else ""))
        return aus
    arten = {}
    for a in daten["aufgaben"]:
        for kz in einheiten_von(a):
            praefix = re.sub(r"\d+$", "", kz)
            art = next((n for m, n in MATERIALARTEN if re.match(m, praefix)), "Material")
            arten.setdefault(art, [])
            if kz not in arten[art]:
                arten[art].append(kz)
    aus = [(art, ", ".join(kz)) for art, kz in arten.items()]
    if stil.get("quelle"):
        aus.append(("Altklausur", "als Gestaltungsvorlage: %s" % stil["quelle"]))
    return aus


def grundlagen_block(daten, stil, S, breite):
    """Verwendete Materialarten als Infokasten (TUDa-Alert "info")."""
    zeilen = grundlagen(daten, stil)
    if not zeilen:
        return []
    T = S["_T"]
    innen = Infokasten.innenbreite(breite)
    sp1 = min(42 * mm, innen * 0.4)
    rows = [[Paragraph(rt(art, T["sb"]), S["gl_art"]), Paragraph(rt(umfang, T["r"]), S["gl_umfang"])]
            for art, umfang in zeilen]
    t = Table(rows, colWidths=[sp1, innen - sp1])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEBELOW", (0, 0), (-1, -2), 0.35, hx(TUDA["info_rand"]))] +
                          _pad(0, 0, 1.1 * mm, 1.1 * mm)))
    kasten = Infokasten("buch", "Erstellt auf Grundlage von", [t], breite,
                        hx(TUDA["info"]), hx(TUDA["info_flaeche"]), hx(TUDA["info_rand"]),
                        T["sb"], titel_farbe=hx(TUDA["ink"]))
    return [kasten, Spacer(1, 4.5 * mm)]


def aufgaben_uebersicht(daten, stil, S, breite):
    """Fuer die Musterloesung: Aufgabe, Thema, Materialeinheiten, Punkte."""
    meta = daten.get("meta", {})
    namen = meta.get("materialien") or {}
    tuda = S["_tuda"]
    akz = hx(stil["akzent"])
    hl = hx(stil["haarlinie"])
    stark = hx(TUDA["linie_stark"]) if tuda else akz
    rows = [[Paragraph("Aufgabe", S["th"]), Paragraph("Thema", S["th"]),
             Paragraph("Material", S["th"]), Paragraph("Punkte", S["th_c"])]]
    for a in daten["aufgaben"]:
        thema = a.get("titel") or ""
        if a.get("thema") and a.get("thema") != thema:
            thema = "%s <font color='%s'>· %s</font>" % (rt(thema, S["_x"][0]), stil["grau"],
                                                         rt(a["thema"], S["_x"][0]))
        else:
            thema = rt(thema, S["_x"][0])
        if tuda:
            kz_fmt = "<font name='%s' size='8.2'>%%s</font>" % S["_mono"]
            mat = "<br/>".join((kz_fmt % rt(kz)) + ("&#160;&#160;" + rt(namen[kz], S["_x"][0])
                                                    if kz in namen else "")
                               for kz in einheiten_von(a)) or "–"
        else:
            mat = "<br/>".join(rt(("%s  %s" % (kz, namen[kz])) if kz in namen else kz)
                               for kz in einheiten_von(a)) or "–"
        rows.append([Paragraph(nummer(a), S["td_c"]), Paragraph(thema, S["td"]),
                     Paragraph(mat, S["td"]), Paragraph(de(a_punkte(a)), S["td_c"])])
    rows.append([Paragraph("", S["td"]), Paragraph("<b>Summe</b>", S["td"]), Paragraph("", S["td"]),
                 Paragraph("<b>%s</b>" % de(gesamtpunkte(daten["aufgaben"])), S["td_c"])])
    t = Table(rows, colWidths=[18 * mm, breite - 18 * mm - 58 * mm - 20 * mm, 58 * mm, 20 * mm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.9 if not tuda else 0.8, stark),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, stark),
        ("LINEBELOW", (0, 1), (-1, -3), 0.3, hl),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, stark),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9 if not tuda else 0.8, stark),
        ("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(3, 3, 2.6, 2.6)))
    if tuda:
        kopf = Paragraph("Aufgaben im Überblick", S["kicker"])
    else:
        kopf = mit_symbol("blaetter", Paragraph("Aufgaben im Überblick", S["h_abschnitt"]),
                          akz, breite, g=3.1 * mm)
    # zusammenhalten: lieber ganz auf die naechste Seite als eine verwaiste Summenzeile
    return [KeepTogether([kopf, Spacer(1, 2 * mm), t])]


def zeichen_kopf(meta, stil, S, breite):
    """Deckblattkopf: Zeichen mit Name und Zeile, rechts Hochschule und Fachbereich."""
    T = S["_T"]
    g = stil.get("logo_mm", 16) * mm
    zeile = meta.get("byline")
    if zeile is None:
        zeile = stil.get("zeichen_zeile", "")
    marke = [Paragraph(rt(stil.get("zeichen_name") or "Probeklausur", T["b"]), S["lockup_name"])]
    if zeile:
        marke += [Spacer(1, 0.6 * mm), Paragraph(rt(zeile, T["r"]), S["lockup_zeile"])]
    rechts = "<br/>".join(rt(x, T["r"]) for x in [meta.get("hochschule"),
                                                  meta.get("fachbereich")] if x)
    if stil.get("logo") == "eigen":
        zellen, breiten = [Zeichen(g, "kachel"), marke], [g + 4 * mm, 62 * mm]
    else:
        zellen, breiten = [marke], [62 * mm]
    zellen.append(Paragraph(rechts, S["kopfzeile_deck_r"]))
    breiten.append(breite - sum(breiten))
    t = Table([zellen], colWidths=breiten)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")] + _pad()))
    return t


def kennzahlen(meta, aufgaben, stil, S, breite):
    """Eckdaten als Kennzahlenzeile (TUDa Facts): Icon und Beschriftung, darunter
    der Wert, getrennt durch Haarlinien, ohne Flaeche."""
    eck = []
    if meta.get("bearbeitungszeit_min"):
        eck.append(("uhr", "Bearbeitungszeit", "%s Minuten" % meta["bearbeitungszeit_min"]))
    eck.append(("punkte", "Punkte", de(gesamtpunkte(aufgaben))))
    eck.append(("blaetter", "Aufgaben", str(len(aufgaben))))
    if meta.get("hilfsmittel"):
        eck.append(("stift", "Hilfsmittel", meta["hilfsmittel"]))
    n = len(eck)
    gw = S["wert"].fontSize
    # Platzbedarf je Spalte: Icon und Beschriftung oder Wert in einer Zeile, plus Abstaende
    bedarf = [max(pdfmetrics.stringWidth(la, S["label"].fontName, S["label"].fontSize) + 4.7 * mm,
                  pdfmetrics.stringWidth(we, S["_sb"], gw)) + (7.5 * mm if i else 3 * mm)
              for i, (sy, la, we) in enumerate(eck)]
    lang = None
    if max(bedarf) <= breite / float(n):
        spalten = [breite / float(n)] * n
    elif sum(bedarf) <= breite:
        extra = (breite - sum(bedarf)) / float(n)
        spalten = [b + extra for b in bedarf]
    else:
        # ein langer Wert (meist Hilfsmittel): die anderen Spalten auf Bedarf, er bekommt
        # den Rest und steht kleiner, damit er in zwei Zeilen passt
        lang = bedarf.index(max(bedarf))
        spalten = list(bedarf)
        spalten[lang] = breite - (sum(bedarf) - bedarf[lang])
    klein = ParagraphStyle("wert_lang", parent=S["wert"], fontSize=gw * 0.82, leading=gw * 1.04)
    grau = hx(TUDA["text2"])
    zellen = []
    for i, (sy, la, we) in enumerate(eck):
        innen = spalten[i] - (4.5 * mm if i else 0) - 3 * mm
        kopf = mit_symbol(sy, Paragraph(rt(la), S["label"]), grau, innen,
                          g=3.2 * mm, abstand=1.5 * mm, versatz=-0.2)
        zellen.append([kopf, Spacer(1, 1.3 * mm),
                       Paragraph(rt(we, S["_sb"]), klein if i == lang else S["wert"])])
    t = Table([zellen], colWidths=spalten)
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(0, 3 * mm, 0.5 * mm, 0.5 * mm)
    for i in range(1, len(eck)):
        cmds += [("LINEBEFORE", (i, 0), (i, 0), 0.5, hx(stil["haarlinie"])),
                 ("LEFTPADDING", (i, 0), (i, 0), 4.5 * mm)]
    t.setStyle(TableStyle(cmds))
    return t


def personalien_block(felder, stil, S, breite, tinte):
    zeilen, reihe = [], []
    for i, lab in enumerate(felder):
        zelle = [Spacer(1, 6 * mm), Linie(0.6, tinte), Spacer(1, 1.2 * mm),
                 Paragraph(rt(lab), S["label"])]
        if i == 0:
            zeilen.append([zelle, ""])
        else:
            reihe.append(zelle)
            if len(reihe) == 2:
                zeilen.append(reihe)
                reihe = []
    if reihe:
        zeilen.append(reihe + [""])
    pt = Table(zeilen, colWidths=[breite / 2.0, breite / 2.0])
    cmds = [("VALIGN", (0, 0), (-1, -1), "BOTTOM")] + _pad(0, 8 * mm, 0, 1.5 * mm) + \
        [("RIGHTPADDING", (-1, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0)]
    if zeilen and zeilen[0][1] == "":
        cmds.append(("SPAN", (0, 0), (1, 0)))
    pt.setStyle(TableStyle(cmds))
    return pt


def deckblatt_tuda(daten, stil, S, modus, breite):
    """Generisches Deckblatt im Stil von TUDa UI: Zeichen mit Name, Dachzeile,
    grosser Titel, Kennzahlenzeile, Hinweiskaesten, Punkteuebersicht."""
    meta = daten.get("meta", {})
    aufgaben = daten["aufgaben"]
    T = S["_T"]
    f = [zeichen_kopf(meta, stil, S, breite), Spacer(1, 11 * mm)]

    # Titelblock: Dachzeile, grosser Titel, Lead
    if meta.get("semester"):
        f += [Paragraph(rt(meta["semester"], T["sb"]), S["kicker"]), Spacer(1, 1.6 * mm)]
    titel = meta.get("modul", "")
    if all(ord(ch) in _CMAPS.get(T["xb"], ()) for ch in titel if ord(ch) > 127) \
            or not _CMAPS.get(T["xb"]):
        f.append(Grosstitel(titel, T["xb"], stil["groesse_titel"], hx(TUDA["ink"])))
    else:
        f.append(Paragraph(rt(titel, T["xb"]), ParagraphStyle(
            "titel_ersatz", fontName=T["xb"], fontSize=stil["groesse_titel"],
            leading=stil["groesse_titel"] * 1.1, textColor=hx(TUDA["ink"]))))
    lead = []
    if meta.get("modulkuerzel"):
        lead.append("<font name='%s'>%s</font>" % (T["mono"], rt(meta["modulkuerzel"])))
    if meta.get("dozent"):
        lead.append(rt(meta["dozent"], T["r"]))
    if lead:
        f += [Spacer(1, 2.4 * mm), Paragraph(" · ".join(lead), S["lead"])]
    variante = meta.get("variante") or "Probeklausur"
    if modus == "loesung":
        variante += " — Musterlösung und Bewertungsschema"
    f += [Spacer(1, 6.5 * mm), Paragraph(rt(variante, T["b"]), S["variante"]),
          Spacer(1, 3.5 * mm), Linie(0.5, hx(stil["haarlinie"])), Spacer(1, 3.5 * mm)]

    # Kennzahlenzeile
    if stil["deckblatt"].get("eckdaten", True):
        f += [kennzahlen(meta, aufgaben, stil, S, breite), Spacer(1, 7 * mm)]

    if stil["deckblatt"].get("grundlagen", True):
        f += grundlagen_block(daten, stil, S, breite)

    # Personalien (nur wenn ausdruecklich konfiguriert)
    if modus == "aufgaben" and stil["deckblatt"].get("personalien"):
        f += [personalien_block(stil["deckblatt"]["personalien"], stil, S, breite,
                                hx(stil["tinte"])), Spacer(1, 7 * mm)]

    f += [ki_kasten(meta, stil, S, breite), Spacer(1, 6 * mm)]

    if meta.get("hinweise") and modus == "aufgaben":
        f += [Paragraph(rt(stil["deckblatt"]["hinweise_titel"], T["sb"]), S["kicker"]),
              Spacer(1, 2 * mm)]
        zeilen = []
        for i, h in enumerate(meta["hinweise"], 1):
            marke = "%d." % i if stil["deckblatt"].get("hinweise_stil") != "punkte" else "–"
            zeilen.append([Paragraph(marke, S["hinweis_nr"]),
                           Paragraph(rt(h, S["_t"][0]), S["klein"])])
        t = Table(zeilen, colWidths=[6 * mm, breite - 6 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(0, 0, 0, 1.4)))
        f += [t, Spacer(1, 6.5 * mm)]

    if modus == "loesung":
        f += aufgaben_uebersicht(daten, stil, S, breite)
        return f
    art = stil["deckblatt"].get("punktetabelle", "horizontal")
    if art != "keine":
        titel_pt = stil["deckblatt"].get("punktetabelle_titel")
        if titel_pt is None:
            titel_pt = "Punkteübersicht"
        kopfteil = [Paragraph(rt(titel_pt, T["sb"]), S["kicker"]), Spacer(1, 2 * mm)] \
            if titel_pt else []
        f.append(KeepTogether(kopfteil + punktetabelle(aufgaben, stil, S, modus, breite, art)))
    return f


def deckblatt(daten, stil, S, modus, breite):
    if stil.get("gestaltung") == "tuda":
        return deckblatt_tuda(daten, stil, S, modus, breite)
    meta = daten.get("meta", {})
    aufgaben = daten["aufgaben"]
    db = stil["deckblatt"]
    akz = hx(stil["akzent"])
    hl = hx(stil["haarlinie"])
    tinte = hx(stil["tinte"])
    zentriert = db["ausrichtung"] == "zentriert"
    werte = werte_aus(meta)
    f = []

    # Kopfleiste: Zeichen + Einordnung links, Institution rechts
    links = []
    if stil.get("logo") == "eigen":
        links.append(Zeichen(stil.get("logo_mm", 19) * mm, "tinte"))
    marke = [Paragraph("Probeklausur", S["marke"]),
             Paragraph("zur Selbstkontrolle", S["kopfzeile_deck"])]
    rechts_txt = "<br/>".join(rt(x) for x in [meta.get("hochschule"),
                                              meta.get("fachbereich"),
                                              meta.get("semester")] if x)
    if zentriert:
        if links:
            e = links[0]
            e.hAlign = "CENTER"
            f += [e, Spacer(1, 3 * mm)]
        if rechts_txt and db.get("institution", True):
            f.append(Paragraph(rechts_txt, S["zeile_mitte_klein"]))
        f.append(Spacer(1, 6 * mm))
    else:
        if links:
            kopf = Table([[links[0], marke, Paragraph(rechts_txt, S["kopfzeile_deck_r"])]],
                         colWidths=[23 * mm, 55 * mm, breite - 78 * mm])
        else:
            kopf = Table([[marke, Paragraph(rechts_txt, S["kopfzeile_deck_r"])]],
                         colWidths=[70 * mm, breite - 70 * mm])
        kopf.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")] + _pad()))
        f += [kopf, Spacer(1, 7 * mm)]

    # Titelblock
    if db.get("titelzeilen"):
        for i, z in enumerate(db["titelzeilen"]):
            txt = fmt(z, **werte)
            if txt:
                f.append(Paragraph(rt(txt), S["titel"] if i == 0 else
                                   (S["titel2"] if i == 1 else S["zeile_z"])))
                f.append(Spacer(1, 1.5 * mm))
    else:
        f.append(Paragraph(rt(meta.get("modul", "")), S["titel"]))
        unter = "   ·   ".join(x for x in [meta.get("modulkuerzel"),
                                           meta.get("dozent")] if x)
        if unter:
            f.append(Spacer(1, 1.5 * mm))
            f.append(Paragraph(rt(unter), S["untertitel"]))
    f.append(Spacer(1, 3 * mm))
    if db.get("linie", True):
        f.append(Linie(1.3, akz, doppelt=True, farbe2=hl, nach=3))
    titel = meta.get("variante") or "Probeklausur"
    if modus == "loesung":
        titel += " — Musterlösung und Bewertungsschema"
    if db.get("variante_zeile", True) or modus == "loesung":
        f += [Paragraph(rt(titel if db.get("variante_zeile", True) else
                           "Musterlösung und Bewertungsschema"), S["variante"])]
    f.append(Spacer(1, 7 * mm))

    # Eckdaten mit Symbolen, zweispaltig
    if db.get("eckdaten", True):
        eck = []
        if meta.get("bearbeitungszeit_min"):
            eck.append(("uhr", "Bearbeitungszeit", "%s Minuten" % meta["bearbeitungszeit_min"]))
        eck.append(("punkte", "Erreichbare Punkte", de(gesamtpunkte(aufgaben))))
        eck.append(("blaetter", "Aufgaben", str(len(aufgaben))))
        if meta.get("hilfsmittel"):
            eck.append(("stift", "Zugelassene Hilfsmittel", meta["hilfsmittel"]))
        zellen = []
        sp = (breite - 8 * mm) / 2.0
        for sym, lab, wert in eck:
            inhalt = [Paragraph(rt(lab), S["label"]), Paragraph(rt(wert), S["wert"])]
            zellen.append(mit_symbol(sym, inhalt, akz, sp, g=4.2 * mm, abstand=3 * mm)
                          if SYMBOLE_AN[0] else inhalt)
        zeilen = [zellen[i:i + 2] + [""] * (2 - len(zellen[i:i + 2]))
                  for i in range(0, len(zellen), 2)]
        t = Table(zeilen, colWidths=[sp + 8 * mm, sp])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")] +
                              _pad(0, 0, 0, 4.5 * mm)))
        f += [t, Spacer(1, 3 * mm)]

    # Personalien
    if modus == "aufgaben" and db.get("personalien") and \
            db.get("personalien_stil") == "zeile":
        zeilen = [[Paragraph(rt(lab) + ":", S["wert"]), ""] for lab in db["personalien"]]
        t = Table(zeilen, colWidths=[40 * mm, breite - 40 * mm],
                  rowHeights=[11 * mm] * len(zeilen))
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                               ("LINEBELOW", (1, 0), (1, -1), 0.6, tinte)] +
                              _pad(0, 0, 0, 1.2 * mm)))
        f += [t, Spacer(1, 8 * mm)]
    elif modus == "aufgaben" and db.get("personalien"):
        felder = db["personalien"]
        zeilen, reihe = [], []
        for i, lab in enumerate(felder):
            zelle = [Spacer(1, 7 * mm), Linie(0.6, tinte), Spacer(1, 1.2 * mm),
                     Paragraph(rt(lab), S["label"])]
            if i == 0:
                zeilen.append([zelle, ""])
            else:
                reihe.append(zelle)
                if len(reihe) == 2:
                    zeilen.append(reihe)
                    reihe = []
        if reihe:
            zeilen.append(reihe + [""])
        t = Table(zeilen, colWidths=[breite / 2.0 - 4 * mm, breite / 2.0 + 4 * mm])
        cmds = [("VALIGN", (0, 0), (-1, -1), "BOTTOM")] + _pad(0, 8 * mm, 0, 1 * mm) + \
            [("RIGHTPADDING", (-1, 0), (-1, -1), 0)]
        if zeilen and zeilen[0][1] == "":
            cmds.append(("SPAN", (0, 0), (1, 0)))
        t.setStyle(TableStyle(cmds))
        f += [t, Spacer(1, 6 * mm)]

    if db.get("grundlagen", True):
        f += grundlagen_block(daten, stil, S, breite)

    # KI-Hinweis
    f.append(ki_kasten(meta, stil, S, breite))
    f.append(Spacer(1, 5 * mm))

    # Hinweise zur Bearbeitung
    if meta.get("hinweise") and modus == "aufgaben":
        if stil.get("symbole", True):
            f.append(mit_symbol("liste", Paragraph(rt(db["hinweise_titel"]),
                                                   S["h_abschnitt"]), akz, breite,
                                g=3 * mm))
        else:
            f.append(Paragraph("<b>%s</b>" % rt(db["hinweise_titel"]),
                               S["zeile_z"] if db.get("hinweise_ausrichtung") == "zentriert"
                               else S["wert"]))
        f.append(Spacer(1, 1.5 * mm))
        zeilen = []
        for i, h in enumerate(meta["hinweise"], 1):
            marke_h = "%d." % i if db.get("hinweise_stil") == "nummeriert" else "–"
            zeilen.append([Paragraph(marke_h, S["klein"]), Paragraph(rt(h), S["klein"])])
        t = Table(zeilen, colWidths=[6 * mm, breite - 6 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(0, 0, 0, 1.2)))
        f += [t, Spacer(1, 6 * mm)]

    # Punkteuebersicht bzw. in der Loesung die Aufgabenuebersicht
    art = db.get("punktetabelle", "horizontal")
    if modus == "loesung":
        f += aufgaben_uebersicht(daten, stil, S, breite)
    elif art != "keine":
        titel_pt = db.get("punktetabelle_titel")
        if titel_pt is None:
            titel_pt = "Punkteübersicht" if modus == "aufgaben" else "Punkteverteilung"
        kopfteil = []
        if titel_pt:
            p_t = Paragraph(rt(titel_pt), S["h_abschnitt"])
            kopfteil = [mit_symbol("punkte", p_t, akz, breite, g=3 * mm)
                        if stil.get("symbole", True) else p_t, Spacer(1, 2 * mm)]
        f.append(KeepTogether(kopfteil + punktetabelle(aufgaben, stil, S, modus,
                                                       breite, art)))
    return f


def ki_kasten(meta, stil, S, breite):
    """KI-Hinweis als gerahmter Kasten mit rotem Akzent, in jeder Vorlage gleich."""
    T = S["_T"]
    txt = meta.get("ki_hinweis") or KI_HINWEIS
    return Infokasten("hinweis", "KI-generiert – keine offizielle Prüfung",
                      [Paragraph(rt(txt, T["r"]), S["ki"])], breite,
                      hx(TUDA["fehler"]), hx(TUDA["fehler_flaeche"]), hx(TUDA["fehler_rand"]),
                      T["sb"])


def punktetabelle(aufgaben, stil, S, modus, breite, art):
    hl = hx(stil["haarlinie"])
    tinte = hx(stil["tinte"])
    fl = hx(stil["flaeche"])
    tuda = stil.get("gestaltung") == "tuda"
    stark = hx(TUDA["linie_stark"])
    nrs = [nummer(a) for a in aufgaben]
    pkt = [de(a_punkte(a)) for a in aufgaben]
    summe = de(gesamtpunkte(aufgaben))
    if art == "vertikal":
        rows = [[Paragraph("Aufgabe", S["th"]), Paragraph("Punkte", S["th_c"])] +
                ([Paragraph("erreicht", S["th_c"])] if modus == "aufgaben" else [])]
        for a, p in zip(aufgaben, pkt):
            rows.append([Paragraph(rt("%s  %s" % (nummer(a), a.get("titel", "")), S["_x"][0]),
                                   S["td"]),
                         Paragraph(p, S["td_c"])] +
                        ([""] if modus == "aufgaben" else []))
        rows.append([Paragraph("<b>Summe</b>", S["td"]), Paragraph("<b>%s</b>" % summe, S["td_c"])]
                    + ([""] if modus == "aufgaben" else []))
        cw = [breite - 48 * mm, 24 * mm, 24 * mm] if modus == "aufgaben" else \
             [breite - 24 * mm, 24 * mm]
        t = Table(rows, colWidths=cw)
        linie = stark if tuda else tinte
        t.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.9 if not tuda else 0.8, linie),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, linie),
            ("LINEBELOW", (0, 1), (-1, -2), 0.35, hl),
            ("LINEABOVE", (0, -1), (-1, -1), 0.5, linie),
            ("LINEBELOW", (0, -1), (-1, -1), 0.9 if not tuda else 0.8, linie),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")] + _pad(3, 3, 3.5, 3.5)))
        return [t]

    # horizontal: bis 14 Aufgaben in einer Zeile, darueber gleich grosse Bloecke
    je_zeile = int(math.ceil(len(nrs) / math.ceil(len(nrs) / 14.0))) if nrs else 1
    erste = 22 * mm
    rest = min((breite - erste) / 11.0, (breite - erste) / float(je_zeile + 1))
    # Summenzeichen aus der Tabellenschrift, sonst das griechische Sigma
    summenzeichen = "\u2211" if 0x2211 in (_CMAPS.get(S["_sb"]) or ()) else "Σ"
    bloecke = []
    for start in range(0, len(nrs), je_zeile):
        teil_n = nrs[start:start + je_zeile]
        teil_p = pkt[start:start + je_zeile]
        letzter = start + je_zeile >= len(nrs)
        z_max, z_err = (stil["deckblatt"].get("punktetabelle_zeilen") or
                        ["max.", "erreicht"])[:2]
        kopf = ["Aufgabe"] + teil_n + ([summenzeichen] if letzter else [])
        max_z = [z_max] + teil_p + ([summe] if letzter else [])
        rows = [[Paragraph(rt(x, S["_sb"]), S["th_c"] if i else S["th"])
                 for i, x in enumerate(kopf)],
                [Paragraph(rt(x, S["_x"][0]), S["td_c"] if i else S["td"])
                 for i, x in enumerate(max_z)]]
        if modus == "aufgaben":
            rows.append([Paragraph(rt(z_err), S["td"])] + [""] * (len(kopf) - 1))
        t = Table(rows, colWidths=[erste] + [rest] * (len(kopf) - 1),
                  rowHeights=[None, None] + ([10 * mm] if modus == "aufgaben" else []))
        if tuda:
            cmds = [("INNERGRID", (0, 0), (-1, -1), 0.4, hl),
                    ("BOX", (0, 0), (-1, -1), 0.6, hl),
                    ("ROUNDEDCORNERS", [2.4 * mm] * 4),
                    ("BACKGROUND", (0, 0), (-1, 0), fl),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.7, stark),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE")] + _pad(3, 3, 3.2, 3.2)
            if letzter:
                cmds.append(("LINEBEFORE", (-1, 0), (-1, -1), 0.7, stark))
        else:
            cmds = [("GRID", (0, 0), (-1, -1), 0.45, tinte),
                    ("BACKGROUND", (0, 0), (-1, 0), fl),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE")] + _pad(3, 3, 3, 3)
            if letzter:
                cmds.append(("LINEBEFORE", (-1, 0), (-1, -1), 1.2, tinte))
        t.setStyle(TableStyle(cmds))
        t.hAlign = "LEFT"
        bloecke += [t, Spacer(1, 2 * mm)]
    return bloecke


# ==========================================================================
# Aufgaben
# ==========================================================================
def nummer(a):
    return re.sub(r"^A", "", str(a.get("id", "")))


def teilaufgaben(a):
    tas = a.get("teilaufgaben")
    if tas:
        return tas
    return [{"nr": "", "punkte": a.get("punkte", 0), "text": a.get("text", ""),
             "loesung": a.get("loesung", ""), "bewertung": a.get("bewertung", []),
             "quelle": a.get("quelle", ""), "antwortraum": a.get("antwortraum"),
             "antwortraum_zeilen": a.get("antwortraum_zeilen"),
             "antwortraum_hoehe_mm": a.get("antwortraum_hoehe_mm"),
             "tabelle": a.get("tabelle"), "tabelle_loesung": a.get("tabelle_loesung"),
             "bild": a.get("bild")}]


def a_punkte(a):
    if a.get("punkte") is not None:
        return float(a["punkte"])
    return sum(float(t.get("punkte", 0)) for t in teilaufgaben(a))


def gesamtpunkte(aufgaben):
    return sum(a_punkte(a) for a in aufgaben)


def werte_aus(meta):
    return {k: meta.get(k, "") for k in
            ("modul", "modulkuerzel", "variante", "semester", "hochschule",
             "fachbereich", "dozent", "pruefungsdatum")}


def aufgabenkopf(a, stil, S, modus, breite):
    """Aufgabenueberschrift: Titel in Tinte, Punkte rechts, Kasten fuer die
    erreichten Punkte, Linie darunter."""
    tinte = hx(stil["tinte"])
    tuda = stil.get("gestaltung") == "tuda"
    linie = tinte if tuda else hx(stil["akzent"])
    w = {"nr": nummer(a), "titel": a.get("titel", ""), "punkte": de(a_punkte(a))}
    vorlage = stil["aufgabe_titel"] if a.get("titel") else stil["aufgabe_titel_ohne"]
    titel = fmt(vorlage, **w)
    punkte_im_titel = "{punkte}" in vorlage
    zellen = [Paragraph(rt(titel, S["_h"][1]), S["aufgabe"])]
    breiten = [None]
    if not punkte_im_titel and stil.get("aufgabe_punkte"):
        zellen.append(Paragraph(rt(fmt(stil["aufgabe_punkte"], **w)), S["aufgabe_p"]))
        breiten.append(22 * mm)
    if stil.get("punktekasten"):
        if modus == "aufgaben":
            kasten = Table([[Paragraph("/ %s" % de(a_punkte(a)), S["kasten_r"])]],
                           colWidths=[20 * mm], rowHeights=[8.5 * mm])
            kasten.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.7 if tuda else 0.8, tinte),
                                        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                                        ("VALIGN", (0, 0), (-1, -1), "BOTTOM")] +
                                       _pad(2, 2.5 * mm, 0, 1.2 * mm)))
            zellen.append(kasten)
            breiten.append(24 * mm)
    fest = sum(b for b in breiten[1:])
    breiten[0] = breite - fest
    t = Table([zellen], colWidths=breiten)
    cmds = [("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("ALIGN", (-1, 0), (-1, 0), "RIGHT")] \
        + _pad(0, 0, 0, 2.2 * mm)
    if stil.get("aufgabe_linie", True):
        cmds.append(("LINEBELOW", (0, 0), (-1, 0), 0.7 if tuda else 0.8, linie))
    t.setStyle(TableStyle(cmds))
    return t


class Kaestchen(Flowable):
    """Eckiges Ankreuzfeld; mit haken=True in der Musterloesung blau angekreuzt."""

    def __init__(self, haken=False, seite=3.5 * mm):
        super().__init__()
        self.haken, self.seite = haken, seite

    def wrap(self, aw, ah):
        self.width, self.height = self.seite, self.seite + 1.4 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(hx(TUDA["linie_stark"]))
        c.setLineWidth(0.7)
        c.rect(0, 0.9 * mm, self.seite, self.seite, stroke=1, fill=0)
        if self.haken:
            # Kreuz wie beim handschriftlichen Ankreuzen
            g = self.seite
            y0 = 0.9 * mm
            e = 0.2 * g
            c.setStrokeColor(hx(LOESUNG_BLAU))
            c.setLineWidth(1.3)
            c.setLineCap(1)
            c.line(e, y0 + e, g - e, y0 + g - e)
            c.line(e, y0 + g - e, g - e, y0 + e)


def mc_optionen(opts, stil, S, breite, einzug=0, geloest=False):
    """Antwortoptionen wie im Skill mc-fragen: Buchstabe, Ankreuzfeld, Text."""
    zeilen = []
    for j, o in enumerate(opts):
        richtig = bool(o.get("richtig"))
        text = rt(o.get("text", ""), S["_t"][0])
        if geloest and richtig:
            text = '<font color="%s"><b>%s</b></font>' % (LOESUNG_BLAU, text)
        zeilen.append(["", Paragraph(BUCHSTABEN_MC[j], S["mc_buchstabe"]),
                       Kaestchen(haken=geloest and richtig), Paragraph(text, S["mc_text"])])
    t = Table(zeilen, colWidths=[einzug or 0.01, 6 * mm, 7 * mm,
                                 breite - (einzug or 0.01) - 13 * mm])
    t.hAlign = "LEFT"
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(0, 2, 1.2, 1.2)))
    return t


BUCHSTABEN_MC = "ABCDEFGH"


def loesungs_tabelle(ta):
    """Tabelle fuer die Musterloesung mit [[...]] an den Loesungszellen, oder None.
    Quelle entweder [[...]] direkt in ta.tabelle oder ta.tabelle_loesung, deren
    Abweichungen von ta.tabelle automatisch als Loesung markiert werden."""
    leer = ta.get("tabelle") or {}
    voll = ta.get("tabelle_loesung")
    if voll:
        z_leer = leer.get("zeilen") or []
        neu_z = []
        for i, zeile in enumerate(voll.get("zeilen") or []):
            alt_z = z_leer[i] if i < len(z_leer) else []
            neu_z.append([("[[%s]]" % c) if str(c).strip() and
                          (j >= len(alt_z) or str(alt_z[j]).strip() != str(c).strip())
                          else c for j, c in enumerate(zeile)])
        return dict(voll, header=voll.get("header") or leer.get("header"), zeilen=neu_z)
    if leer and any("[[" in str(c) for z in (leer.get("zeilen") or []) for c in z):
        return leer
    return None


def tabelle_block(spec, stil, S, breite, luecken="zelle"):
    kopf, zeilen = spec.get("header") or [], spec.get("zeilen") or []
    if not zeilen and not kopf:
        return []
    rows = ([[Paragraph(rt(x, S["_sb"], luecken=luecken), S["th"]) for x in kopf]]
            if kopf else []) + \
        [[Paragraph(rt(x, S["_x"][0], luecken=luecken), S["td"]) for x in z] for z in zeilen]
    n = max(len(r) for r in rows)
    for r in rows:
        r += [Paragraph("", S["td"])] * (n - len(r))
    cw = spec.get("spaltenbreiten_mm")
    cw = [x * mm for x in cw] if cw else [breite / n] * n
    t = Table(rows, colWidths=cw, repeatRows=1 if kopf else 0)
    gitter = hx(TUDA["linie_stark"]) if stil.get("gestaltung") == "tuda" else hx(stil["tinte"])
    cmds = [("GRID", (0, 0), (-1, -1), 0.5 if stil.get("gestaltung") == "tuda" else 0.45, gitter),
            ("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(4, 4, 3.5, 3.5)
    if kopf:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), hx(stil["flaeche"])))
    t.setStyle(TableStyle(cmds))
    return [Spacer(1, 2.5 * mm), t, Spacer(1, 2.5 * mm)]


def bild_block(spec, basis, S):
    pfad = spec if isinstance(spec, str) else spec.get("pfad")
    if pfad and not os.path.isabs(pfad):
        pfad = os.path.join(basis, pfad)
    if not pfad or not os.path.exists(pfad):
        return [Paragraph(rt("[Abbildung fehlt: %s]" % pfad), S["beleg"])]
    b_mm = (spec.get("breite_mm") if isinstance(spec, dict) else None) or 120
    img = Image(pfad)
    img.drawHeight = img.imageHeight * (b_mm * mm / float(img.imageWidth))
    img.drawWidth = b_mm * mm
    return [Spacer(1, 2.5 * mm), img, Spacer(1, 2.5 * mm)]


def antwortraum(ta, stil, meta, S):
    art = ta.get("antwortraum") or meta.get("antwortraum_stil") or stil["antwortraum_stil"]
    hl = hx(stil["haarlinie"])
    if art in (None, "keiner", "kein", False):
        return [Spacer(1, 3 * mm)]
    if art == "platz":
        z = ta.get("antwortraum_zeilen") or max(3, int(round(float(ta.get("punkte", 2)) * 1.5)))
        return [Spacer(1, z * 8.5 * mm)]
    if art in ("kasten", "raster"):
        return [Spacer(1, 2 * mm),
                AntwortKasten(ta.get("antwortraum_hoehe_mm", 45), hl, raster=(art == "raster")),
                Spacer(1, 5 * mm)]
    z = ta.get("antwortraum_zeilen")
    if z is None:
        z = max(3, int(round(float(ta.get("punkte", 2)) * 1.5)))
    return [Spacer(1, 1 * mm), AntwortLinien(z, hl), Spacer(1, 5 * mm)]


def bewertung(ta, stil, S, breite):
    krit = ta.get("bewertung") or []
    if not krit:
        return []
    tuda = stil.get("gestaltung") == "tuda"
    linie = hx(TUDA["linie_stark"]) if tuda else hx(stil["tinte"])
    hl = hx(stil["haarlinie"])
    rows = [[Paragraph("Bewertungskriterium", S["th"]), Paragraph("Punkte", S["th_c"])]]
    for k in krit:
        rows.append([Paragraph(rt(k.get("kriterium", ""), S["_x"][0]), S["td"]),
                     Paragraph(de(k.get("punkte", 0)), S["td_c"])])
    rows.append([Paragraph("<b>Summe</b>", S["td"]),
                 Paragraph("<b>%s</b>" % de(sum(float(k.get("punkte", 0)) for k in krit)), S["td_c"])])
    t = Table(rows, colWidths=[breite - 22 * mm, 22 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, linie),
        ("LINEBELOW", (0, 0), (-1, 0), 0.45, linie),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, hl),
        ("LINEABOVE", (0, -1), (-1, -1), 0.45, linie),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, linie),
        ("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad(3, 3, 3, 3)))
    return [t]


def _loesungsfarben(stil):
    """Linie und Icons der Loesungsbloecke."""
    if stil.get("gestaltung") == "tuda":
        return hx(TUDA["markiert_linie"]), hx(TUDA["text2"])
    akz = hx(stil["akzent"])
    return akz, akz


def mc_bewertung_block(a, meta, stil, S, breite):
    """Einmal je Aufgabe: Bewertungsregel fuer alle MC-Fragen plus Loesungsschluessel."""
    mc = [ta for ta in teilaufgaben(a) if ta.get("optionen")]
    if not mc:
        return []
    linie, icon = _loesungsfarben(stil)
    mehrfach = any(sum(1 for o in ta["optionen"] if o.get("richtig")) > 1 for ta in mc)
    regel = meta.get("mc_bewertung") or (
        "Jede Frage wird mit der angegebenen Punktzahl bewertet, wenn genau alle "
        "richtigen Antworten und keine falsche angekreuzt sind; sonst 0 Punkte."
        if mehrfach else
        "Jede Frage wird mit der angegebenen Punktzahl bewertet, wenn die richtige "
        "Antwort angekreuzt ist. Keine, mehrere oder eine falsche Antwort ergeben 0 Punkte.")
    schluessel = "&#160;&#160;·&#160;&#160; ".join(
        "%s <font color='%s'><b>%s</b></font> <font color='%s'>(%s P.)</font>"
        % (fmt(stil["teilaufgabe_format"], nr=ta.get("nr", "")) if ta.get("nr") else "",
           LOESUNG_BLAU,
           ", ".join(BUCHSTABEN_MC[j] for j, o in enumerate(ta["optionen"]) if o.get("richtig")),
           stil["grau"], de(ta.get("punkte", 0)))
        for ta in mc)
    innen = breite - 8.5 * mm
    inhalt = [Paragraph("Bewertungsschema (Multiple Choice)", S["h_abschnitt"]),
              Spacer(1, 1.3 * mm), Paragraph(rt(regel, S["_t"][0]), S["erlaeuterung"]),
              Spacer(1, 1.6 * mm),
              Paragraph("<font name='%s'>Lösungsschlüssel:</font>&#160;&#160;%s"
                        % (S["_sb"], schluessel), S["td"])]
    t = Table([[Symbol("liste", 3.5 * mm, icon, versatz=0.2 * mm) if SYMBOLE_AN[0] else "",
                inhalt]], colWidths=[8.5 * mm, innen])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEBEFORE", (0, 0), (0, 0), 1.2, linie),
                           ("LEFTPADDING", (0, 0), (0, 0), 3.2 * mm),
                           ("LEFTPADDING", (1, 0), (1, 0), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0.6 * mm),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8 * mm)]))
    return [t, Spacer(1, 5 * mm)]


def loesungsblock(a, ta, stil, S, breite, einzug=0):
    """Musterloesung in vier Abschnitten: Loesung, Erlaeuterung, Quelle, Bewertung."""
    linie, icon = _loesungsfarben(stil)
    hl = hx(stil["haarlinie"])
    sym = SYMBOLE_AN[0]
    icon_b = 8.5 * mm if sym else 3.5 * mm
    inhalt_b = breite - icon_b
    muster = []
    opts = ta.get("optionen") or []
    lsg_tab = loesungs_tabelle(ta)
    if lsg_tab:
        muster += tabelle_block(lsg_tab, stil, S, inhalt_b, luecken="loesung")[1:2]
    if ta.get("lueckentext"):
        if muster:
            muster.append(Spacer(1, 2.5 * mm))
        muster.append(Paragraph(rt(ta["lueckentext"], S["_t"][0], luecken="loesung"),
                                S["lueckentext"]))
    lsg = ta.get("loesung") or ""
    if (lsg if isinstance(lsg, list) else lsg.strip()):
        if muster:
            muster.append(Spacer(1, 2.5 * mm))
        muster += textblock(lsg, S["_t"][0], S["body"], S)
    abschnitte = [] if (opts and not muster) else \
        [("schluessel", "Musterlösung", muster or [Paragraph("–", S["body"])])]
    erl = []
    erl_text = (ta.get("erlaeuterung") or ta.get("erklaerung") or "").strip()
    if erl_text:
        erl += textblock(erl_text, S["_t"][0], S["erlaeuterung"], S)
    falsch = ["<font name='%s'>%s:</font> %s" % (S["_sb"], BUCHSTABEN_MC[j],
                                                 rt(o.get("warum_falsch"), S["_x"][0]))
              for j, o in enumerate(opts)
              if not o.get("richtig") and (o.get("warum_falsch") or "").strip()]
    if falsch:
        if erl:
            erl.append(Spacer(1, 1.5 * mm))
        erl.append(Paragraph("<br/>".join(falsch), S["mc_falsch"]))
    if erl:
        abschnitte.append(("lampe", "Begründung" if opts else "Erläuterung", erl))
    q = ta.get("quelle") or a.get("quelle")
    if q:
        abschnitte.append(("buch", "Quelle", [Paragraph(rt(q, S["_mono"]), S["quelle_n"])]))
    inhalt_b = breite - icon_b
    bw = [] if opts else bewertung(ta, stil, S, inhalt_b)   # MC: Schema einmal je Aufgabe
    if bw:
        abschnitte.append(("liste", "Bewertungsschema", bw))
    rows = []
    for symbol, titel, inhalt in abschnitte:
        links = Symbol(symbol, 3.5 * mm, icon, versatz=0.2 * mm) if sym else ""
        rows.append(["", links, [Paragraph(titel, S["h_abschnitt"]), Spacer(1, 1.3 * mm)]
                     + inhalt])
    t = Table(rows, colWidths=[einzug or 0.01, icon_b, inhalt_b])
    t.hAlign = "LEFT"
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBEFORE", (1, 0), (1, -1), 1.2, linie),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (1, 0), (1, -1), 3.2 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6 * mm),
            ("TOPPADDING", (0, 0), (-1, 0), 0.6 * mm),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 0.8 * mm)]
    if len(rows) > 1:
        cmds.append(("LINEBELOW", (2, 0), (2, -2), 0.4, hl))
    t.setStyle(TableStyle(cmds))
    return t


def aufgaben_flowables(daten, stil, S, modus, breite, basis):
    meta = daten.get("meta", {})
    f = []
    for idx, a in enumerate(daten["aufgaben"]):
        if stil.get("neue_seite_je_aufgabe") and idx > 0:
            f.append(PageBreak())
        else:
            f.append(CondPageBreak(55 * mm))
        kopf = [aufgabenkopf(a, stil, S, modus, breite), Spacer(1, 3.5 * mm)]
        if a.get("einleitung"):
            kopf += [Paragraph(rt(a["einleitung"], S["_t"][0]), S["einleitung"]),
                     Spacer(1, 2 * mm)]
        if modus == "loesung":
            kopf += mc_bewertung_block(a, meta, stil, S, breite)
        f.append(KeepTogether(kopf))
        if a.get("teilaufgaben") and a.get("tabelle"):
            f += tabelle_block(a["tabelle"], stil, S, breite,
                               luecken="zelle" if modus == "aufgaben" else "loesung")
        if a.get("teilaufgaben") and a.get("bild"):
            f += bild_block(a["bild"], basis, S)

        tas = teilaufgaben(a)
        mehrteilig = len(tas) > 1 or bool(tas[0].get("nr"))
        for ta in tas:
            label = fmt(stil["teilaufgabe_format"], nr=ta.get("nr", "")) \
                if mehrteilig and ta.get("nr") else ""
            punkte = fmt(stil["teilpunkte_format"], punkte=de(ta.get("punkte", 0)))
            lab_b = 9 * mm if label else 0
            lk = "leer" if modus == "aufgaben" else "loesung"
            opts = ta.get("optionen") or []
            n_richtig = sum(1 for o in opts if o.get("richtig"))
            if opts and n_richtig > 1 and "richtige Antworten" not in (ta.get("text") or ""):
                ta = dict(ta, text=(ta.get("text") or "") +
                          " <i>(%d richtige Antworten)</i>" % n_richtig)
            if stil.get("teilpunkte_position") == "inline":
                zeile = Table([[Paragraph(rt(label), S["ta_label"]),
                                Paragraph(rt(ta.get("text", ""), S["_t"][0], luecken=lk) + " " +
                                          rt(punkte), S["body"])]],
                              colWidths=[lab_b, breite - lab_b])
            else:
                zeile = Table([[Paragraph(rt(label), S["ta_label"]),
                                Paragraph(rt(ta.get("text", ""), S["_t"][0], luecken=lk),
                                          S["body"]),
                                Paragraph(rt(punkte), S["ta_punkte"])]],
                              colWidths=[lab_b, breite - lab_b - 17 * mm, 17 * mm])
            zeile.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")] + _pad()))
            block = [zeile]
            lsg_tab = loesungs_tabelle(ta)
            if modus == "aufgaben":
                if ta.get("tabelle"):
                    block += tabelle_block(ta["tabelle"], stil, S, breite, luecken="zelle")
                if ta.get("lueckentext"):
                    block += [Spacer(1, 2 * mm),
                              einruecken([Paragraph(rt(ta["lueckentext"], S["_t"][0],
                                                       luecken="leer"), S["lueckentext"])],
                                         lab_b, breite)]
            elif ta.get("tabelle") and not lsg_tab:
                block += tabelle_block(ta["tabelle"], stil, S, breite, luecken="loesung")
            if opts:
                block += [Spacer(1, 1.6 * mm),
                          mc_optionen(opts, stil, S, breite, einzug=lab_b,
                                      geloest=(modus == "loesung"))]
            if ta.get("bild"):
                block += bild_block(ta["bild"], basis, S)
            f.append(KeepTogether(block))

            if modus == "aufgaben":
                f += [Spacer(1, 5 * mm)] if opts else antwortraum(ta, stil, meta, S)
                continue
            f.append(Spacer(1, 2.5 * mm))
            ein = lab_b
            b2 = breite - ein
            f.append(loesungsblock(a, ta, stil, S, b2, einzug=ein))
            f.append(Spacer(1, 6 * mm))
        f.append(Spacer(1, 5 * mm))
    return f


# ==========================================================================
# Vorlage finden
# ==========================================================================
def lade_vorlage(json_pfad, meta, cli):
    wahl = cli or meta.get("vorlage")
    if wahl == "generisch":
        return copy.deepcopy(STANDARD), "generisch"
    kandidaten = []
    if wahl:
        kandidaten.append(wahl if os.path.isabs(wahl)
                          else os.path.join(os.path.dirname(os.path.abspath(json_pfad)), wahl))
    elif meta.get("modulkuerzel"):
        kandidaten.append(os.path.join(os.path.dirname(os.path.abspath(json_pfad)),
                                       "vorlage_%s.json" % meta["modulkuerzel"]))
    for k in kandidaten:
        if os.path.exists(k):
            with open(k, encoding="utf-8") as fh:
                profil = json.load(fh)
            # Nachbildungen einer Altklausur: schlichte Gestaltung, Haarlinie im Kopf
            stil = tief_mischen(tief_mischen(STANDARD, {"gestaltung": "schlicht",
                                                        "kopflinie": "haar"}), profil)
            stil["gestaltung"] = GESTALTUNG_ALIAS.get(stil.get("gestaltung"),
                                                      stil.get("gestaltung"))
            stil["logo"] = "eigen" if profil.get("logo") != "keins" else "keins"
            return stil, os.path.basename(k)
    if wahl:
        print("WARNUNG: Vorlage %s nicht gefunden, nutze generische Vorlage." % wahl)
    return copy.deepcopy(STANDARD), "generisch"


def baue(daten, pfad, modus, stil, basis):
    meta = daten.get("meta", {})
    werte = werte_aus(meta)
    S = baue_stile(stil)
    SYMBOLE_AN[0] = bool(stil.get("symbole", True))
    doc = KlausurDoc(pfad, stil, werte, modus)
    breite = doc.width
    # Folgeseiten nutzen die Inhaltsvorlage, auch wenn das Deckblatt ueberlaeuft
    story = [NextPageTemplate("inhalt")] + deckblatt(daten, stil, S, modus, breite)
    story += [PageBreak()]
    story += aufgaben_flowables(daten, stil, S, modus, breite, basis)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("— Ende der %s —" % ("Klausur" if modus == "aufgaben"
                                                else "Musterlösung"), S["schluss"]))

    class _C(ZaehlCanvas):
        pass
    _C.ctx = {"stil": stil, "werte": werte, "ki_fuss": meta.get("ki_hinweis_fuss")}
    doc.build(story, canvasmaker=_C)
    return pfad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--out", default="/mnt/user-data/outputs" if os.path.isdir("/mnt/user-data/outputs") else ".")
    ap.add_argument("--praefix", default=None)
    ap.add_argument("--nur", choices=["aufgaben", "loesung"], default=None)
    ap.add_argument("--vorlage", default=None,
                    help="Pfad zu vorlage_*.json oder 'generisch'")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as fh:
        daten = json.load(fh)
    meta = daten.get("meta", {})
    stil, herkunft = lade_vorlage(args.json, meta, args.vorlage)
    basis = os.path.dirname(os.path.abspath(args.json))
    os.makedirs(args.out, exist_ok=True)
    praefix = args.praefix or re.sub(
        r"[^A-Za-z0-9_-]+", "_",
        "%s_%s" % (meta.get("modulkuerzel") or meta.get("modul", "Klausur"),
                   meta.get("variante", ""))).strip("_")
    print("Vorlage: %s" % herkunft)
    for modus, suffix in (("aufgaben", "Aufgabenblatt"), ("loesung", "Loesungen")):
        if args.nur and args.nur != modus:
            continue
        p = os.path.join(args.out, "%s_%s.pdf" % (praefix, suffix))
        baue(daten, p, modus, stil, basis)
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
