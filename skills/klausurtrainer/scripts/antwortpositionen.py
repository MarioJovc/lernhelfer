#!/usr/bin/env python3
"""
antwortpositionen.py - Lost VOR der Inhaltserzeugung aus, an welcher Position
die richtige Antwort steht. Erst danach werden Antworttext und Distraktoren
geschrieben.

Das ist der Kern des Skills: wer erst die richtige Antwort formuliert und sie
dann irgendwo einsortiert, erzeugt zuverlaessig Muster (Position, Laenge,
Detailgrad). Wer die Position vorher zieht, kann sie nicht mehr an den Inhalt
anpassen.

Aufruf:
    python3 antwortpositionen.py --fragen 20 --optionen 4 --richtige 1
    python3 antwortpositionen.py --fragen 15 --optionen 5 --richtige 2 --seed 42
    python3 antwortpositionen.py --fragen 20 --optionen 4 --modus zufall

Modi:
    balanciert (Standard) - jede Position kommt etwa gleich oft vor, Reihenfolge
                            zufaellig, keine langen Wiederholungen
    zufall                - reine Ziehung je Frage; kann Haeufungen enthalten

Schreibt positionen.json und gibt eine Tabelle aus.
"""

import argparse
import json
import random
import sys
from collections import Counter
from itertools import combinations

BUCHSTABEN = "ABCDEFGH"


def alle_kombis(k, r):
    return [tuple(c) for c in combinations(range(k), r)]


def ziehe_balanciert(n, k, r, rng, versuche=200):
    """Gleichverteilung ueber alle moeglichen Kombinationen, dann mischen."""
    kombis = alle_kombis(k, r)
    voll, rest = divmod(n, len(kombis))
    pool = kombis * voll + rng.sample(kombis, rest)
    bestes, beste_bewertung = None, None
    for _ in range(versuche):
        rng.shuffle(pool)
        # Bewertung: Anzahl direkter Wiederholungen moeglichst klein
        wdh = sum(1 for i in range(1, len(pool)) if pool[i] == pool[i - 1])
        lauf = max_lauf(pool)
        bew = (lauf, wdh)
        if beste_bewertung is None or bew < beste_bewertung:
            bestes, beste_bewertung = list(pool), bew
        if bew <= (2, 0):
            break
    return bestes


def max_lauf(folge):
    best = akt = 1
    for i in range(1, len(folge)):
        akt = akt + 1 if folge[i] == folge[i - 1] else 1
        best = max(best, akt)
    return best


def ziehe_zufall(n, k, r, rng):
    return [tuple(sorted(rng.sample(range(k), r))) for _ in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragen", type=int, required=True)
    ap.add_argument("--optionen", type=int, default=4)
    ap.add_argument("--richtige", type=int, default=1)
    ap.add_argument("--modus", choices=["balanciert", "zufall"],
                    default="balanciert")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default="positionen.json")
    args = ap.parse_args()

    k, r = args.optionen, args.richtige
    if not 2 <= k <= len(BUCHSTABEN):
        print("optionen muss zwischen 2 und %d liegen" % len(BUCHSTABEN))
        return 1
    if not 1 <= r < k:
        print("richtige muss mindestens 1 und kleiner als optionen sein")
        return 1

    seed = args.seed if args.seed is not None else random.randrange(1, 10 ** 9)
    rng = random.Random(seed)
    zieh = ziehe_balanciert if args.modus == "balanciert" else ziehe_zufall
    gezogen = zieh(args.fragen, k, r, rng)

    daten = {
        "seed": seed, "modus": args.modus, "optionen": k, "richtige": r,
        "buchstaben": list(BUCHSTABEN[:k]),
        "zuordnung": [
            {"nr": i + 1, "id": "F%d" % (i + 1),
             "richtige_positionen": list(p),
             "richtige_buchstaben": [BUCHSTABEN[x] for x in p]}
            for i, p in enumerate(gezogen)],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1)

    print("Ziehung: %d Fragen, %d Optionen, %d richtige | Modus %s | Seed %d\n"
          % (args.fragen, k, r, args.modus, seed))
    for e in daten["zuordnung"]:
        print("  F%-3d richtig: %s" % (e["nr"], ", ".join(e["richtige_buchstaben"])))
    zaehl = Counter(b for e in daten["zuordnung"] for b in e["richtige_buchstaben"])
    print("\nVerteilung:", "  ".join("%s=%d" % (b, zaehl.get(b, 0))
                                     for b in BUCHSTABEN[:k]))
    print("Laengster Lauf gleicher Belegung: %d" % max_lauf(gezogen))
    print("\nGeschrieben: %s" % args.out)
    print("Diese Zuordnung ist ab jetzt bindend. Sie wird nicht mehr geaendert, "
          "auch nicht,\nwenn spaetere Pruefungen etwas beanstanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
