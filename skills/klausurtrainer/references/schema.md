# Schema der klausur.json

Alle Inhalte der beiden PDFs stammen aus dieser Datei. Encoding UTF-8.

## Aufbau

```json
{
  "meta":     { ... },
  "aufgaben": [ { ... }, { ... } ]
}
```

## meta

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `modul` | ja | Vollständiger Modulname, erscheint als Titel |
| `variante` | ja | z. B. "Probeklausur A", erscheint in Kopfzeile |
| `gesamtpunkte` | ja | Muss der Summe der Aufgaben entsprechen (wird geprüft) |
| `modulkuerzel` | nein | Kürzel für Kopfzeile und Dateiname |
| `hochschule` | nein | Institution, auf dem Deckblatt oben rechts |
| `fachbereich` | nein | Zweite Zeile unter der Institution |
| `pruefungsdatum` | nein | Für Vorlagen, deren Titelzeilen ein Datum tragen |
| `vorlage` | nein | Pfad zu `vorlage_*.json` oder `"generisch"`; ohne Angabe automatisch |
| `dozent` | nein | |
| `semester` | nein | Dachzeile über dem Modultitel und Fußzeile |
| `bearbeitungszeit_min` | nein | Richtwert ca. 1 min je Punkt |
| `hilfsmittel` | nein | Freitext, z. B. "Taschenrechner, Formelsammlung" |
| `hinweise` | nein | Liste von Strings, erscheint als Kasten auf dem Deckblatt |
| `grundlagen` | empfohlen | Verwendete Materialarten fürs Deckblatt: Liste aus `{"art": ..., "umfang": ...}` oder `"Art: Umfang"`; ohne Angabe aus den Quellankern abgeleitet |
| `mc_bewertung` | nein | Bewertungsregel für alle MC-Fragen, falls abweichend vom Standard |
| `materialien` | nein | Klarnamen der Einheiten für die Aufgabenübersicht der Musterlösung, z. B. `{"VL02": "Informationssysteme"}` |
| `antwortraum_stil` | nein | `"linien"`, `"kasten"`, `"raster"`, `"platz"`, `"keiner"`; überschreibt die Vorlage |
| `byline` | nein | Zweite Zeile neben dem Zeichen auf dem Deckblatt; Standard "zur Selbstkontrolle", `""` lässt sie weg |
| `ki_hinweis` | nein | Ersetzt den Text im KI-Hinweiskasten auf dem Deckblatt |
| `ki_hinweis_fuss` | nein | Ersetzt die KI-Hinweiszeile in der Fußzeile |

Der KI-Hinweis erscheint immer, auf dem Deckblatt und in jeder Fußzeile. Es gibt
bewusst keinen Schalter zum Abschalten, nur die beiden Textfelder oben.

## aufgaben[]

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `id` | ja | Eindeutig, z. B. `"A1"`. Die Anzeige wird daraus abgeleitet |
| `punkte` | ja | Muss der Summe der Teilaufgaben entsprechen |
| `titel` | empfohlen | Erscheint hinter "Aufgabe n:" |
| `thema` | empfohlen | Für Punkteübersicht und Themenverteilungs-Report |
| `quelle` | ja* | Quellanker; kann auf Teilaufgabenebene überschrieben werden |
| `einleitung` | nein | Fallbeschreibung vor den Teilaufgaben |
| `tabelle` | nein | Tabelle auf Aufgabenebene (siehe unten) |
| `bild` | nein | Grafik auf Aufgabenebene |
| `konzepte` | nein | IDs aus der Coverage Map, für die Fortschreibung |
| `teilaufgaben` | nein | Fehlt sie, gelten `text`, `loesung`, `bewertung` direkt auf Aufgabenebene |

\* Pflicht entweder hier oder in jeder Teilaufgabe. Der Validator bricht sonst ab.

## teilaufgaben[]

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `nr` | empfohlen | `"a"`, `"b"`, … Leer lassen bei einteiligen Aufgaben |
| `punkte` | ja | |
| `text` | ja | Aufgabentext |
| `loesung` | ja* | Musterlösung, wie sie die volle Punktzahl erhält; nur im Lösungs-PDF. Punktegebende Teilsätze als `==Teilsatz==` oder mit Punkten `==Teilsatz==[2]` markieren (erscheinen blau und fett). Mehrteilige Antworten als Stichpunkte: jede Zeile, die mit `- ` beginnt (Zeilenumbruch `\n`), wird ein Aufzählungspunkt; übriger Text bleibt Absatz, Leerzeile trennt Absätze. Zusammenhängende Definitionen als ein Absatz. Gilt ebenso für `erlaeuterung`. *Darf leer sein, wenn Tabelle oder Lückentext die Lösung tragen |
| `lueckentext` | nein | Text mit Lücken `[[Lösung]]`. Aufgabenblatt: gleich lange leere Lücken. Musterlösung: ausgefüllter Text, Lösungen blau und fett |
| `erlaeuterung` | nein | Begründung bzw. Erläuterung der Musterlösung, nur wenn die Aufgabe eine braucht (Rechenweg, Abgrenzung, typischer Fehler) |
| `bewertung` | ja | Liste aus `{"kriterium": "...", "punkte": n}`, Summe = `punkte` |
| `quelle` | ja* | Quellanker, erscheint klein unter der Bewertungstabelle |
| `antwortraum` | nein | Überschreibt `meta.antwortraum_stil` |
| `antwortraum_zeilen` | nein | Bei `"linien"`; Standard ca. 1,5 Zeilen je Punkt |
| `antwortraum_hoehe_mm` | nein | Bei `"kasten"`; Standard 45 |
| `tabelle` | nein | Erscheint im Aufgabenblatt und im Lösungs-PDF |
| `tabelle_loesung` | nein | Ausgefüllte Fassung von `tabelle`; alle abweichenden Zellen gelten als Lösung. Einfacher: Lösungen direkt als `[[...]]` in die Zellen von `tabelle` schreiben |
| `bild` | nein | |

