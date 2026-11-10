---
name: "foliennotizen"
description: "Macht aus einem Foliensatz (Vorlesungsfolien als PDF oder PPTX, Querformat) einen kommentierten Foliensatz als PDF im Hochformat im TUDa-Design – jede Folie oben unverändert, darunter die Erläuterungen, die die Dozentin beim Präsentieren geben würde (Intuition, wichtige Begriffe, Diagramme, Formeln); Folien mit mehreren gewichtigen Aspekten zusätzlich Schritt für Schritt mit gelben Markierungen auf der Folie, am Ende eine kurze Zusammenfassung mit Takeaways und Kernbegriffen. Nutze diesen Skill IMMER, wenn Folien kommentiert, erläutert, erklärt, annotiert oder zum Nacharbeiten und Selbststudium aufbereitet werden sollen – auch bei „erklär mir die Folien“, „Vorlesung verpasst“, „kommentierter Foliensatz“, „Folien mit Erklärungen drunter“, „Handout mit Notizen“, „Skript aus den Folien“, „Folien nachbereiten“ oder wenn ein Foliensatz hochgeladen wird mit der Bitte, ihn verständlich zu machen. Nicht für reine Textzusammenfassungen ohne Folienseiten (dafür wissensdestillat) und nicht für Probeklausuren."
---

# Foliennotizen

Aus einem Foliensatz im Querformat wird ein PDF im Hochformat (A4): je Folie mindestens
eine Seite, oben die Originalfolie, darunter der Kommentar. Folien mit mehreren
gewichtigen Aspekten bekommen zusätzlich Schritt-Seiten, auf denen jeweils ein Teil der
Folie gelb markiert und erklärt wird. Am Ende steht eine kurze Zusammenfassung der
Vorlesung mit Takeaways und Kernbegriffen. Ziel: Wer die Vorlesung verpasst hat,
versteht mit Folie und Kommentar so viel, als wäre er dabei gewesen.

**Kernprinzip: Inhalt und Layout sind getrennt.** Du schreibst nur Kommentare als
Markdown (`kommentar/*.md`). Layout, Einbettung der Folien, Markierungen und Prüfung
erledigen die Skripte. Die Originalfolien werden als Vektorgrafik unverändert
eingebettet – nie neu gezeichnet, gerastert oder beschnitten. Markierungen liegen auf
einer eigenen PDF-Ebene über der Folie, das Original darunter bleibt unangetastet.

`SKILL` steht im Folgenden für den Ordner dieser SKILL.md.

## Ablauf

| Schritt | Was | Ergebnis |
|---|---|---|
| 0 | Abhängigkeiten | `pip install` einmal pro Sitzung |
| 1 | Analyse | `arbeit/` mit Folien-PDF, Text, Bildern, Element-IDs |
| 2 | Verstehen | ganze Vorlesung gelesen und angesehen |
| 3 | Einordnen | je Folie: ohne Kommentar, kurz, normal oder mit Schritten |
| 4 | Kommentieren | `kommentar/*.md` blockweise, dazu `arbeit/begriffe.md`, am Ende die Zusammenfassung |
| 5 | Bauen | über `arbeit/bauen.py`: kommentiertes PDF mit Zeichen in der Fußzeile |
| 6 | Sichtprüfung | Vorschaubilder angesehen, Markierungen, Spalten und Fußzeile sitzen |
| 7 | Abschlussprüfung | `kommentar_pruefen.py` meldet BESTANDEN |
| 8 | Ausliefern | PDF an den Nutzer |

Frag vorher nichts, was du selbst klären kannst. Rückfragen nur, wenn wirklich unklar
ist, welche Datei gemeint ist. Die Kommentarsprache ist die Sprache, in der der Nutzer
schreibt (meist Deutsch), auch bei englischen Folien – Fachbegriffe der Folie bleiben
dann im Original stehen und werden beim ersten Auftreten übersetzt oder erklärt.

### 0. Abhängigkeiten

```bash
pip install --break-system-packages pymupdf pyphen
```

ReportLab, matplotlib, numpy, Pillow und fontTools sind meist vorhanden (sonst ebenfalls
per pip). Für PPTX wird LibreOffice (`soffice`) gebraucht; fehlt es, den Nutzer um einen
PDF-Export bitten. Die Schriften liegen in `SKILL/assets/fonts/`.

### 1. Analyse

```bash
python3 SKILL/scripts/folien_analyse.py <Foliensatz.pdf|.pptx> --out arbeit
```

Legt in `arbeit/` ab: `folien.pdf` (Quelle für alles Weitere), `analyse.json`,
`folien_text.md` (Text aller Folien mit Element-IDs, ohne Kopf- und Fußzeilen),
`bilder/uebersicht_NN.png` (je 4 Folien), `bilder/folie_NNN.png` (einzelne Folie) und
`bilder/karte_NNN.png` (Lagekarte: Elemente mit IDs und Koordinatenraster).

