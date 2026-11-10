#!/usr/bin/env python3
"""
validate_exam.py - Prueft klausur.json deterministisch, bevor gerendert wird.
Kostet keine Modell-Token und faengt genau die Fehler, die man sonst erst
im fertigen PDF sieht.

Aufruf:
    python3 validate_exam.py klausur.json
    python3 validate_exam.py klausur.json --blueprint blueprint.json

Exitcode 0 = keine Fehler (Warnungen moeglich), 1 = Fehler gefunden.
"""

import argparse
import json
import re
import sys
from collections import Counter

PFLICHT_META = ["modul", "variante", "gesamtpunkte"]


def tas(a):
    return a.get("teilaufgaben") or [a]


def punkte(x):
    try:
        return float(x.get("punkte", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def pruefe(daten, blueprint=None):
    fehler, warnung = [], []
    meta = daten.get("meta") or {}
    aufgaben = daten.get("aufgaben") or []

    for k in PFLICHT_META:
        if not meta.get(k):
            fehler.append("meta.%s fehlt" % k)
    if not aufgaben:
        fehler.append("keine Aufgaben enthalten")
        return fehler, warnung, {}

    # IDs eindeutig
    ids = [a.get("id") for a in aufgaben]
    for i, n in Counter(ids).items():
        if n > 1:
            fehler.append("Aufgaben-ID '%s' kommt %dx vor" % (i, n))
        if not i:
            fehler.append("Aufgabe ohne id")

    summe = 0.0
    themen = Counter()
    for a in aufgaben:
        aid = a.get("id", "?")
        teil = tas(a)
        tsumme = sum(punkte(t) for t in teil)
        ap = punkte(a) if a.get("punkte") is not None else tsumme
        summe += ap

        if a.get("punkte") is not None and a.get("teilaufgaben") and abs(ap - tsumme) > 1e-6:
            fehler.append("%s: Punkte %g != Summe der Teilaufgaben %g"
                          % (aid, ap, tsumme))
        if ap <= 0:
            fehler.append("%s: Punktzahl ist 0" % aid)
        if not (a.get("titel") or a.get("thema")):
            warnung.append("%s: weder titel noch thema gesetzt" % aid)
        themen[a.get("thema") or a.get("titel") or "ohne Thema"] += ap

        nrs = [t.get("nr") for t in teil if t.get("nr")]
        for n, c in Counter(nrs).items():
            if c > 1:
                fehler.append("%s: Teilaufgabe '%s' kommt %dx vor" % (aid, n, c))

        for t in teil:
            label = "%s%s" % (aid, ")" + str(t.get("nr")) if t.get("nr") else "")
            if not (t.get("text") or "").strip():
                fehler.append("%s: Aufgabentext fehlt" % label)
            # Grounding: jede Teilaufgabe braucht einen Quellanker
            if not (t.get("quelle") or a.get("quelle")):
                fehler.append("%s: kein Quellanker (Grounding-Regel verletzt)" % label)
            tab = t.get("tabelle") or {}
            hat_tabellenloesung = bool(t.get("tabelle_loesung")) or any(
                "[[" in str(c) for z in (tab.get("zeilen") or []) for c in z)
            hat_luecken = "[[" in (t.get("lueckentext") or "") or "[[" in (t.get("text") or "")
            opts = t.get("optionen") or []
            if opts:
                hat_luecken = True     # Loesung steckt in den Optionen
                richtige = [o for o in opts if o.get("richtig")]
                if len(opts) < 2:
                    fehler.append("%s: MC mit weniger als zwei Optionen" % label)
                if not richtige:
                    fehler.append("%s: MC ohne richtige Option" % label)
                if len(richtige) == len(opts):
                    fehler.append("%s: MC, alle Optionen richtig" % label)
                texte = [re.sub(r"\W+", "", (o.get("text") or "").lower()) for o in opts]
                if len(set(texte)) < len(texte):
                    fehler.append("%s: MC mit identischen Optionen" % label)
                for j, o in enumerate(opts):
                    if not o.get("richtig") and not (o.get("warum_falsch") or "").strip():
                        warnung.append("%s: Option %s ohne Begründung, warum sie falsch ist"
                                       % (label, "ABCDEFGH"[j]))
                if not (t.get("erklaerung") or t.get("erlaeuterung") or "").strip():
                    warnung.append("%s: MC ohne Erläuterung der richtigen Antwort" % label)
            if not (t.get("loesung") or "").strip() and not hat_tabellenloesung \
                    and not hat_luecken:
                fehler.append("%s: Musterloesung fehlt" % label)
            if t.get("lueckentext") and "[[" not in t["lueckentext"]:
                fehler.append("%s: Lueckentext ohne Luecken [[...]]" % label)
            if tab and not hat_tabellenloesung and any(
                    not str(c).strip() for z in (tab.get("zeilen") or []) for c in z):
                warnung.append("%s: Tabelle mit leeren Feldern, aber ohne Loesungen "
                               "([[...]] oder tabelle_loesung)" % label)
            krit = t.get("bewertung") or []
            if not krit and t.get("optionen"):
                pass          # MC: Bewertung einheitlich je Aufgabe, siehe meta.mc_bewertung
            elif not krit:
                fehler.append("%s: Bewertungsschema fehlt" % label)
            else:
                ks = sum(punkte(k) for k in krit)
                if abs(ks - punkte(t)) > 1e-6:
                    fehler.append("%s: Bewertungsschema summiert auf %g, "
                                  "Teilaufgabe gibt %g" % (label, ks, punkte(t)))
                for k in krit:
                    if not (k.get("kriterium") or "").strip():
                        fehler.append("%s: Bewertungskriterium ohne Text" % label)
            loes = t.get("loesung") or ""
            if loes.count("==") % 2:
                fehler.append("%s: Textmarker == nicht geschlossen" % label)
            markiert = re.findall(r"==(.+?)==\[(\d+(?:[.,]\d+)?)\]", loes)
            msumme = sum(float(n.replace(",", ".")) for _, n in markiert)
            if markiert and msumme > punkte(t) + 1e-6:
                fehler.append("%s: markierte Teilsätze ergeben %g Punkte, Teilaufgabe "
                              "hat %g" % (label, msumme, punkte(t)))
            if punkte(t) >= 4 and "==" not in loes and not hat_tabellenloesung \
                    and not hat_luecken:
                warnung.append("%s: keine punktegebenden Teilsätze markiert (==...==)"
                               % label)
            if len((t.get("text") or "")) < 15:
                warnung.append("%s: Aufgabentext sehr kurz" % label)
            if punkte(t) >= 6 and len((t.get("loesung") or "")) < 120 \
                    and not hat_tabellenloesung and not hat_luecken:
                warnung.append("%s: %g Punkte, aber sehr knappe Musterloesung"
                               % (label, punkte(t)))

    soll = meta.get("gesamtpunkte")
    if soll is not None and abs(float(soll) - summe) > 1e-6:
        fehler.append("meta.gesamtpunkte = %g, Aufgaben summieren auf %g"
                      % (float(soll), summe))

    zeit = meta.get("bearbeitungszeit_min")
    if zeit and summe:
        quote = float(zeit) / summe
        if not 0.7 <= quote <= 1.6:
            warnung.append("Zeit/Punkte-Verhaeltnis %.2f min/P. ist "
                           "unueblich (Richtwert 1.0)" % quote)

    if blueprint:
        bp_ids = [a.get("id") for a in blueprint.get("aufgaben", [])]
        fehlend = [i for i in bp_ids if i not in ids]
        extra = [i for i in ids if i not in bp_ids]
        if fehlend:
            fehler.append("Blueprint-Aufgaben fehlen: %s" % ", ".join(fehlend))
        if extra:
            warnung.append("Nicht im Blueprint: %s" % ", ".join(extra))

    stat = {"aufgaben": len(aufgaben), "punkte": summe, "themen": themen}
    return fehler, warnung, stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--blueprint")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as fh:
        daten = json.load(fh)
    bp = None
    if args.blueprint:
        with open(args.blueprint, encoding="utf-8") as fh:
            bp = json.load(fh)

    fehler, warnung, stat = pruefe(daten, bp)

    if stat:
        print("Aufgaben: %d | Punkte gesamt: %g" % (stat["aufgaben"], stat["punkte"]))
        print("Themenverteilung:")
        for thema, p in stat["themen"].most_common():
            anteil = 100.0 * p / stat["punkte"] if stat["punkte"] else 0
            print("  %-45s %5g P.  (%4.1f %%)" % (thema[:45], p, anteil))
        print()
    for w in warnung:
        print("WARNUNG: %s" % w)
    for f in fehler:
        print("FEHLER : %s" % f)
    if not fehler:
        print("\nOK - keine Fehler. Rendern moeglich.")
    else:
        print("\n%d Fehler. Bitte in der JSON korrigieren, dann erneut pruefen."
              % len(fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
