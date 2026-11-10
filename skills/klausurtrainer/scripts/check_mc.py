#!/usr/bin/env python3
"""
check_mc.py - Prueft die Multiple-Choice-Teilaufgaben einer klausur.json mit
denselben Regeln wie der Skill mc-fragen: Zahl der Optionen und richtigen
Antworten, Uebereinstimmung mit der Ziehung, Positionsverteilung, Laengen- und
Detailbias, Absolutwoerter, Weichmacher, Wortanklang, Begruendungen, Quellen.

Aufruf:
    python3 check_mc.py klausur.json
    python3 check_mc.py klausur.json --positionen positionen.json

Die Ziehung wird der Reihe nach zugeordnet: erste MC-Teilaufgabe der Klausur
= F1 der Ziehung, zweite = F2 usw.
"""

import argparse
import json
import re
import sys
from collections import Counter

BUCHSTABEN = "ABCDEFGH"

ABSOLUT = ["immer", "nie", "niemals", "ausschließlich", "ausschliesslich",
           "stets", "grundsätzlich", "grundsaetzlich", "in jedem fall",
           "keinesfalls", "alle", "keine", "jeder", "jede", "nur"]
WEICH = ["in der regel", "meist", "häufig", "haeufig", "kann", "typischerweise",
         "üblicherweise", "ueblicherweise", "tendenziell", "oft"]
SAMMEL = ["alle der genannten", "keine der genannten", "alle genannten",
          "a und b", "sowohl", "keine der obigen", "alle oben"]


def woerter(text):
    return set(w for w in re.findall(r"[A-Za-zÄÖÜäöüß]{5,}", text.lower()))


def zahlen(text):
    return len(re.findall(r"\d", text))


def enthaelt(text, liste):
    t = " " + text.lower() + " "
    return sum(1 for w in liste if w in t)