Die Ausgabe nennt die erkannte Akzentfarbe, Aufbaustufen (Beamer-`\pause`,
Animationen), Folien ohne Textebene (Scans) und Folien mit Sprechernotizen. PPTX wird
per LibreOffice exportiert; besser ist ein PDF-Export aus PowerPoint, weil dann die
Schriften exakt stimmen – das dem Nutzer kurz sagen, aber trotzdem weiterarbeiten.

### 2. Verstehen

Erst die ganze Vorlesung erfassen, dann schreiben – sonst fehlen die Querbezüge
(„auf Folie 7 kommt das wieder“), die einen Kommentar erst wertvoll machen.

- `arbeit/folien_text.md` vollständig lesen.
- Alle Übersichtsbögen ansehen: Diagramme, Abbildungen und Layout erschließen sich
  nur im Bild, Formeln sind im extrahierten Text oft zerstückelt.
- Dichte Folien, Diagramme und Formelfolien zusätzlich einzeln (`folie_NNN.png`) ansehen.
- **Sprechernotizen** sind die Stimme des Dozenten: Was dort steht, gehört inhaltlich
  in den Kommentar (in eigenen Worten).
- Gibt es für das Modul ein Wissensdestillat oder einen Volltext (Skill
  `wissensdestillat`), als Kontext nutzen.

Bei langen Foliensätzen (mehr als etwa 40 Folien) den Kontext schonen: Text und
Übersichtsbögen einmal ganz durchgehen und den roten Faden in ein paar Stichpunkten
festhalten; Einzelbilder und Lagekarten erst beim Kommentieren des jeweiligen Blocks öffnen.

### 3. Einordnen

Lege für alle Folien fest, wie sie behandelt werden, bevor du schreibst. Maßstab ist der
Mehrwert: Komplexes gründlich, Triviales knapp.

| Art | Typische Folien | Seiten | Umfang |
|---|---|---|---|
| ohne Kommentar | Organisatorisches, das vollständig für sich spricht: Team, Kontakt, Sprechstunden, Termine, Übungsgruppen, Stellenangebote; Gliederungsfolien, die nur die Agenda wiederholen | 1 | nur Kennung und Titel, im Markdown `(ohne Kommentar)` |
| kurz | Titel, erste Gliederung, Abschnittsstart, Organisatorisches mit Einordnungsbedarf (welches Buch zum Einstieg, Bezug zum Kurs), Folien mit einfachen Punkten | 1 | 1–3 Sätze oder wenige kurze Stichpunkte |
| normal | gewöhnliche Inhaltsfolie, auch Definitionen, Formeln, Diagramme | 1 | so viel wie nötig, meist 80–250 Wörter |
| mit Schritten | Folien mit zwei oder mehr gewichtigen, auf der Folie getrennt sichtbaren Teilen: zwei Diagramme nebeneinander, Code und Zustand, ein Schaubild mit klar getrennten Bereichen, eine dichte Tabelle mit Erklärkästen, zwei Kernbegriffe auf einer Folie, eine Formel mit Herleitung, ein Gleichungssystem, ein Diagramm mit nummerierten Stationen; außerdem, wenn die Erklärung nicht auf eine Seite passt | 1 + ein Schritt je gewichtigem Aspekt (Kernfolien oft 3–5) | Überblick 2–4 Sätze, je Schritt so viel wie der Aspekt braucht |

**Ohne Kommentar** heißt wirklich selbsterklärend: Ein Satz darunter würde nur
wiederholen, was auf der Folie steht („Hier stellt sich das Team vor“). Solche Füllsätze
empfinden Leser als Ballast. Sobald etwas einzuordnen ist – eine Bonusregel, ein Bezug
zum Kursinhalt, welches Buch sich zum Einstieg eignet –, bekommt die Folie einen kurzen
Kommentar. Inhaltsfolien bekommen immer einen.

**Eine Seite je Folie ist der Normalfall, Schritte sind die Ausnahme – aber keine
Seltenheit.** Richtwert: etwa jede vierte bis fünfte Inhaltsfolie (Titel, Gliederung und
Organisatorisches nicht mitgezählt), bei 47 Folien mit rund 30 Inhaltsfolien also 6–8
Folien mit Schritten; bei formel- und modelllastigen Vorlesungen auch mehr. Schritte
helfen dort, wo das Auge sonst nicht weiß, wohin es schauen soll. Mehrere Stichpunkte,
Symbole oder Teile allein sind darum kein Grund für Schritte: Einfache Aspekte stehen
gemeinsam auf einer Seite, gern als kurze Stichpunkte.

**Wie viele Schritte: so viele, wie die Folie gewichtige Aspekte hat – ohne feste
Obergrenze.** Leser haben zurückgemeldet, dass gerade die wichtigsten Folien zu knapp
ausfielen, wenn sie in zwei Schritte gezwängt wurden: Eine Herleitung mit vier
Zwischenstufen oder ein Diagramm mit drei nummerierten Stationen verliert den roten
Faden, wenn man Stufen zusammenlegt, und das Auge findet die Stelle nicht mehr, über die
der Text gerade spricht. Darum:

