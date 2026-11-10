---
name: "klausurtrainer"
description: Erzeugt Probeklausuren für die Uni als zwei PDFs (Aufgabenblatt und Musterlösung mit Bewertungsschema) ausschließlich auf Basis des vom Dozenten bereitgestellten Materials. Nutze diesen Skill IMMER, wenn eine Probeklausur, Übungsklausur, Testklausur, Musterklausur, Klausursimulation oder ein Aufgabenblatt zur Prüfungsvorbereitung erstellt, erweitert, überarbeitet oder erneut gerendert werden soll — auch wenn nur "Klausur generieren", "Probeklausur für Modul X", "Aufgaben zum Üben", "Prüfungsvorbereitung", "noch eine Variante" oder "Aufgabe 3 ist zu leicht" gesagt wird und weder PDF noch Format ausdrücklich erwähnt werden. Enthält die Klausur Multiple-Choice-, Single-Choice-, Tabellen- oder Lückentextaufgaben, gilt dieser Skill auch für diese Teile. Ebenso nutzen, wenn aus Vorlesungsmaterial ein Wissensdestillat oder Aufgabenpool für spätere Klausuren aufgebaut werden soll.
---

# Klausurtrainer

Erzeugt aus Dozentenmaterial zwei PDFs: `*_Aufgabenblatt.pdf` und `*_Loesungen.pdf`.

**Kernprinzip:** Inhalt und Layout sind getrennt. Du schreibst ausschließlich eine
`klausur.json`. Das Layout macht `scripts/render_exam.py` und wird nie im Chat
erzeugt. Beide PDFs stammen aus derselben JSON und können daher nicht
auseinanderlaufen.

## Vorlage: generisch oder nach Altklausur

Das Erscheinungsbild der PDFs steuert eine Vorlage. Es gibt zwei Zustände je
Modul:

| Zustand | Wann | Wirkung |
|---|---|---|
| generisch | keine Altklausur vorhanden | Gestaltung nach dem Design System TUDa UI (Abschnitt "Gestaltung") |
| individuell | `vorlage_<MODULKUERZEL>.json` liegt neben der `klausur.json` | Layout, Schrift, Kopf- und Fußzeilen, Aufgabenmuster und Deckblatt der Altklausur |

**Einmaliges Umschalten.** Liefert der Nutzer eine echte Altklausur und
existiert für das Modul noch keine Vorlage:

```bash
python3 scripts/analyse_altklausur.py Altklausur.pdf --modul GPUM --out vorlage_GPUM.json --vorschau vorschau/
```

Danach die Vorschaubilder des Originals ansehen, eine Probeklausur mit der neuen
Vorlage rendern und beides nebeneinander vergleichen. Abweichungen im Profil von
Hand nachschärfen (Felder in `references/vorlage.md`). Die fertige Vorlage wird
neben den Klausurdateien des Moduls abgelegt und gehört in die Project
Knowledge. Ab dann nutzt der Renderer sie automatisch; `--vorlage generisch`
erzwingt die Standardvorlage.

Mehrere Altklausuren: die jüngste analysieren. Weichen ältere deutlich ab, dem
Nutzer das sagen, statt Stile zu mischen.

**Grenzen der Nachbildung, nicht verhandelbar:**

- Logos, Siegel und Wappen des Lehrstuhls oder der Universität werden nie
  übernommen, auch nicht auf Wunsch; das gilt auch für das Logo der TU
  Darmstadt. An ihrer Stelle steht das eigene Zeichen (Fünffingerturm).
- "Klausur" wird in Titel- und Kopfzeilen zu "Probeklausur" bzw. zur Variante.
- Der KI-Hinweis steht in jeder Vorlage auf dem Deckblatt und in jeder Fußzeile.
- Übernommen wird das Erscheinungsbild, nie der Wortlaut alter Aufgaben. Der
  Aufgabenstil wird über den Abschnitt "Prüfungsformat" im Destillat imitiert.

Je näher die Nachbildung am Original ist, desto wichtiger ist der Hinweis. Eine
Probeklausur, die mit einer echten verwechselt werden kann, ist ein Problem,
kein Qualitätsmerkmal.