def pruefe(daten, ziehung=None):
    fehler, warnung, info = [], [], []
    meta = daten.get("meta") or {}
    fragen = daten.get("fragen") or []
    if not fragen:
        return ["keine Fragen enthalten"], [], []

    k_soll = meta.get("optionen")
    r_soll = meta.get("richtige")

    pos_zaehler = Counter()
    laenge_richtig, laenge_falsch = [], []
    richtig_laengste = richtig_kuerzeste = 0
    zahl_nur_richtig = 0
    absolut_falsch = absolut_richtig = 0
    weich_richtig = weich_falsch = 0
    anklang = []

    ids = [f.get("id") for f in fragen]
    for i, n in Counter(ids).items():
        if n > 1:
            fehler.append("Frage-ID '%s' kommt %dx vor" % (i, n))

    for idx, f in enumerate(fragen, 1):
        fid = f.get("id") or "F%d" % idx
        opts = f.get("optionen") or []
        if len(opts) < 2:
            fehler.append("%s: weniger als zwei Optionen" % fid)
            continue
        if k_soll and len(opts) != k_soll:
            fehler.append("%s: %d Optionen, vorgegeben sind %d"
                          % (fid, len(opts), k_soll))
        if not (f.get("frage") or "").strip():
            fehler.append("%s: kein Fragetext" % fid)
        if not (f.get("quelle") or "").strip():
            fehler.append("%s: keine Quellenangabe" % fid)
        if not (f.get("erklaerung") or "").strip():
            fehler.append("%s: keine Begründung der richtigen Antwort" % fid)

        richtige = [j for j, o in enumerate(opts) if o.get("richtig")]
        if not richtige:
            fehler.append("%s: keine Option als richtig markiert" % fid)
            continue
        if r_soll and len(richtige) != r_soll:
            fehler.append("%s: %d richtige Antworten, vorgegeben sind %d"
                          % (fid, len(richtige), r_soll))
        for j in richtige:
            pos_zaehler[BUCHSTABEN[j]] += 1

        texte = [(o.get("text") or "").strip() for o in opts]
        for j, t in enumerate(texte):
            if not t:
                fehler.append("%s: Option %s ohne Text" % (fid, BUCHSTABEN[j]))
        for j, o in enumerate(opts):
            if not o.get("richtig") and not (o.get("warum_falsch") or "").strip():
                warnung.append("%s: Option %s ohne Begründung, warum sie falsch ist"
                               % (fid, BUCHSTABEN[j]))

        # doppelte oder fast gleiche Optionen
        norm = [re.sub(r"\W+", "", t.lower()) for t in texte]
        for a in range(len(norm)):
            for b in range(a + 1, len(norm)):
                if norm[a] and norm[a] == norm[b]:
                    fehler.append("%s: Optionen %s und %s sind identisch"
                                  % (fid, BUCHSTABEN[a], BUCHSTABEN[b]))
        for j, t in enumerate(texte):
            if enthaelt(t, SAMMEL):
                warnung.append("%s: Option %s ist eine Sammeloption "
                               "(\"alle/keine der genannten\") - vermeiden"
                               % (fid, BUCHSTABEN[j]))

        # Laenge
        lr = [len(texte[j]) for j in richtige]
        lf = [len(texte[j]) for j in range(len(texte)) if j not in richtige]
        laenge_richtig += lr
        laenge_falsch += lf
        if lf:
            if max(lr) > max(lf):
                richtig_laengste += 1
            if min(lr) < min(lf):
                richtig_kuerzeste += 1
            spanne = max(max(lr), max(lf)) / float(max(1, min(min(lr), min(lf))))
            if spanne > 2.2:
                warnung.append("%s: Optionen unterschiedlich lang (Faktor %.1f)"
                               % (fid, spanne))

        # Detailgrad
        zr = sum(zahlen(texte[j]) for j in richtige)
        zf = sum(zahlen(texte[j]) for j in range(len(texte)) if j not in richtige)
        if zr and not zf:
            zahl_nur_richtig += 1

        # Sprachmuster
        for j, t in enumerate(texte):
            if j in richtige:
                absolut_richtig += enthaelt(t, ABSOLUT)
                weich_richtig += enthaelt(t, WEICH)
            else:
                absolut_falsch += enthaelt(t, ABSOLUT)
                weich_falsch += enthaelt(t, WEICH)

        # Wortanklang: Begriff aus dem Stamm taucht nur in der richtigen Antwort auf
        stamm = woerter(f.get("frage", ""))
        nur_richtig = set()
        for j in richtige:
            nur_richtig |= (woerter(texte[j]) & stamm)
        for j in range(len(texte)):
            if j not in richtige:
                nur_richtig -= woerter(texte[j])
        if nur_richtig:
            anklang.append("%s (%s)" % (fid, ", ".join(sorted(nur_richtig)[:3])))

    n = len(fragen)

    # Abgleich mit der Ziehung
    if ziehung:
        zu = {e["id"]: set(e["richtige_buchstaben"]) for e in ziehung["zuordnung"]}
        for idx, f in enumerate(fragen, 1):
            fid = f.get("id") or "F%d" % idx
            soll = zu.get(fid)
            if soll is None:
                continue
            ist = set(BUCHSTABEN[j] for j, o in enumerate(f.get("optionen") or [])
                      if o.get("richtig"))
            if ist != soll:
                fehler.append("%s: richtige Antwort steht auf %s, ausgelost war %s"
                              % (fid, ",".join(sorted(ist)) or "-",
                                 ",".join(sorted(soll))))

    # Positionsverteilung
    k = k_soll or max((len(f.get("optionen") or []) for f in fragen), default=4)
    r = r_soll or 1
    erwartet = n * r / float(k)
    verteilung = "  ".join("%s=%d" % (b, pos_zaehler.get(b, 0))
                           for b in BUCHSTABEN[:k])
    info.append("Positionen: %s  (erwartet je %.1f)" % (verteilung, erwartet))
    if n >= 8 and erwartet > 0:
        for b in BUCHSTABEN[:k]:
            anteil = pos_zaehler.get(b, 0) / erwartet
            if anteil > 1.8:
                warnung.append("Position %s ist deutlich überrepräsentiert "
                               "(%d statt ~%.1f)" % (b, pos_zaehler[b], erwartet))
            if anteil < 0.25:
                warnung.append("Position %s kommt fast nie vor (%d statt ~%.1f)"
                               % (b, pos_zaehler.get(b, 0), erwartet))

    # Laengenbias
    if laenge_richtig and laenge_falsch:
        mr = sum(laenge_richtig) / float(len(laenge_richtig))
        mf = sum(laenge_falsch) / float(len(laenge_falsch))
        info.append("Mittlere Länge: richtig %.0f Zeichen, Distraktoren %.0f "
                    "(Verhältnis %.2f)" % (mr, mf, mr / mf if mf else 0))
        if mf and not 0.85 <= mr / mf <= 1.15:
            warnung.append("Längenbias: richtige Antworten sind im Mittel %s "
                           "als die Distraktoren. Distraktoren angleichen."
                           % ("länger" if mr > mf else "kürzer"))
        quote_lang = richtig_laengste / float(n)
        if n >= 8 and quote_lang > max(0.45, 1.8 / k):
            warnung.append("In %d von %d Fragen ist die richtige Antwort die "
                           "längste Option." % (richtig_laengste, n))
        quote_kurz = richtig_kuerzeste / float(n)
        if n >= 8 and quote_kurz > max(0.45, 1.8 / k):
            warnung.append("In %d von %d Fragen ist die richtige Antwort die "
                           "kürzeste Option." % (richtig_kuerzeste, n))

    if n >= 6 and zahl_nur_richtig / float(n) > 0.4:
        warnung.append("In %d von %d Fragen stehen Zahlenangaben nur in der "
                       "richtigen Antwort." % (zahl_nur_richtig, n))
    if absolut_falsch >= 3 and absolut_richtig == 0:
        warnung.append("Absolutwörter (immer, nie, nur) kommen %dx vor, "
                       "ausschließlich in Distraktoren - klassischer Verräter."
                       % absolut_falsch)
    if weich_richtig >= 3 and weich_falsch == 0:
        warnung.append("Weichmacher (in der Regel, meist, kann) kommen %dx vor, "
                       "ausschließlich in richtigen Antworten." % weich_richtig)
    if anklang:
        warnung.append("Wortanklang zum Fragestamm nur in der richtigen "
                       "Antwort: %s" % "; ".join(anklang[:6]))

    return fehler, warnung, info