- **Ein Schritt je gewichtigem, eigenständigem Aspekt.** Hat eine Folie genau zwei
  solche Teile, sind zwei Schritte richtig. **Kernfolien** – das zentrale Modell der
  Vorlesung, Herleitungen, Gleichungssysteme, Diagramme mit Verschiebungen und neuem
  Gleichgewicht, längere Wirkungsketten – haben oft drei bis fünf.
- **Gibt die Folie eine Reihenfolge vor, folgen die Schritte ihr:** nummerierte
  Erläuterungen im Diagramm („1. … 2. … 3. …“), Zeilen einer Herleitung, eine Pfeilkette.
  Je Station oder Umformung, die eigens erklärt werden muss, ein Schritt. Bei einer
  einfachen Ursache-Wirkung mit zwei Stationen, die man auf einen Blick versteht, reicht
  dagegen oft eine Seite.
- **Kleinigkeiten bekommen keinen eigenen Schritt**, sondern wandern in den Überblick oder
  in den passenden Schritt. Prüfstein: Hat jeder Schritt eine eigene Markierung und einen
  eigenen Gedanken, den man danach besser versteht? Markieren zwei Schritte dieselbe
  Stelle oder sagen dasselbe, zusammenlegen. Mehr als sechs Schritte deuten darauf hin,
  dass Kleinigkeiten einzeln stehen.

Diese Regeln gehen der Angabe „meist 2–3 Schritte“ in `references/leitfaden.md`
(Abschnitt 8) vor. Eine Seite fasst unter einer 16:9-Folie gut 350, unter einer
4:3-Folie gut 300 Wörter. Formeln mit Legende und Herleitung (siehe Schritt 4) brauchen
mehr Platz als Fließtext – auch das ist ein häufiger Grund für einen zusätzlichen
Schritt, etwa einen je Formelblock.

**Aufbaustufen** (dieselbe Folie wird schrittweise aufgedeckt) sind bereits Schritte:
Jede Stufe kommentiert genau das, was neu dazukommt, ohne Markierungen. Das Layout
beschriftet sie als „Aufbaustufe k von n“. Jede PDF-Seite des Foliensatzes ist eine
Folie und bekommt mindestens eine Seite – auch Aufbaustufen.

### 4. Kommentieren

Vor dem ersten Schreiben **`SKILL/references/leitfaden.md`** (was ein guter Kommentar
leistet, mit Beispielen) und **`SKILL/references/kommentar_format.md`** (Dateiformat,
Markierungsziele) lesen.

Das Format in Kürze:

```markdown
---
titel: Lineare Regression und Gradientenabstieg
veranstaltung: Maschinelles Lernen I
sprache: de
---

# Folie 2: Sprechstunden
(ohne Kommentar)

# Folie 3: Motivation: Mietpreise vorhersagen
Kommentar auf einer Seite – der Normalfall.

# Folie 8: Gradientenabstieg
Kurze Einordnung der ganzen Folie (diese Seite zeigt sie unmarkiert).

## Die Update-Regel
@rahmen: b3-b5
@markiere: b6-b9
Erklärung des gelb umrahmten Formelblocks und der markierten Stichpunkte.

## Das Höhenliniendiagramm
@rahmen: i1
Erklärung des Diagramms.

# Zusammenfassung
Kurzfassung der Vorlesung in drei bis fünf Sätzen.

## Takeaways
- …

## Kernbegriffe
- **Begriff**: Erklärung in einem Satz (Folie 4)
```

- `# Folie N: Titel` beginnt eine Folie; jede `## …`-Überschrift darunter ist ein
  Schritt (eigene Seite, dieselbe Folie mit Markierung). Folien ohne `##` bleiben einseitig –
  der Normalfall.
- `(ohne Kommentar)` als einzige Zeile: Die Seite zeigt Folie, Kennung und Titel, darunter
  bleibt es leer. Nur für die Art „ohne Kommentar“ aus Schritt 3; den deutschen Titel
  trotzdem setzen. Funktioniert nur über `arbeit/bauen.py`.
- Markierungsziele stehen in `folien_text.md` und auf den Lagekarten: `b3` (Textblock),
  `b3.2` (Zeile), `b3-b5`, `i1` (Bild), `g1` (Grafik), `text="…"`, `bereich=x0,y0,x1,y1`
  (Anteile der Folie, von der Lagekarte ablesen). `@markiere:` für Text (gelber Marker),
  `@rahmen:` für Bilder, Diagramme und Bereiche.
- Vor dem Markieren die Lagekarte der Folie ansehen: Die Markierung muss genau das
  Element treffen, über das der Schritt spricht. Beides ist gelb wie ein Textmarker.
- Ein Rahmen liegt 5 pt außerhalb seines Ziels (bei 16:9 etwa 0,016 der Folienhöhe und
  0,01 der Breite). Stehen Nachbarn dichter – gestapelte Kästen, Tabellenzeilen, die
  Titellinie oder Fußlinie der Folie –, die Kante mit `bereich=` in die Lücke legen: den
  Bereich um diese 5 pt kleiner wählen als das, was eingerahmt wirken soll. Keine
  Rahmenkante darf durch Text oder einen fremden Kasten laufen.