## Grounding-Regeln (nicht verhandelbar)

0. Ist der Skill `wissensdestillat` installiert, wird nur mit einem Destillat
   gearbeitet, dessen `pruefprotokoll_<MODUL>.md` den Status BESTANDEN zeigt.
   Fehlt das Protokoll oder zeigt es NICHT BESTANDEN, wird zuerst das Destillat
   geprüft und korrigiert, dann erst generiert. Ohne diesen Skill entsteht das
   Destillat in Stufe 0; vor dem Generieren wird jeder Quellanker darin am
   Material nachgeprüft.
1. Inhalte stammen **ausschließlich** aus dem Material des Dozenten (Project
   Knowledge, hochgeladene Dateien, Volltext, Destillat). Musterlösungen und
   Wortlaut werden im Volltext am jeweiligen Anker nachgelesen, nicht aus dem
   Destillat rekonstruiert. Kein Weltwissen, keine
   Standarddefinitionen aus dem Training, keine Begriffe, die im Material nicht
   vorkommen.
2. Jede Teilaufgabe trägt ein `quelle`-Feld mit konkretem Anker
   (`"VL07, F23-29"`, `"Skript Kap. 4.2, S. 88"`). Ohne Beleg wird die Aufgabe
   **nicht erstellt**, sondern dem Nutzer als Lücke gemeldet.
3. Weicht die Definition des Dozenten von der gängigen Lehrbuchdefinition ab,
   gilt die des Dozenten. Formulierungen und Notation aus dem Material übernehmen.
4. Bei Unsicherheit: Aufgabe weglassen und nachfragen, nicht raten.

## Ablauf

Prüfe zuerst, in welcher Stufe der Nutzer steht. Existiert schon ein Destillat
oder eine `klausur.json`, springe direkt dorthin.

### Stufe 0 — Destillat (einmalig je Modul)

Nur wenn für das Modul noch kein Destillat existiert. Steht der Skill
`wissensdestillat` zur Verfügung, übernimmt er diese Stufe vollständig;
dann hier nicht selbst destillieren, sondern ihn nutzen. Andernfalls erzeuge
`destillat_<MODUL>.md` aus dem Rohmaterial: je Vorlesungseinheit die prüfbaren
Konzepte, Definitionen, Formeln, Beispiele und Abgrenzungen, jeweils mit
Quellanker. Kein Fließtext, kompakte Stichpunkte.

Struktur je Einheit:
```
## VL07 — Prozessmodellierung
**Quelle:** Folien 1-42
### Prüfbare Konzepte
- Begriff X: <Definition wie im Material> [F12]
- Verfahren Y: Schritte 1..n [F18-22]
### Formeln / Notation
### Beispiele aus der Vorlesung
### Vom Dozenten betonte Abgrenzungen
```

Das Destillat gehört danach in die Project Knowledge. Ab dann arbeitest du damit
statt mit den Roh-PDFs.

### Stufe 1 — Blueprint

Steht der Skill `coverage-map` zur Verfügung und existiert eine Karte für das
Modul, zuerst die Themenauswahl mit dessen Skript holen:

```bash
python3 scripts/coverage_plan.py coverage_<MODUL>.tsv --konzepte 12 --regeln regeln_<MODUL>.json
```

Die ausgegebenen Konzept-IDs und Quellanker gehen unverändert in den Blueprint.

Vor jeder Generierung erst ein Gerüst zur Freigabe, nie sofort die volle Klausur.
Pro Aufgabe nur: `id`, Thema, Aufgabentyp, Punkte, Quellanker, ein Satz zum
Inhalt. Themengewichtung an der Gewichtung im Material orientieren. Punktsumme
muss der Zielpunktzahl entsprechen. Blueprint als kurze Tabelle im Chat zeigen
und bestätigen lassen.

### Stufe 2 — Aufgaben ausformulieren

Erzeuge `klausur.json` (Schema: `references/schema.md`). Regeln:

- Aufgabenstil an Altklausuren/Übungen des Dozenten orientieren, sofern vorhanden.
- Punkte sind konsistent: Bewertungskriterien summieren auf die Teilaufgabenpunkte,
  Teilaufgaben auf die Aufgabe, Aufgaben auf `meta.gesamtpunkte`.
- Richtwert Bearbeitungszeit: etwa 1 Minute je Punkt.
- Musterlösung so ausführlich, dass damit korrigiert werden kann. Sie erscheint im
  Lösungs-PDF in vier Abschnitten: **Musterlösung** (die Antwort, die volle
  Punktzahl erhält), **Erläuterung** (nur wenn nötig), **Quelle**,
  **Bewertungsschema**.
- **Form der Musterlösung folgt der Form der Antwort.** Verlangt die Aufgabe
  mehrere getrennte Elemente (Aufzählung, Merkmale, Vor-/Nachteile, Schritte,
  Entitäten, Schwächen, Rechenschritte), steht jedes Element als eigener
  Stichpunkt: je Zeile `- ...` in `loesung`, gegebenenfalls nach einem kurzen
  Einleitungssatz. Eine zusammenhängende Definition oder Argumentation bleibt
  ein Textblock. Mischformen sind erlaubt (Definition als Absatz, danach
  Stichpunkte). Faustregel: Gibt es im Bewertungsschema je Element ein eigenes
  Kriterium, gehört je Element ein Stichpunkt in die Lösung. Dasselbe gilt für
  `erlaeuterung`.
- In Textantworten jeden punktegebenden Teilsatz markieren: `==Teilsatz==[2]`.
  Er erscheint blau und fett mit Punktzahl. Nur das markieren, was tatsächlich
  Punkte bringt, nicht ganze Absätze.
- Tabellen-, Zuordnungs- und Lückentextaufgaben: Lösungen als `[[...]]` in die
  Tabellenzellen bzw. in `lueckentext` schreiben. Das Aufgabenblatt zeigt leere
  Felder und gleich lange Lücken, die Musterlösung die ausgefüllte Fassung mit
  den Lösungen in Blau. `loesung` enthält dann nur, was darüber hinaus verlangt
  ist, etwa eine Begründung. Die markierten Punkte entsprechen
  den Kriterien im Bewertungsschema; ihre Summe darf die Teilaufgabe nicht
  übersteigen (der Validator prüft das).
- `erlaeuterung` nur schreiben, wenn die Lösung allein nicht nachvollziehbar ist:
  Rechenwege, Abgrenzungen, warum eine naheliegende Antwort falsch ist. Keine
  Wiederholung der Musterlösung in anderen Worten.
- Bewertungsschema in nachvollziehbaren Teilschritten, nicht "alles oder nichts".
- Bei umfangreichen Klausuren blockweise arbeiten: Aufgaben einzeln in die JSON
  schreiben (Python, `json.load` → anhängen → `json.dump`), statt die ganze Datei
  neu auszugeben.

### Multiple-Choice-Aufgaben in der Klausur

MC-Teilaufgaben folgen denselben Regeln wie der Skill `mc-fragen`. Sie werden
nie frei formuliert, sondern in dieser Reihenfolge erstellt:

1. **Parameter** aus der Projektanweisung: Antwortmöglichkeiten
   (`mc_optionen`, Standard 4) und richtige Antworten (`mc_richtige`, Standard 1).
   In `meta.mc_optionen` und `meta.mc_richtige` übernehmen.
2. **Positionen auslosen, bevor eine Frage geschrieben wird**, für alle
   MC-Teilaufgaben der Klausur auf einmal:
   ```bash
   python3 scripts/antwortpositionen.py --fragen <ANZAHL> --optionen 4 --richtige 1 --out positionen.json
   ```
   Die erste MC-Teilaufgabe der Klausur bekommt F1, die zweite F2 und so weiter.
   Die Ziehung ist bindend.