def mc_aus_klausur(daten):
    meta = daten.get("meta") or {}
    fragen = []
    for a in daten.get("aufgaben") or []:
        tas = a.get("teilaufgaben") or [a]
        for ta in tas:
            if not ta.get("optionen"):
                continue
            fragen.append({
                "id": "F%d" % (len(fragen) + 1),
                "ort": "%s%s" % (a.get("id", "?"), ta.get("nr", "")),
                "frage": ta.get("text", ""),
                "optionen": ta["optionen"],
                "erklaerung": ta.get("erklaerung") or ta.get("erlaeuterung") or ta.get("loesung", ""),
                "quelle": ta.get("quelle") or a.get("quelle", ""),
            })
    k = meta.get("mc_optionen") or (Counter(len(f["optionen"]) for f in fragen).most_common(1)[0][0]
                                    if fragen else 4)
    r = meta.get("mc_richtige") or (Counter(sum(1 for o in f["optionen"] if o.get("richtig"))
                                            for f in fragen).most_common(1)[0][0] if fragen else 1)
    return {"meta": {"optionen": k, "richtige": r}, "fragen": fragen}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--positionen", default=None)
    args = ap.parse_args()
    with open(args.json, encoding="utf-8") as fh:
        daten = mc_aus_klausur(json.load(fh))
    if not daten["fragen"]:
        print("Keine MC-Teilaufgaben in der Klausur.")
        return 0
    ziehung = None
    if args.positionen:
        with open(args.positionen, encoding="utf-8") as fh:
            ziehung = json.load(fh)
    fehler, warnung, info = pruefe(daten, ziehung)
    orte = {f["id"]: f["ort"] for f in daten["fragen"]}
    def ort(t):
        return re.sub(r"\bF(\d+)\b", lambda m: orte.get("F" + m.group(1), m.group(0)), t)
    print("MC-Teilaufgaben: %d  (%s)\n" % (len(daten["fragen"]),
                                          ", ".join(f["ort"] for f in daten["fragen"])))
    for z in info:
        print("  " + z)
    print()
    for w in warnung:
        print("WARNUNG: %s" % ort(w))
    for f in fehler:
        print("FEHLER : %s" % ort(f))
    print("\nOK - keine Auffälligkeiten." if not fehler and not warnung else
          ("\n%d Fehler." % len(fehler) if fehler else
           "\n%d Warnung(en). Texte überarbeiten, Positionen unverändert lassen." % len(warnung)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
