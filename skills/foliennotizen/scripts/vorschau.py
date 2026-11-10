#!/usr/bin/env python3
"""Seiten des kommentierten PDFs als Bilder zum Ansehen rendern.

    python3 vorschau.py kommentiert.pdf --out vorschau [--seiten 1-6,9] [--folien 4,8]

Je zwei Seiten nebeneinander pro Bild (doppel_NN.png). Mit --folien werden alle
Seiten der genannten Folien gewaehlt (Ueberblick, Schritte, Fortsetzungen).
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw


def zahlen(text: str) -> list[int]:
    aus = []
    for teil in text.split(","):
        teil = teil.strip()
        if "-" in teil:
            a, b = teil.split("-")
            aus.extend(range(int(a), int(b) + 1))
        elif teil:
            aus.append(int(teil))
    return aus


def folie_der_seite(doc, page) -> int | None:
    typ, wert = doc.xref_get_key(page.xref, "PieceInfo/FolienKommentar/Private/Folie")
    return int(wert) if typ == "int" else None


def ist_zusammenfassung(doc, page) -> bool:
    typ, wert = doc.xref_get_key(page.xref, "PieceInfo/FolienKommentar/Private/Art")
    return typ == "name" and wert.lstrip("/") == "Zusammenfassung"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default="vorschau")
    ap.add_argument("--seiten", help="z. B. 1-4,9")
    ap.add_argument("--folien", help="alle Seiten dieser Folien, z. B. 4,8 (zf = Zusammenfassung)")
    ap.add_argument("--breite", type=int, default=820, help="Pixelbreite je Seite")
    a = ap.parse_args()
    doc = pymupdf.open(a.pdf)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.seiten:
        seiten = [s for s in zahlen(a.seiten) if 1 <= s <= len(doc)]
    elif a.folien:
        teile = [t.strip().lower() for t in a.folien.split(",")]
        mit_zf = any(t in ("zf", "zusammenfassung") for t in teile)
        wahl = set(zahlen(",".join(t for t in teile if t not in ("zf", "zusammenfassung"))))
        seiten = [i + 1 for i, p in enumerate(doc)
                  if folie_der_seite(doc, p) in wahl or (mit_zf and ist_zusammenfassung(doc, p))]
    else:
        seiten = list(range(1, len(doc) + 1))
    namen = []
    for k in range(0, len(seiten), 2):
        paar = seiten[k:k + 2]
        bilder = []
        for s in paar:
            p = doc[s - 1]
            z = a.breite / p.rect.width
            pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
            bilder.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        h = max(b.height for b in bilder)
        bogen = Image.new("RGB", (2 * a.breite + 30, h + 20), (150, 150, 150))
        for i, b in enumerate(bilder):
            bogen.paste(b, (10 + i * (a.breite + 10), 10))
        name = f"doppel_{k // 2 + 1:02d}_s{paar[0]}" + (f"-{paar[-1]}" if len(paar) > 1 else "") + ".png"
        bogen.save(out / name)
        namen.append(name)
    print(f"{len(namen)} Bilder in {out}/: " + ", ".join(namen))


if __name__ == "__main__":
    main()