3. **Schreiben**: Kernaussage der richtigen Antwort festlegen, an die ausgeloste
   Position setzen, dann die Distraktoren. Glaubwürdige Distraktoren kommen aus
   dem Material: Nachbarbegriffe derselben Einheit, typische Denkfehler, richtige
   Aussagen zur falschen Frage, Vertauschungen, Ergebnisse konkreter
   Rechenfehler. Alle Optionen gleich lang (±20 %), gleicher Satzbau, gleicher
   Detailgrad. Keine Absolutwörter nur in Distraktoren, keine Sammeloptionen
   ("alle/keine der genannten"), keine Gegensatzpaare, kein Stichwort aus dem
   Fragestamm nur in der richtigen Antwort. Ist `mc-fragen` installiert, dessen
   `references/distraktoren.md` lesen.
4. **Felder** je MC-Teilaufgabe: `text` (Fragestamm), `optionen` als Liste aus
   `{"text", "richtig", "warum_falsch"}` in der ausgelosten Reihenfolge,
   `erklaerung` (warum die richtige Antwort richtig ist), `quelle`. Kein
   eigenes `bewertung`, `loesung` bleibt leer. Die Bewertungsregel gilt für alle
   MC-Fragen gemeinsam; weicht die Projektanweisung vom Standard ab (etwa
   Minuspunkte für falsche Kreuze), steht die Regel in `meta.mc_bewertung`.
5. **Prüfen**:
   ```bash
   python3 scripts/check_mc.py klausur.json --positionen positionen.json
   ```
   Befunde durch Umschreiben der Texte beheben, nie durch Verschieben der
   richtigen Antwort.

Das Aufgabenblatt zeigt je Option Buchstabe, Ankreuzfeld und Text. Die
Musterlösung zeigt zu Beginn der Aufgabe einmal das Bewertungsschema für alle
MC-Fragen samt Lösungsschlüssel, danach jede Frage wie im Aufgabenblatt mit den
richtigen Antworten blau angekreuzt, darunter Begründung (inklusive je
Distraktor ein Satz, warum er falsch ist) und Quelle.

Soll die gesamte Übung ein reiner Fragensatz sein (Fragebogen mit
Lösungstabelle statt Klausur), ist der Skill `mc-fragen` zuständig.

### Stufe 3 — Validierung

```bash
python3 scripts/validate_exam.py klausur.json
```

Enthält die Klausur MC-Teilaufgaben, zusätzlich `check_mc.py` (siehe oben).

`validate_exam.py` prüft deterministisch: Punktsummen auf allen Ebenen, eindeutige IDs, fehlende
Quellanker, fehlende Musterlösungen oder Bewertungsschemata, Zeit/Punkte-Verhältnis
und Themenverteilung. Erst bei Exitcode 0 rendern. Fehler in der JSON beheben,
nicht im PDF.

Danach ein kurzer inhaltlicher Grounding-Check: jede Aufgabe gegen ihren
Quellanker halten. Nicht belegbare Aussagen streichen oder korrigieren.

### Stufe 4 — Rendern

```bash
python3 scripts/render_exam.py klausur.json --out <Ausgabeordner>
```

Ausgabeordner ist der Ort, von dem aus Dateien an den Nutzer gehen (z. B.
`/mnt/user-data/outputs`, sonst das Arbeitsverzeichnis). Ohne `--out` nimmt das
Skript `/mnt/user-data/outputs`, falls es den Ordner gibt, sonst den aktuellen.
Optional `--nur aufgaben` oder `--nur loesung`, wenn nur eine Datei neu gebraucht
wird. Danach beide Dateien mit dem verfügbaren Datei-Werkzeug ausgeben (z. B.
`present_files`), Aufgabenblatt zuerst.

### Stufe 5 — Coverage Map fortschreiben

Gibt es eine Karte (Skill `coverage-map`), die fertige Klausur mit dessen Skript eintragen:

```bash
python3 scripts/coverage_record.py coverage_<MODUL>.tsv --quelle klausur.json --variante PK-B
```

Dafür trägt jede Aufgabe in `klausur.json` das Feld `konzepte` mit den IDs aus
der Planung. Dieser Schritt gehört fest zum Abschluss, sonst zählt die Klausur
beim nächsten Mal nicht mit.

## Korrekturwünsche