## tabelle

```json
{
  "header": ["System", "Ebene"],
  "zeilen": [["ERP-Buchungserfassung", ""], ["Kassensystem", ""]],
  "spaltenbreiten_mm": [90, 70]
}
```

`header` und `spaltenbreiten_mm` sind optional. Ohne Breitenangabe werden die
Spalten gleich verteilt. Leere Zellen ergeben ausfüllbare Felder.

### Multiple-Choice-Teilaufgaben

```json
{
  "nr": "a", "punkte": 2,
  "text": "Wie wird eine n:m-Beziehung in das Relationenmodell überführt?",
  "optionen": [
    {"text": "Durch einen Fremdschlüssel ...", "richtig": false, "warum_falsch": "..."},
    {"text": "Durch eine eigene Relation ...",  "richtig": true}
  ],
  "erklaerung": "Warum die richtige Antwort richtig ist.",
  "quelle": "VL05, F20-22",
  "loesung": ""
}
```

MC-Teilaufgaben brauchen kein eigenes `bewertung`. Die Musterlösung nennt zu
Beginn der Aufgabe einmal die Bewertungsregel für alle MC-Fragen und einen
Lösungsschlüssel. Standardregel: volle Punktzahl bei genau den richtigen
Kreuzen, sonst 0. Abweichende Regeln aus der Projektanweisung in
`meta.mc_bewertung` als Text.

Reihenfolge der Optionen = Reihenfolge im PDF (A, B, C, ...), also genau die
ausgeloste. Bei mehreren richtigen Antworten wird die Anzahl automatisch an die
Frage angehängt. `meta.mc_optionen` und `meta.mc_richtige` halten die Vorgaben
der Projektanweisung fest und werden von `check_mc.py` geprüft.

### Tabellen mit Lösungsfeldern

```json
"tabelle": {
  "header": ["System", "Ebene"],
  "zeilen": [["ERP-Buchungserfassung", "[[operativ]]"],
             ["Management-Cockpit", "[[strategisch]]"]]
}
```

Im Aufgabenblatt sind die `[[...]]`-Zellen leer. In der Musterlösung steht statt
der leeren Tabelle die ausgefüllte, die Lösungen blau und fett. Eine Begründung,
die die Aufgabe zusätzlich verlangt, gehört in `loesung` und erscheint unter der
Tabelle.

`[[...]]` funktioniert auch direkt im Aufgabentext, etwa für einzelne Lücken in
einem Satz.

## bild

```json
{ "pfad": "diagramme/A3.png", "breite_mm": 130 }
```

Auch als einfacher String möglich. PNG und JPG werden direkt eingebettet, SVG
muss vorher konvertiert werden. Fehlt die Datei, erscheint ein sichtbarer
Platzhalter statt eines Absturzes.

## Textformatierung

In allen Textfeldern erlaubt: `<b>`, `<i>`, `<u>`, `<sub>`, `<super>`, `<br/>`.
`**fett**` wird automatisch umgesetzt. Alles andere wird escaped, `<` und `&`
sind also gefahrlos verwendbar. Keine Unicode-Hoch- und Tiefstellungen
verwenden, stattdessen `<super>` und `<sub>`.

## Minimalbeispiel

```json
{
  "meta": { "modul": "Statistik I", "variante": "Probeklausur A", "gesamtpunkte": 5 },
  "aufgaben": [{
    "id": "A1", "titel": "Lagemaße", "thema": "Deskriptive Statistik", "punkte": 5,
    "teilaufgaben": [{
      "nr": "", "punkte": 5,
      "text": "Berechnen Sie Median und arithmetisches Mittel der Reihe 2, 4, 4, 9, 11.",
      "quelle": "VL03, F14",
      "loesung": "Median = 4. Arithmetisches Mittel = 30/5 = 6.",
      "bewertung": [
        { "kriterium": "Median korrekt", "punkte": 2 },
        { "kriterium": "Mittelwert korrekt berechnet", "punkte": 3 }
      ]
    }]
  }]
}
```

## Prüfregeln des Validators

Fehler (blockieren das Rendern):
- Pflichtfelder in `meta` fehlen
- doppelte Aufgaben-IDs oder doppelte Teilaufgaben-Nummern
- Punktsummen stimmen auf irgendeiner Ebene nicht
- fehlender Quellanker, fehlende Musterlösung, fehlendes Bewertungsschema
- Bewertungskriterium ohne Text, Aufgabe mit 0 Punkten

Warnungen (nur Hinweis):
- Zeit/Punkte-Verhältnis außerhalb 0,7 bis 1,6 min je Punkt
- sehr kurzer Aufgabentext
- hohe Punktzahl bei sehr knapper Musterlösung
- Aufgabe ohne `titel` und ohne `thema`
