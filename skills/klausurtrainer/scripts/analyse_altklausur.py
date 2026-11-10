#!/usr/bin/env python3
"""
analyse_altklausur.py - Leitet aus einer echten Altklausur (PDF) ein
Vorlagenprofil ab, mit dem render_exam.py deren Erscheinungsbild nachbildet.

Aufruf:
    python3 analyse_altklausur.py Altklausur_WS23.pdf --modul GPUM --out vorlage_GPUM.json
    python3 analyse_altklausur.py Altklausur_WS23.pdf --modul GPUM --out vorlage_GPUM.json --vorschau vorschau/

Erkannt werden: Schriftart und -groessen (auf verfuegbare Schriften abgebildet),
Farben, Seitenraender, Kopf- und Fusszeilen, das Muster der
Aufgabenueberschriften und Teilaufgaben, Punktekaesten, Seitenumbruch je
Aufgabe, Aufbau und Ausrichtung des Deckblatts, Personalienfelder,
Punktetabelle, Art des Antwortraums.

Nie uebernommen werden: Logos, Siegel und andere Bilder, sowie woertliche
Inhalte der alten Aufgaben. Das Wort "Klausur" in Kopf- und Titelzeilen wird zu
"Probeklausur", damit das Ergebnis nicht mit einer echten Pruefung verwechselt
werden kann.

Das Profil ist ein Vorschlag. Mit --vorschau werden Deckblatt und erste
Aufgabenseite der Altklausur als Bild abgelegt, damit das Profil gegen das
Original gehalten und von Hand nachgeschaerft werden kann.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

PT_MM = 25.4 / 72.0

SCHRIFT_MUSTER = [
    ("freeserif", r"times|nimbusrom|tinos|liberationserif|termes|freeserif"),
    ("freesans", r"arial|helvetica|nimbussans|liberationsans|arimo|freesans|heros"),
    ("carlito", r"calibri|carlito|frutiger|myriad|segoe|verdana|tahoma|opensans|"
                r"roboto|lato|sourcesans|univers|stafford|dejavusans|sans"),
    ("caladea", r"cambria|caladea|charter|georgia|palatino|garamond|minion|utopia|"
                r"cmr|lmroman|latinmodern|computermodern|serif|roman|book"),
]

AUFGABE_RE = re.compile(r"^\s*(Aufgabe|Aufg\.|Task|Frage|Teilaufgabe|Problem)\s*"
                        r"(\d+)\s*(.*)$", re.I)
PUNKTE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(Punkte|Punkten|Pkt\.?|P\.|P\b|Points|pts\.?)",
                       re.I)
TEIL_RE = re.compile(r"^\s*(\(([a-hA-H])\)|([a-hA-H])\)|([a-hA-H])\.)\s+\S")
SEMESTER_RE = re.compile(r"\b(WS|SS|WiSe|SoSe|Wintersemester|Sommersemester)\s*"
                         r"\d{2,4}(\s*/\s*\d{2,4})?", re.I)
DATUM_RE = re.compile(r"\b\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}\b")
PERSONALIEN_RE = re.compile(r"^(Name|Vorname|Nachname|Matrikel|Matr\.|Studiengang|"
                            r"Unterschrift|Platz|Sitzplatz|E-?Mail|Raum)", re.I)


def schrift_familie(fontname):
    n = re.sub(r"^[A-Z]{6}\+", "", fontname or "").lower().replace("-", "").replace(" ", "")
    for fam, muster in SCHRIFT_MUSTER:
        if re.search(muster, n):
            return fam
    return "caladea"


def ist_fett(fontname):
    return bool(re.search(r"bold|black|heavy|semibold|demi|,b\b|-b\b|bd",
                          (fontname or "").lower()))


def farbe_hex(c):
    if c is None:
        return None
    if isinstance(c, (int, float)):
        c = (c,)
    c = [float(x) for x in c]
    if len(c) == 1:
        r = g = b = c[0]
    elif len(c) == 3:
        r, g, b = c
    elif len(c) == 4:
        k = c[3]
        r, g, b = [(1 - x) * (1 - k) for x in c[:3]]
    else:
        return None
    return "#%02X%02X%02X" % tuple(int(round(max(0, min(1, x)) * 255)) for x in (r, g, b))


def ist_bunt(hx):
    if not hx:
        return False
    r, g, b = int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
    return max(r, g, b) - min(r, g, b) > 40


def perzentil(werte, p):
    if not werte:
        return None
    s = sorted(werte)
    return s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))]


def segmente(zeile, luecke=18):
    """Teilt eine Textzeile an grossen horizontalen Luecken (links/mitte/rechts)."""
    zs = [c for c in zeile.get("chars", []) if c["text"] != ""]
    if not zs:
        return [(zeile["text"], zeile["x0"], zeile["x1"])]
    aus, akt = [], [zs[0]]
    for a, b in zip(zs, zs[1:]):
        if b["x0"] - a["x1"] > luecke:
            aus.append(akt)
            akt = [b]
        else:
            akt.append(b)
    aus.append(akt)
    def text(seg):
        t = seg[0]["text"]
        for a, b in zip(seg, seg[1:]):
            if b["x0"] - a["x1"] > a.get("size", 10) * 0.18 and a["text"] != " " \
                    and b["text"] != " ":
                t += " "
            t += b["text"]
        return re.sub(r"\s+", " ", t).strip()
    return [(text(seg), seg[0]["x0"], seg[-1]["x1"]) for seg in aus if text(seg)]


def entschaerfen(text):
    """Keine Verwechslung mit einer echten Pruefung, keine alten Daten."""
    t = SEMESTER_RE.sub("{semester}", text)
    t = DATUM_RE.sub("{pruefungsdatum}", t)
    t = re.sub(r"\b(?<!Probe)(Klausur|Prüfung|Pruefung|Exam)\b", "Probeklausur", t)
    return t.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--modul", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--vorschau", default=None)
    args = ap.parse_args()

    import pdfplumber
    pdf = pdfplumber.open(args.pdf)
    seiten = pdf.pages
    breite_pt, hoehe_pt = seiten[0].width, seiten[0].height
    befunde = []

    # ------------------------------------------------------------ Schriften
    zeichen_zaehler = Counter()
    farben = Counter()
    groessen_s1 = []
    for s in seiten:
        for ch in s.chars:
            if not ch["text"].strip():
                continue
            zeichen_zaehler[(ch["fontname"], round(ch["size"], 1))] += 1
            hx = farbe_hex(ch.get("non_stroking_color"))
            if hx:
                farben[hx] += 1
    for ch in seiten[0].chars:
        if ch["text"].strip():
            groessen_s1.append(ch["size"])
    (text_font, text_groesse), _ = zeichen_zaehler.most_common(1)[0]
    text_fam = schrift_familie(text_font)
    befunde.append("Fließtext: %s %.1f pt -> %s" % (text_font, text_groesse, text_fam))

    # ------------------------------------------------------------ Aufgaben
    aufgaben_zeilen, teil_zeilen = [], []
    zeilen_je_seite = []
    for i, s in enumerate(seiten):
        try:
            zeilen = s.extract_text_lines()
        except Exception:
            zeilen = []
        zeilen_je_seite.append(zeilen)
        for z in zeilen:
            m = AUFGABE_RE.match(z["text"])
            if m and not re.fullmatch(r"[\d\sΣ|.,]*", m.group(3) or ""):
                zs = [c for c in z["chars"] if c["text"].strip()]
                hervor = zs and (ist_fett(zs[0]["fontname"]) or
                                 zs[0]["size"] > text_groesse * 1.05)
                if hervor:
                    aufgaben_zeilen.append((i, z))
                    continue
            if TEIL_RE.match(z["text"]):
                teil_zeilen.append((i, z))

    titel_fam, titel_groesse, aufg_titel, aufg_ohne = text_fam, text_groesse * 1.2, None, None
    punkte_im_titel = False
    if aufgaben_zeilen:
        _, z0 = aufgaben_zeilen[0]
        ch0 = next((c for c in z0["chars"] if c["text"].strip()), None)
        if ch0:
            titel_fam = schrift_familie(ch0["fontname"])
            titel_groesse = ch0["size"]
        muster = Counter()
        for _, z in aufgaben_zeilen:
            m = AUFGABE_RE.match(z["text"])
            wort, rest = m.group(1), m.group(3)
            pm = PUNKTE_RE.search(rest)
            punkte_teil = ""
            if pm:
                vor = rest[:pm.start()].rstrip()
                nach = rest[pm.end():]
                klammer_auf = vor[-1] if vor.endswith(("(", "[")) else ""
                klammer_zu = nach[:1] if nach[:1] in (")", "]") else ""
                punkte_teil = " %s{punkte} %s%s" % (klammer_auf, pm.group(2), klammer_zu)
                titelteil = vor.rstrip("([ ").strip(" :.–-")
            else:
                titelteil = rest.strip(" :.–-")
            trenner = ":" if re.match(r"^\s*:", rest) else (
                " –" if re.match(r"^\s*[–-]", rest) else (
                    "." if re.match(r"^\s*\.", rest) else ""))
            if titelteil:
                muster[("%s {nr}%s {titel}%s" % (wort, trenner, punkte_teil)).strip()] += 1
            else:
                muster[("%s {nr}%s" % (wort, punkte_teil)).strip()] += 1
        haeufig = [m for m, _ in muster.most_common()]
        mit = next((m for m in haeufig if "{titel}" in m), None)
        ohne = next((m for m in haeufig if "{titel}" not in m), None)
        aufg_titel = mit or (ohne.replace("{nr}", "{nr}: {titel}", 1) if ohne else None)
        aufg_ohne = ohne or (re.sub(r"[:.–]?\s*\{titel\}", "", mit) if mit else None)
        punkte_im_titel = "{punkte}" in (aufg_titel or "")
        befunde.append("Aufgabenüberschrift: %s" % (aufg_titel or aufg_ohne))
    else:
        befunde.append("Keine Aufgabenüberschriften erkannt - Muster manuell setzen")

    teil_format, teilpunkte = "{nr})", "{punkte} P."
    if teil_zeilen:
        formen = Counter()
        pformen = Counter()
        for _, z in teil_zeilen:
            m = TEIL_RE.match(z["text"])
            if m.group(2):
                formen["({nr})"] += 1
            elif m.group(3):
                formen["{nr})"] += 1
            else:
                formen["{nr}."] += 1
            pm = PUNKTE_RE.search(z["text"])
            if pm:
                vor = z["text"][:pm.start()].rstrip()
                nach = z["text"][pm.end():]
                a = vor[-1] if vor.endswith(("(", "[")) else ""
                zu = nach[:1] if nach[:1] in (")", "]") else ""
                pformen["%s{punkte} %s%s" % (a, pm.group(2), zu)] += 1
        teil_format = formen.most_common(1)[0][0]
        if pformen:
            teilpunkte = pformen.most_common(1)[0][0]
        befunde.append("Teilaufgaben: %s, Punkte %s" % (teil_format, teilpunkte))

    # Punktekasten: kleines Rechteck auf Hoehe der Aufgabenueberschrift
    kasten = False
    for i, z in aufgaben_zeilen:
        for r in seiten[i].rects:
            w, h = r["x1"] - r["x0"], r["bottom"] - r["top"]
            if 10 < w < 120 and 8 < h < 45 and abs(r["top"] - z["top"]) < 30 \
                    and r["x0"] > breite_pt * 0.6:
                kasten = True
                break
    befunde.append("Punktekasten: %s" % ("ja" if kasten else "nein"))

    neue_seite = False
    if len(aufgaben_zeilen) >= 2:
        oben = sum(1 for i, z in aufgaben_zeilen if z["top"] < hoehe_pt * 0.25)
        seiten_mit = len(set(i for i, _ in aufgaben_zeilen))
        neue_seite = oben >= 0.7 * len(aufgaben_zeilen) and seiten_mit >= len(aufgaben_zeilen)
    befunde.append("Neue Seite je Aufgabe: %s" % ("ja" if neue_seite else "nein"))

    # ------------------------------------------------------------ Raender
    x0s, x1s = [], []
    for s in seiten[1:] or seiten:
        for ch in s.chars:
            if ch["text"].strip():
                x0s.append(ch["x0"])
                x1s.append(ch["x1"])
    links = (perzentil(x0s, 0.02) or 60) * PT_MM
    rechts = (breite_pt - (perzentil(x1s, 0.98) or breite_pt - 60)) * PT_MM
    rand = [round(max(12, min(35, links))), round(max(12, min(35, rechts))), 25, 22]

    # ------------------------------------------------------------ Kopf/Fuss
    def wiederkehrend(bereich):
        kand = Counter()
        pos = {}
        for i, zeilen in enumerate(zeilen_je_seite):
            for z in zeilen:
                oben = z["top"] < hoehe_pt * 0.1
                unten = z["top"] > hoehe_pt * 0.9
                if not ((bereich == "kopf" and oben) or (bereich == "fuss" and unten)):
                    continue
                for text, x0, x1 in segmente(z):
                    schluessel = re.sub(r"\d+", "#", text)
                    kand[schluessel] += 1
                    pos.setdefault(schluessel, ({"text": text, "x0": x0, "x1": x1}, i))
        n = len(zeilen_je_seite)
        return [(k, pos[k]) for k, c in kand.items() if c >= max(2, 0.5 * n)]

    def vorlage_aus(zeile, seitenindex):
        t = zeile["text"].strip()
        t = re.sub(r"Seite\s+\d+\s+(von|/)\s+\d+", r"Seite {seite} \1 {seiten}", t)
        t = re.sub(r"^\s*\d+\s*/\s*\d+\s*$", "{seite} / {seiten}", t)
        t = re.sub(r"^\s*-?\s*\d+\s*-?\s*$", "{seite}", t)
        if "{seite}" not in t and str(seitenindex + 1) in t.split():
            t = t.replace(str(seitenindex + 1), "{seite}", 1)
        return entschaerfen(t)

    kopf = {"links": "", "rechts": ""}
    fuss = {"links": "", "rechts": ""}
    for bereich, ziel in (("kopf", kopf), ("fuss", fuss)):
        for _, (z, i) in wiederkehrend(bereich):
            v = vorlage_aus(z, i)
            mitte = (z["x0"] + z["x1"]) / 2.0
            seite = "rechts" if mitte > breite_pt * 0.6 else "links"
            ziel[seite] = (ziel[seite] + "  " + v).strip() if ziel[seite] else v
    if not any("{seite}" in v for v in fuss.values()) and \
            not any("{seite}" in v for v in kopf.values()):
        fuss["rechts"] = "Seite {seite} von {seiten}"
    if not kopf["links"] and not kopf["rechts"]:
        kopf = {"links": "{modul}", "rechts": "{variante}"}
    befunde.append("Kopfzeile: %s | %s" % (kopf["links"], kopf["rechts"]))
    befunde.append("Fußzeile: %s | %s" % (fuss["links"], fuss["rechts"]))

    # ------------------------------------------------------------ Deckblatt
    s1 = zeilen_je_seite[0] if zeilen_je_seite else []
    hat_deckblatt = not any(i == 0 for i, _ in aufgaben_zeilen)
    zentriert = False
    titelzeilen, personalien, hinweise_stil = [], [], "nummeriert"
    tabelle = "keine"
    tab_max, tab_erreicht = "max.", "erreicht"
    if hat_deckblatt and s1:
        mitte = breite_pt / 2.0
        grosse = [z for z in s1 if z["chars"] and z["top"] < hoehe_pt * 0.4 and
                  max(c["size"] for c in z["chars"]) >= text_groesse * 1.05]
        bezug = grosse or s1
        zent = sum(1 for z in bezug if abs((z["x0"] + z["x1"]) / 2.0 - mitte) < 18
                   and (z["x1"] - z["x0"]) < breite_pt * 0.8)
        zentriert = zent >= 0.6 * len(bezug)
        for z in grosse[:5]:
            t = entschaerfen(z["text"])
            if t and not PERSONALIEN_RE.match(t):
                titelzeilen.append(t)
        for z in s1:
            t = z["text"].strip()
            if PERSONALIEN_RE.match(t):
                lab = re.split(r"[:_.]{2,}|:\s*$|:\s", t)[0].strip(" :_")
                if lab and lab not in personalien and len(lab) < 40:
                    personalien.append(lab)
        if sum(1 for z in s1 if re.match(r"^\s*[•\-–]\s", z["text"])) > \
                sum(1 for z in s1 if re.match(r"^\s*\d+[.)]\s", z["text"])):
            hinweise_stil = "punkte"
        try:
            for t in seiten[0].find_tables():
                zeilen = t.extract()
                if not zeilen:
                    continue
                erste = " ".join((c or "") for c in zeilen[0]).lower()
                spalte = " ".join((r[0] or "") for r in zeilen).lower()
                if "aufgabe" in erste and sum(1 for c in zeilen[0]
                                              if (c or "").strip().isdigit()) >= 2:
                    tabelle = "horizontal"
                    if len(zeilen) > 1 and (zeilen[1][0] or "").strip():
                        tab_max = zeilen[1][0].strip()
                    if len(zeilen) > 2 and (zeilen[2][0] or "").strip():
                        tab_erreicht = zeilen[2][0].strip()
                elif "aufgabe" in erste or "aufgabe" in spalte or \
                        sum(1 for r in zeilen if (r[0] or "").strip().isdigit()) >= 2:
                    tabelle = "vertikal"
        except Exception:
            pass
    # Modulname: grosse Deckblattzeile, die weder "Klausur" noch Semester/Datum ist
    modulname = None
    for t in titelzeilen:
        rein = re.sub(r"\{[a-z]+\}", "", t).strip(" –-")
        if rein and not re.fullmatch(r"(Probe)?klausur", rein, re.I) and len(rein) > 6:
            modulname = rein
            break
    if modulname:
        titelzeilen = [t.replace(modulname, "{modul}") for t in titelzeilen]
        for ziel in (kopf, fuss):
            for k in ziel:
                ziel[k] = ziel[k].replace(modulname, "{modul}")
        befunde.append("Modulname im Original: \"%s\" -> {modul}" % modulname)
        befunde[:] = [b if not b.startswith("Kopfzeile") else
                      "Kopfzeile: %s | %s" % (kopf["links"], kopf["rechts"]) for b in befunde]
    befunde.append("Deckblatt: %s, %s, Punktetabelle %s, Personalien: %s"
                   % ("ja" if hat_deckblatt else "nein",
                      "zentriert" if zentriert else "linksbündig", tabelle,
                      ", ".join(personalien) or "-"))

    # ------------------------------------------------------------ Feinheiten
    # Schrift der Kopfzeile, kraeftige Kopflinie, Teilpunkte im Text
    kopf_font, kopf_groesse = None, None
    for zeilen in zeilen_je_seite[1:]:
        for z in zeilen:
            if z["top"] < hoehe_pt * 0.1 and z["chars"]:
                kopf_font = schrift_familie(z["chars"][0]["fontname"])
                kopf_groesse = round(z["chars"][0]["size"], 1)
                break
        if kopf_font:
            break
    kopflinie = "keine"
    for s_ in seiten[1:2]:
        for l in list(s_.lines) + [r for r in s_.rects if r["bottom"] - r["top"] < 2]:
            if l["top"] < hoehe_pt * 0.12 and (l["x1"] - l["x0"]) > breite_pt * 0.5:
                lw = l.get("linewidth") or 1.0    # 0 = PDF-Standardbreite 1
                kopflinie = "kraeftig" if lw >= 0.6 else "haar"
    teil_inline = False
    if teil_zeilen:
        teil_inline = sum(1 for _, z in teil_zeilen if PUNKTE_RE.search(z["text"])
                          and z["x1"] < breite_pt * 0.85) >= 0.5 * len(teil_zeilen)
    hinweise_titel, hinweise_zent = "Hinweise", False
    for z in s1:
        if re.match(r"^\s*(Hinweise|Bearbeitungshinweise|Allgemeine Hinweise)\b",
                    z["text"], re.I):
            hinweise_titel = z["text"].strip().rstrip(":")
            hinweise_zent = abs((z["x0"] + z["x1"]) / 2.0 - breite_pt / 2.0) < 18
            break
    # Eine Titelzeile, die nur "Klausur" war, traegt kuenftig die Variante
    titelzeilen = ["{variante}" if re.fullmatch(r"(Probe)?klausur", t, re.I) else t
                   for t in titelzeilen]

    # ------------------------------------------------------------ Antwortraum
    lange_linien, grosse_kaesten = 0, 0
    for s in seiten[1:]:
        for l in s.lines:
            if abs(l["top"] - l["bottom"]) < 1 and (l["x1"] - l["x0"]) > breite_pt * 0.55:
                lange_linien += 1
        for r in s.rects:
            if (r["x1"] - r["x0"]) > breite_pt * 0.55 and (r["bottom"] - r["top"]) > 80:
                grosse_kaesten += 1
    if lange_linien > 10:
        antwort = "linien"
    elif grosse_kaesten >= 2:
        antwort = "kasten"
    else:
        antwort = "platz"
    befunde.append("Antwortraum: %s" % antwort)
    befunde.append("Kopflinie: %s, Kopfzeilenschrift: %s, Teilpunkte: %s"
                   % (kopflinie, kopf_font or "-", "im Text" if teil_inline else "am Rand"))

    # ------------------------------------------------------------ Farben
    bunt = [(h, n) for h, n in farben.most_common() if ist_bunt(h)]
    akzent = bunt[0][0] if bunt else "#111111"
    tinte = "#000000" if not bunt or farben.most_common(1)[0][0] in ("#000000",) \
        else farben.most_common(1)[0][0]

    profil = {
        "name": "altklausur",
        "quelle": os.path.basename(args.pdf),
        "modul": args.modul,
        "rand_mm": rand,
        "schrift_text": text_fam,
        "schrift_titel": titel_fam,
        "schrift_hilfe": kopf_font or (text_fam if text_fam in ("freesans", "carlito")
                                       else "carlito"),
        "groesse_text": round(max(9, min(12.5, text_groesse)), 1),
        "groesse_aufgabe": round(max(10, min(16, titel_groesse)), 1),
        "groesse_titel": round(max(15, min(28, max(groessen_s1 or [20])))),
        "tinte": tinte,
        "akzent": akzent,
        "grau": "#555555",
        "flaeche": "#FFFFFF",
        "groesse_kopf": kopf_groesse or 8,
        "logo": "eigen",
        "kopfzeile": kopf,
        "fusszeile": fuss,
        "aufgabe_titel": aufg_titel or "Aufgabe {nr}: {titel}",
        "aufgabe_titel_ohne": aufg_ohne or "Aufgabe {nr}",
        "aufgabe_punkte": "" if punkte_im_titel else "{punkte} Punkte",
        "aufgabe_linie": False,
        "punktekasten": kasten,
        "teilaufgabe_format": teil_format,
        "teilpunkte_format": teilpunkte,
        "neue_seite_je_aufgabe": neue_seite,
        "antwortraum_stil": antwort,
        "symbole": False,
        "kopflinie": kopflinie,
        "teilpunkte_position": "inline" if teil_inline else "rechts",
        "logo_mm": 14,
        "deckblatt": {
            "ausrichtung": "zentriert" if zentriert else "links",
            "titelzeilen": titelzeilen,
            "personalien": personalien or ["Name, Vorname", "Matrikelnummer"],
            "personalien_stil": "zeile",
            "punktetabelle": tabelle,
            "punktetabelle_titel": "",
            "punktetabelle_zeilen": [tab_max, tab_erreicht],
            "hinweise_stil": hinweise_stil,
            "hinweise_titel": hinweise_titel,
            "hinweise_ausrichtung": "zentriert" if hinweise_zent else "links",
            "eckdaten": False,
            "linie": False,
            "institution": False,
            "variante_zeile": False,
        },
        "_befunde": befunde,
    }

    out = args.out or "vorlage_%s.json" % args.modul
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(profil, fh, ensure_ascii=False, indent=1)

    print("Vorlagenprofil aus %s\n" % os.path.basename(args.pdf))
    for b in befunde:
        print("  " + b)
    print("\nGeschrieben: %s" % out)

    if args.vorschau:
        try:
            import pypdfium2 as pdfium
            os.makedirs(args.vorschau, exist_ok=True)
            doc = pdfium.PdfDocument(args.pdf)
            ziele = [0]
            if aufgaben_zeilen:
                ziele.append(aufgaben_zeilen[0][0])
            for n in sorted(set(ziele)):
                p = os.path.join(args.vorschau, "original_S%d.png" % (n + 1))
                doc[n].render(scale=1.4).to_pil().save(p)
                print("Vorschau: %s" % p)
        except Exception as e:
            print("Vorschau nicht möglich: %s" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