Nur das betroffene Objekt in der JSON ändern, dann Stufe 3 und 4 erneut.
Die Klausur nie neu generieren, wenn nur einzelne Aufgaben betroffen sind.
`klausur.json` bleibt die Quelle der Wahrheit und wird mit ausgeliefert, damit
spätere Sitzungen daran anknüpfen können.

## Deckblatt und Materialangaben

Das Deckblatt des Aufgabenblatts nennt unter "Erstellt auf Grundlage von", welche
Arten von Material in diese Probeklausur eingeflossen sind. Dafür vor dem
Rendern `meta.grundlagen` füllen, und zwar mit dem, was tatsächlich verwendet
wurde, nicht mit allem, was im Projekt liegt:

```json
"grundlagen": [
  {"art": "Vorlesungsfolien", "umfang": "VL01–VL12, WiSe 2026/27"},
  {"art": "Übungsblätter", "umfang": "Blatt 1–6 mit Musterlösungen"},
  {"art": "Altklausur", "umfang": "WS 2023/24 (Aufgabenstil)"},
  {"art": "Gedächtnisprotokoll", "umfang": "SoSe 2024, inoffiziell"}
]
```

Gedächtnisprotokolle sind keine Dozentenunterlagen. Sie werden immer als
"inoffiziell" gekennzeichnet, dienen nur als Hinweis auf Aufgabentypen und
Themenschwerpunkte, und keine Musterlösung stützt sich allein auf sie; fachliche
Aussagen werden am offiziellen Material belegt.

Fehlt `meta.grundlagen`, leitet der Renderer die Angabe aus den Quellankern ab
(VL → Vorlesungsfolien, UE → Übungen, AK → Altklausuren, GP → Gedächtnisprotokolle,
SK → Skript) und ergänzt eine Altklausur, die als Gestaltungsvorlage dient.

Die Musterlösung zeigt auf dem Deckblatt zusätzlich "Aufgaben im Überblick":
je Aufgabe Titel, Thema, die zugrunde liegenden Materialeinheiten und die
Punkte. Klarnamen der Einheiten über `meta.materialien`, etwa
`{"VL02": "Informationssysteme"}`.

Personalienfelder gibt es nur, wenn eine Vorlage sie verlangt, etwa bei der
Nachbildung einer Altklausur.

## KI-Hinweis (Pflicht)

Beide PDFs tragen den Hinweis, dass es sich um eine KI-generierte Probeklausur
handelt, die nicht vom Lehrstuhl gestellt wurde: als gerahmter Kasten mit rotem
Akzent auf dem Deckblatt und als Zeile mit Warnsymbol in der Fußzeile jeder
Seite. Der Kasten sieht in jeder Vorlage gleich aus, auch in nachgebildeten. Der Renderer setzt das
automatisch, es ist kein Feld in der JSON nötig.

Der Wortlaut lässt sich über `meta.ki_hinweis` (Kasten) und
`meta.ki_hinweis_fuss` (Fußzeile) anpassen, etwa um einen Modul- oder
Semesterbezug zu ergänzen. Entferne den Hinweis nicht und schwäche ihn nicht ab,
auch nicht auf Wunsch: die Blätter sehen offiziellen Klausuren bewusst ähnlich
und dürfen nicht mit einer echten Prüfung verwechselt werden.

## Gestaltung (TUDa UI)

Die generische Vorlage übersetzt das Design System TUDa UI auf Papier. Die
Werte stehen fest im Renderer (`TUDA` und `STANDARD` oben in
`scripts/render_exam.py`), nie in der JSON. Damit der Look ruhig und
prüfungstauglich bleibt, gelten diese Regeln auch bei späteren Änderungen:

- **Zeichen statt Logo.** Das Deckblatt trägt das Zeichen Fünffingerturm mit
  "Probeklausur" und einer zweiten Zeile (Standard "zur Selbstkontrolle",
  änderbar über `meta.byline`, etwa auf die Byline aus TUDa UI). Die Kopfzeile
  zeigt das Kleinformat des Zeichens, darüber steht auf jeder Seite der
  TU-Balken. Das Zeichen enthält keine Teile des TU-Logos.