- **Begriffe einmal erklären:** Wichtige Begriffe stehen im Kommentar **fett** und werden
  beim ersten Auftreten erklärt, danach nur noch verwendet. Eine Erinnerung nur, wenn ein
  Begriff in einem ganz neuen Zusammenhang wichtig wird. Führe dazu `arbeit/begriffe.md`
  (Begriff | Folie | Kurzdefinition), lies sie vor jedem Block und ergänze sie danach.
  Ausnahme sind Variablenlegenden unter Formeln (siehe unten): Dort steht jedes Symbol,
  auch ein schon bekanntes – mit wenigen Wörtern als Erinnerung, nicht als neue Definition.
- **Zusammenfassung:** Nach der letzten Folie ein Abschnitt `# Zusammenfassung` mit
  Kurzfassung (3–5 Sätze), `## Takeaways` (4–7 Punkte) und `## Kernbegriffe` (6–12
  Begriffe aus `begriffe.md`, je ein Satz und die Folie). Eine Seite, nicht mehr.
- Blockweise schreiben, 8–12 Folien je Datei (`kommentar/01.md`, `kommentar/02.md`, …).
  Die Dateien werden nach Namen sortiert zusammengesetzt. So bleibt jede Datei
  überschaubar und einzelne Folien lassen sich später gezielt ändern.
- Nach jedem Block jeden Kommentar gegen seine Folie halten (Prüfliste im Leitfaden):
  Kommt alles Wichtige vor, Triviales nur knapp? Stimmt alles fachlich? Wird nichts
  wiederholt – weder die Folie noch ein schon erklärter Begriff? Hat jede tragende Formel
  ihre Legende, und hat jede Kernfolie so viele Schritte, wie sie gewichtige Aspekte hat?

**Formeln aufschlüsseln.** Für Leser ohne Vorlesung sind Formeln die größte Hürde: Auf der
Folie stehen Symbole, deren Bedeutung die Dozentin mündlich erklärt hat. Eine Formel, die
man nicht lesen kann, kann man auch nicht verstehen – deshalb bekommt jede inhaltlich
tragende Formel (nicht bloße Festlegungen wie G = Ḡ) diese vier Teile:

1. **Aussage in Worten:** ein, zwei Sätze, was die Formel sagt und wofür man sie braucht.
2. **Variablenlegende:** direkt unter der Formel jedes Symbol in der Notation der Folie,
   mit Bedeutung und – wo sinnvoll – Einheit, als kurze Liste. Die Legende ist vollständig,
   damit man nicht zurückblättern muss; schon erklärte Symbole bekommen nur ein paar
   Wörter („L: Arbeit, in Stunden“), neue eine echte Erklärung.
3. **Aufschlüsselung:** Wird eine Formel hergeleitet oder umgeformt, steht jede Umformung
   als eigene abgesetzte Formel (`$$…$$`) da, mit einem Halbsatz, was passiert ist
   („nach L ableiten: der Exponent wandert nach vorn und sinkt um eins“). Zwischenschritte,
   die auf der Folie fehlen, ergänzen.
4. **Zahlenbeispiel oder Plausibilitätsprüfung**, wo es hilft: Zahlen einsetzen und
   nachrechnen, einen Grenzfall durchspielen, die Einheiten prüfen.

```markdown
## Die Standardisierung
@rahmen: b4
Die Formel misst, wie viele Standardabweichungen ein Messwert vom Mittelwert entfernt ist:

$$z = \dfrac{x - \mu}{\sigma}$$

- x: der einzelne Messwert, etwa eine Körpergröße von 190 cm
- μ: der Mittelwert der Verteilung, hier 178 cm
- σ: die Standardabweichung, also die typische Streuung um μ, hier 8 cm
- z: der standardisierte Wert, ohne Einheit

Erst wird der Abstand zum Mittelwert gebildet (190 − 178 = 12 cm), dann durch die
Streuung geteilt: z = 12/8 = 1,5. Die Person ist 1,5 Standardabweichungen größer als der
Durchschnitt – in Zentimetern wie in Zoll, denn die Einheit kürzt sich weg.
```

Praktisches zum Setzen:

- Symbole in der Legende nicht fett schreiben – fett bleibt Fachbegriffen vorbehalten,
  sonst meldet der Build Mehrfachbegriffe. Einfache Symbole als Unicode (α, Δ, Ȳ), `$…$`
  nur für Hoch- und Tiefstellungen.
- Für Herleitungen mehrere `$$…$$`-Zeilen untereinander; Umgebungen wie `align` kennt
  mathtext nicht. Abkürzungen aus mehreren Buchstaben als `\mathrm{MPL}` setzen, sonst
  erscheinen sie kursiv wie ein Produkt M·P·L.
- Brüche in abgesetzten Formeln mit `\dfrac{…}{…}`: `\frac` setzt mathtext so klein wie
  einen Bruch im Fließtext, und gerade die Ableitung ∂Y/∂L wird dann unlesbar.
- Dezimalkomma in Formeln als `0{,}5` – ein bloßes Komma bekommt ein Leerzeichen dahinter.
- Rechnungen mit mehr als drei, vier Gliedern als abgesetzte Formel statt im Fließtext,
  sonst bricht die Zeile mitten in der Rechnung um.

Passt die Aufschlüsselung mehrerer tragender Formeln nicht mehr auf eine Seite, bekommt
jede Formel ihren eigenen Schritt mit einem Rahmen um genau diese Formel.

### 5. Bauen

Gebaut wird über `arbeit/bauen.py`. Es ruft `SKILL/scripts/kommentar_bauen.py` mit allen
Optionen auf und ergänzt vier Dinge: das Zeichen mit Byline in der Fußzeile (siehe
TUDa-Gestaltung), Folien `(ohne Kommentar)`, eine rechte Spalte, die auf Höhe des
Fließtexts links beginnt statt schon auf Höhe der Kennung, und eine Silbentrennung, die
Wörter mit Bindestrich Teil für Teil trennt (sonst entsteht „Time-S-haring“). Der Code
steht als Block am Ende dieser SKILL.md; der erste Befehl kopiert ihn exakt heraus – einmal
pro Sitzung. Für jeden weiteren Build genügt der zweite.

```bash
python3 - SKILL/SKILL.md arbeit/bauen.py <<'EOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
open(sys.argv[2], "w", encoding="utf-8").write(re.search(r"```python\n(# bauen\.py.*?)```", text, re.S)[1])
EOF
python3 arbeit/bauen.py --skill SKILL --folien arbeit/folien.pdf --kommentar kommentar \
    --out "<Ausgabeordner>/<Originalname>_kommentiert.pdf"
```

Ausgabeordner ist der Ort, von dem aus Dateien an den Nutzer gehen (z. B.
`/mnt/user-data/outputs`, sonst das Arbeitsverzeichnis).

Der Build bricht mit einer Liste ab, wenn Folien oder die Zusammenfassung fehlen, eine
Folie doppelt vorkommt oder ein Markierungsziel nicht existiert – Fehler in den
Markdown-Dateien beheben, nicht im Skript. Zwischenstände: `--entwurf` (fehlende Teile
als Platzhalter) oder `--nur 5-9` (`--nur zf` nur die Zusammenfassung).

Der Kommentar steht unter der Folie und läuft die linke Spalte hinab; die rechte Spalte
wird erst benutzt, wenn die linke voll ist. Hinweise des Builds ernst nehmen:
- **Überlauf** auf eine Fortsetzungsseite: kürzen oder – nur wenn die Bedingungen aus
  Schritt 3 erfüllt sind – in Schritte teilen.
- **Nur wenige Zeilen in der rechten Spalte:** ein, zwei Sätze kürzen.
- **Begriff auf mehreren Folien fett:** prüfen, dass er nur einmal erklärt wird.

Die Akzentfarbe kommt aus der Analyse (passend zu den Folien), sonst ist sie TUDa-0b.
Wünscht der Nutzer eine bestimmte Farbe, `akzent: 9c` in den Kopf der ersten
Kommentardatei schreiben (nur TUDa-Palette 0a–0d, 1a–11d). Das Zeichen bleibt davon
unberührt in TU-Blau.

### 6. Sichtprüfung

```bash
python3 SKILL/scripts/vorschau.py "<…>_kommentiert.pdf" --out arbeit/vorschau --folien 4,8,12
```

Alle Folien mit Schritten ansehen (`--folien` mit ihren Nummern), dazu zwei, drei
normale Seiten, eine Seite ohne Kommentar, eine Seite mit Text in der rechten Spalte und
die Zusammenfassung (`--folien zf`). Prüfen: Sitzt jede Markierung auf dem Element, über
das der Text spricht, und läuft keine Rahmenkante durch Text oder einen fremden Kasten?
Ist nichts verdeckt, was gelesen werden muss? Fließt der Text ruhig unter der Folie, und
beginnt die rechte Spalte auf Höhe des Fließtexts links? Steht unten links das Zeichen
mit „Foliennotizen“ und Byline, daneben der Hinweisblock? Falsche Markierungen über
das Ziel in der Markdown-Datei korrigieren und neu bauen.

### 7. Abschlussprüfung (Pflicht vor jeder Auslieferung)

```bash
python3 SKILL/scripts/kommentar_pruefen.py --folien arbeit/folien.pdf \
    --pdf "<…>_kommentiert.pdf" --original <Upload> --bericht arbeit/pruefbericht.md
```

Die Prüfung arbeitet unabhängig vom Build und kontrolliert:
- **Vollständigkeit und Reihenfolge**: jede Folie 1…N kommt vor, aufsteigend, ihre
  Seiten stehen zusammen, die erste Seite jeder Folie zeigt sie unmarkiert.
- **Unverändert**: Jede eingebettete Folie wird mit ausgeblendeter Markierungsebene
  gerendert und pixelweise mit dem Original verglichen, dazu Wort für Wort ihr Text.
- **Format**: A4 hoch, Folie vollständig in der oberen Hälfte, Seitenverhältnis erhalten.
- **Markierungen**: jede Schritt-Seite sichtbar markiert, keine Gesamtansicht markiert.
- **Zusammenfassung**: vorhanden und am Ende.
- **Herkunft**: `folien.pdf` ist der Upload (bzw. sieht auf jeder Seite gleich aus).

Ausgeliefert wird nur bei **BESTANDEN** – oder im nachgewiesenen Grenzfall
Kantenglättung (unten). Bei einem Fehler die Ursache beheben und neu bauen; nie ein
Ergebnis mit Fehlern ausliefern oder die Prüfung überspringen.

**Grenzfall Kantenglättung:** Meldet die Prüfung bei einzelnen Seiten nur eine knappe
lokale Abweichung (Ø und Anteil praktisch 0, „lokal“ knapp über 24), liegt das meist an
der Kantenglättung einzelner Glyphen beim Rendern in genau dieser Auflösung. Dann für die
gemeldeten Seiten nachweisen, dass der Inhaltsstrom der eingebetteten Folie byte-identisch
mit der Quellseite ist und die Abweichung bei höherer Auflösung verschwindet:

```bash
python3 - arbeit/folien.pdf "<…>_kommentiert.pdf" SKILL/scripts 9,12,15 <<'EOF'
import re, sys
sys.path.insert(0, sys.argv[3])
import pymupdf
import kommentar_pruefen as kp
src, aus = pymupdf.open(sys.argv[1]), pymupdf.open(sys.argv[2])
for c in aus.layer_ui_configs():                       # Markierungsebene ausblenden
    if c.get("text") == "Markierungen":
        aus.set_layer_ui_config(c["number"], action=2)

def formen(xref, tiefe=0):
    """Inhaltsströme aller Form-XObjects unter xref (die Folie steckt geschachtelt darin)."""
    if tiefe > 4 or aus.xref_get_key(xref, "Subtype")[1] != "/Form":
        return []
    erg = [aus.xref_stream(xref)]
    typ, res = aus.xref_get_key(xref, "Resources/XObject")
    obj = res if typ == "dict" else aus.xref_object(int(res.split()[0])) if typ == "xref" else ""
    for x in re.findall(r"(\d+) 0 R", obj):
        erg += formen(int(x), tiefe + 1)
    return erg

for s in map(int, sys.argv[4].split(",")):
    p = aus[s - 1]
    info = kp.privat(aus, p)
    q = src[info["folie"] - 1]
    quelle = b"".join(src.xref_stream(x) for x in q.get_contents())
    gleich = any(quelle in formen(x[0]) for x in p.get_xobjects())
    m = info["rect"].width / q.rect.width
    lokal = [kp.vergleich(kp.pixel(p, pymupdf.Matrix(z, z), clip=info["rect"]),
                          kp.pixel(q, pymupdf.Matrix(z * m, z * m)))[2] for z in (3, 4)]
    print(f"Seite {s}: Inhaltsstrom {'identisch' if gleich else 'ABWEICHEND'}, "
          f"lokal bei Zoom 3/4: {lokal[0]:.0f}/{lokal[1]:.0f}")
EOF
```

Ist der Inhaltsstrom auf allen gemeldeten Seiten identisch und „lokal“ bei Zoom 3 und 4
höchstens 2, ist die Folie nachweislich unverändert: ausliefern und den Befund in einem
Satz nennen, ohne Rückfrage – Nutzer empfinden die Frage nach einem Rendering-Artefakt als
Unterbrechung, denn am PDF gibt es nichts zu beheben. Den Nachweis in
`arbeit/pruefbericht.md` festhalten. Ist ein Inhaltsstrom abweichend oder bleibt die
Abweichung bei höherer Auflösung, ist es ein echter Fehler: Ursache beheben, neu bauen.

### 8. Ausliefern

Das PDF mit dem verfügbaren Datei-Werkzeug übergeben (z. B. `present_files` oder
`SendUserFile`). Dazu knapp: Seitenzahl, welche Folien Schritt-Seiten haben, dass am Ende
eine Zusammenfassung steht, das Prüfergebnis in einem Satz („alle 42 Folien enthalten, in Reihenfolge und pixelgleich
mit dem Original“) und der Hinweis, dass die Erläuterungen KI-generiert sind. Den Ordner
`kommentar/` aufheben – Korrekturen setzen dort an.

## Korrekturwünsche

Nur die Markdown-Abschnitte der betroffenen Folien ändern, dann Schritte 5–7
wiederholen. Den Foliensatz nie komplett neu kommentieren, wenn nur einzelne Folien
betroffen sind. Wünscht der Nutzer mehr Tiefe („mehr Schritte“, „Formeln genauer“),
die Kernfolien nach Schritt 3 neu einordnen und ihre Abschnitte nach Schritt 4
überarbeiten – die übrigen Folien bleiben, wie sie sind.

## TUDa-Gestaltung

Das Layout setzt das Corporate Design der TU Darmstadt um, soweit es frei verfügbar ist:
Identitätsbalken (4 mm Balken in der Akzentfarbe, 1,4 mm Abstand, 1,2 pt schwarze
Linie), Ränder 15/15/15/20 mm, 0,6-pt-Abschlusslinie mit Paginierung, ausschließlich
Farben der TUDa-Palette und genau eine Akzentfarbe, Fließtext schwarz in Charis SIL
(freier Charter-Abkömmling), Überschriften in Roboto (Ersatz für Frontpage),
Infozeilen in Roboto Condensed (Ersatz für Stafford), Textspalten höchstens 90 mm
breit (der Text füllt erst die linke Spalte, dann die rechte), Markierungen gelb in
TUDa-6a (Textmarker und Kästen, Kästen mit Kante in 6b).

**Zeichen statt TU-Logo.** Jede Seite trägt unten links das *Zeichen Fünffingerturm* aus
dem Designsystem „TUDa UI“ im Kleinformat: Kachel 6,2 mm in TU-Blau #005AA9 mit fünf
weißen Streifen nach `zeichen-fuenffingerturm-16.svg`, aber waagerecht zentriert – in der
SVG sitzen die Streifen (x = 4 bis 13 im 16er-Raster) eine halbe Einheit zu weit rechts,
was im Kleinformat sichtbar schief wirkt; im Layout stehen sie bei x = 3,5 bis 12,5.
Rechts daneben stehen der App-Name „Foliennotizen“ (Roboto Bold) und darunter die
Byline „by Mario Jovanovic“, dann der Hinweisblock: „Inoffiziell, kein Angebot der TU
Darmstadt“ und darunter der KI-Hinweis (Kopfdaten-Feld `fusszeile`, Standard
„Kommentierter Foliensatz · Erläuterungen KI-generiert, nicht vom Lehrstuhl geprüft“).
Die erste Zeile steht auf der Grundlinie der Seitenzahl.

Warum so: Das Designsystem sieht das Zeichen für inoffizielle Tools ohne Logo-Freigabe
vor. Die Wort-Bildmarke der TU ist geschützt und offiziellen Publikationen vorbehalten,
deshalb kommt sie nicht ins Layout – auch nicht zusätzlich zum Zeichen. Das Zeichen steht
nie zusammen mit dem TU-Logo; darum sitzt es unten links, weit weg von der eingebetteten
Folie, die ihr eigenes Logo meist oben rechts trägt. Bis 24 px Bildschirmgröße
(6,2 mm ≈ 23 px) gilt laut Designsystem das Kleinformat, weil die Rundbögen dort nicht
mehr lesbar sind. Byline, Inoffiziell- und KI-Hinweis bleiben immer stehen, damit niemand
den Foliensatz für Material des Lehrstuhls hält. Ändert sich das Zeichen im Designsystem,
die Streifen-Koordinaten im Codeblock unten aus der neuen `-16.svg` übernehmen und
dabei zentriert halten.

## Dateien

- `scripts/folien_analyse.py` – Schritt 1: PDF/PPTX einlesen, Text, Bilder, Element-IDs, Akzentfarbe
- `scripts/kommentar_bauen.py` – Schritt 5: Markdown → kommentiertes PDF
- Codeblock `bauen.py` (unten) – Schritt 5: ruft `kommentar_bauen.py` auf; Zeichen in der Fußzeile, Folien ohne Kommentar, bündige rechte Spalte, Silbentrennung
- `scripts/vorschau.py` – Schritt 6: Seiten als Bilder zum Ansehen
- `scripts/kommentar_pruefen.py` – Schritt 7: unabhängige Abschlussprüfung
- `scripts/folienlib.py` – gemeinsame Funktionen (Palette, Elementzerlegung)
- `references/leitfaden.md` – was ein guter Kommentar leistet, mit Beispielen (zur Zahl der Schritte und zu Formeln gelten die Regeln dieser SKILL.md, Schritte 3 und 4)
- `references/kommentar_format.md` – vollständiges Dateiformat und alle Markierungsziele
- `assets/beispiel_kommentar.md` – vollständiges Beispiel einer Kommentardatei
- `assets/fonts/` – Charis SIL (OFL), Roboto und Roboto Condensed (Apache 2.0)

## Ergänzungen zum Build (bauen.py)

Wird in Schritt 5 nach `arbeit/bauen.py` kopiert und nimmt alle Optionen von
`kommentar_bauen.py` an, dazu `--skill SKILL`. Die mitgelieferten Skripte bleiben
unverändert; der Block ersetzt nur die Fußzeile (`KommentarDokument.seitenende`), hängt
sich in `spalten_rahmen` und `markdown_flowables` ein und gibt ReportLab eine
Silbentrennung, die Wörter mit Bindestrich Teil für Teil trennt.

```python
# bauen.py – kommentar_bauen.py mit Zeichen in der Fußzeile, bündiger rechter Spalte, Folien ohne Kommentar
# und Silbentrennung, die Wörter mit Bindestrich Teil für Teil trennt
# Aufruf: python3 arbeit/bauen.py --skill SKILL --folien … --kommentar … --out …  (alle Optionen von kommentar_bauen.py)
import sys
import types
from pathlib import Path

i = sys.argv.index("--skill")
skill = Path(sys.argv[i + 1])
del sys.argv[i:i + 2]
sys.path.insert(0, str(skill / "scripts"))
import kommentar_bauen as kb  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402
from reportlab.platypus import Flowable  # noqa: E402
from reportlab.platypus import paragraph as rl_absatz  # noqa: E402

try:
    import pyphen  # noqa: E402
except ImportError:                    # ohne pyphen trennt ReportLab gar nicht; kommentar_bauen.py meldet das
    pyphen = None

MM = kb.MM
TU_BLAU = colors.HexColor("#005AA9")   # Kachel des Zeichens (= TUDa 1b)
APP, BYLINE = "Foliennotizen", "by Mario Jovanovic"
HINWEIS = "Inoffiziell, kein Angebot der TU Darmstadt"
KACHEL = 6.2 * MM                      # Druck-Mindestgröße 6 mm; bis 24 px Kleinformat
GRUND1 = kb.RAND_U - 4.6 * MM          # erste Zeile auf der Grundlinie der Seitenzahl
RECHTS = {}                            # linke Spalte (Frame-ID) -> rechte Spalte derselben Seitenvorlage


def zeichen_klein(c, x, y, s):
    """Zeichen im Kleinformat: Kachel s×s mit fünf Streifen, waagerecht zentriert, unten links bei (x, y)."""
    u = s / 16
    c.setFillColor(TU_BLAU)
    c.roundRect(x, y, s, s, 3.5 * u, stroke=0, fill=1)
    c.setFillColor(colors.white)
    for sx, sy in ((3.5, 8), (5.5, 5), (7.5, 2), (9.5, 5), (11.5, 8)):   # 16er-Raster, Streifen von sy bis 14
        c.rect(x + sx * u, y + 2 * u, u, (14 - sy) * u, stroke=0, fill=1)


def seitenende(self, c, doc):
    fuss, self.fuss = self.fuss, ""                   # alte einzeilige Fußzeile unterdrücken
    _seitenende(self, c, doc)                          # Balken, Infozeile, Rahmen, Linie, Seitenzahl
    self.fuss = fuss
    c.saveState()
    y0 = GRUND1 + 7.6 * 0.711 - KACHEL                 # Kachel oben bündig mit der Versalhöhe von Zeile 1
    zeichen_klein(c, kb.RAND_L, y0, KACHEL)
    x = kb.RAND_L + KACHEL + 2.2 * MM
    c.setFillColor(colors.black)
    c.setFont("Roboto-Bold", 7.6)
    c.drawString(x, GRUND1, APP)
    c.setFont("RobotoCond", 6.9)
    c.drawString(x, y0, BYLINE)                        # Byline auf der Unterkante der Kachel
    x += max(stringWidth(APP, "Roboto-Bold", 7.6), stringWidth(BYLINE, "RobotoCond", 6.9)) + 8 * MM
    c.drawString(x, GRUND1, HINWEIS)
    c.drawString(x, y0, fuss)                          # KI-Hinweis (Kopfdaten-Feld fusszeile)
    c.restoreState()


class RechteSpalteBuendig(Flowable):
    """Nullhohe Marke direkt nach Kennung und Titel: Die rechte Spalte beginnt auf derselben Höhe
    wie der Fließtext links, nicht schon auf Höhe der Kennung."""

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        pass

    def frameAction(self, frame):
        rechts = RECHTS.get(frame.id)
        if rechts is not None and not frame._atTop:    # nur auf Seiten, deren linke Spalte mit dem Kopf beginnt
            rechts._y = frame._y


def spalten_rahmen(oben, gid, spalten):
    rahmen = _spalten_rahmen(oben, gid, spalten)
    if len(rahmen) == 2:
        RECHTS[rahmen[0].id] = rahmen[1]
    return rahmen


def markdown_flowables(text, stile, breite):
    if text.strip().strip("()").strip().lower() == "ohne kommentar":
        return []                                      # selbsterklärende Folie: nur Kennung und Titel
    return [RechteSpalteBuendig()] + _markdown_flowables(text, stile, breite)


if pyphen:
    class Silbentrennung(pyphen.Pyphen):
        """Wörter mit Bindestrich Teil für Teil trennen: Über den Bindestrich hinweg greifen die Trennmuster
        oft daneben („Time-S-haring“, „Mixe-d-Reality“). Am Bindestrich selbst darf weiter getrennt werden."""

        def iterate(self, wort):
            teile = wort.split("-")
            if len(teile) == 1:
                yield from super().iterate(wort)
                return
            for k in range(len(teile) - 1, -1, -1):          # von hinten nach vorn wie pyphen
                vorn = "".join(t + "-" for t in teile[:k])
                hinten = "".join("-" + t for t in teile[k + 1:])
                for kopf, rest in super().iterate(teile[k]):
                    yield vorn + kopf, rest + hinten
                if vorn and teile[k]:
                    yield vorn, teile[k] + hinten             # am Bindestrich

    rl_absatz.pyphen = types.SimpleNamespace(Pyphen=Silbentrennung)   # ReportLab baut daraus den Trenner

_seitenende = kb.KommentarDokument.seitenende
kb.KommentarDokument.seitenende = seitenende
_spalten_rahmen, kb.spalten_rahmen = kb.spalten_rahmen, spalten_rahmen
_markdown_flowables, kb.markdown_flowables = kb.markdown_flowables, markdown_flowables
kb.main()
```