- **Schrift.** Archivo für Text und Titel, JetBrains Mono für Kennungen
  (Modulkürzel, Quellanker), beide in `assets/fonts`. Zeichen, die Archivo
  fehlen (etwa griechische Buchstaben), setzt der Renderer selbst in eine
  Ersatzschrift.
- **Farbe hat feste Aufgaben.** Tinte für Text und Aufgabentitel. TU-Blau für
  Balken, Zeichen, Dachzeilen und die punktegebenden Antworten der
  Musterlösung. Rot nur für den KI-Hinweis, Hellblau nur für den Materialkasten,
  Grau für Beschriftungen, Linien und Tabellenköpfe.
- **Wenige Rundungen.** Abgerundet sind nur das Zeichen, die beiden
  Hinweiskästen und die Punkteübersicht. Ankreuzfelder, Punktekästen,
  Antwortfelder und Aufgabentabellen bleiben eckig. Aufgabentitel stehen
  schlicht in Tinte mit Linie darunter, ohne Reiter, Flächen oder große Ziffern.
- **Icons** im Linienstil von TUDa UI (24er-Raster, runde Enden), klein und grau
  an Kennzahlen und Lösungsabschnitten; das Warndreieck des KI-Hinweises rot.

## Antwortfelder

`meta.antwortraum_stil` steuert das Aufgabenblatt modulweise und überschreibt die
Vorlage:

- `"linien"` — liniert, für Fließtextantworten (Standard der generischen Vorlage)
- `"kasten"` — leerer Rahmen, für Skizzen, Modelle, Rechnungen
- `"raster"` — Rahmen mit Kästchenraster, für Rechenwege und Tabellen
- `"platz"` — freier Raum ohne Linien, wie in vielen Altklausuren
- `"keiner"` — keine Antwortfelder, wenn auf separatem Papier gearbeitet wird

Je Teilaufgabe überschreibbar über `antwortraum`, `antwortraum_zeilen`,
`antwortraum_hoehe_mm`. Ohne Angabe werden etwa 1,5 Zeilen je Punkt gesetzt.

## Diagramme

Standardmäßig textuelle Aufgaben. Existiert für das Modul ein eigener
Diagramm-Skill (z. B. BPMN oder EPK im Modul GPUM), erzeuge damit zwei Varianten
derselben Grafik — Aufgabenversion und Lösungsversion — und binde sie über das
`bild`-Feld ein (Aufgabenversion) bzw. über eine zweite Aufgabe in der
Lösungsansicht. PNG und JPG werden direkt eingebettet; SVG vorher konvertieren.

## Token-Regeln

- Rohmaterial genau einmal lesen (Stufe 0), danach nur noch das Destillat.
- Blueprint vor Ausformulierung, damit Korrekturen billig sind.
- JSON blockweise per Skript fortschreiben, nicht komplett in den Chat schreiben.
- Layout- und Prüflogik laufen als Skript, nicht als Modellausgabe.
- Lange Klausuren auf mehrere Chats aufteilen; der Blueprint hält sie zusammen.

## Dateien

- `scripts/render_exam.py` — JSON → zwei PDFs. Generische Vorlage im Stil von
  TUDa UI (Farben in `TUDA`, Icons, Zeichen) oben im Skript; eine Modulvorlage
  überschreibt einzelne Felder.
- `assets/fonts/` — Archivo und JetBrains Mono (SIL Open Font License) als
  statische Schnitte, glyphengleich mit den Schriften in TUDa UI
- `scripts/analyse_altklausur.py` — leitet aus einer Altklausur ein Vorlagenprofil ab
- `scripts/antwortpositionen.py` — Ziehung der richtigen Positionen für MC-Aufgaben
- `scripts/check_mc.py` — Muster- und Vollständigkeitsprüfung der MC-Aufgaben
- `references/vorlage.md` — alle Felder eines Vorlagenprofils
- `scripts/validate_exam.py` — deterministische Prüfungen.
- `references/schema.md` — vollständige Felddokumentation der `klausur.json`.
- `assets/beispiel_klausur.json` — lauffähiges Vollbeispiel als Vorlage.
