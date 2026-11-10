# Format der Kommentardateien

Die Kommentare stehen in einer oder mehreren Markdown-Dateien. `kommentar_bauen.py`
liest eine einzelne Datei oder alle `*.md` eines Ordners, sortiert nach Dateinamen.
Jede Folie darf genau einmal vorkommen, egal in welcher Datei.

## Inhalt

1. Kopfdaten
2. Folien und Schritte
3. Markierungsziele
4. Textformatierung
5. Zusammenfassung am Ende
6. Meldungen des Builds

## 1. Kopfdaten

Optional, am Anfang einer Datei (üblich: der ersten) zwischen zwei `---`-Zeilen:

```markdown
---
titel: Lineare Regression und Gradientenabstieg
veranstaltung: Maschinelles Lernen I
sprache: de
akzent: auto
marker: 6a
---
```

| Feld | Wirkung | Standard |
|---|---|---|
| `titel` | Titel der Vorlesung, erscheint in der Kopfzeile und in den PDF-Metadaten | Dateiname |
| `veranstaltung` | Modul oder Veranstaltung, steht in der Kopfzeile vor dem Titel | leer |
| `sprache` | `de` oder `en`: Silbentrennung und Anführungszeichen | `de` |
| `akzent` | TUDa-Farbcode (`0a`–`0d`, `1a`–`11d`) oder `auto` (aus den Folien erkannt) | `auto` |
| `marker` | Farbe aller Markierungen (Textmarker und Kästen), TUDa-Code | `6a` (Gelb) |
| `spalten` | `2`: Text läuft die linke Spalte hinab, die rechte nur bei Bedarf; `1`: eine Spalte über die volle Breite | `2` |
| `fusszeile` | Text links in der Fußzeile; den KI-Hinweis darin nicht entfernen | „Kommentierter Foliensatz · Erläuterungen KI-generiert, nicht vom Lehrstuhl geprüft“ |

Blasse Akzentfarben (`0a`, `5a`, `6a`, `6b`, `7a`) färben nur den Balken; Beschriftungen
werden dann automatisch schwarz, weil die TUDa-Regeln diese Farben für Text verbieten.

## 2. Folien und Schritte

```markdown
# Folie 7: Gradientenabstieg
Text der Gesamtansicht. Diese Seite zeigt die Folie unmarkiert.

## Die Update-Regel
@markiere: b3, b4
Text zum ersten Schritt.

## Das Höhenliniendiagramm
@rahmen: i1
Text zum zweiten Schritt.
```

- `# Folie N` oder `# Folie N: Titel` (auch `–`, `|`) beginnt Folie N. Der Titel
  erscheint als Überschrift über dem Kommentar und im Lesezeichen. Ohne Titel wird der
  aus der Folie erkannte genommen – der ist bei Formeln oder ungewöhnlichem Layout oft
  unbrauchbar, deshalb den Titel immer selbst angeben.
- Text direkt unter `# Folie N` ist der Kommentar der Gesamtansicht (erste Seite der Folie).
- Jede `## Überschrift` darunter erzeugt eine Schritt-Seite: dieselbe Folie, darauf
  markiert, was die `@`-Zeilen angeben, und darunter der Text des Schritts. Die
  Überschrift wird zum Titel der Seite („Schritt 2 von 4“ ergänzt das Layout selbst).
- Jeder Schritt braucht mindestens eine `@markiere:`- oder `@rahmen:`-Zeile und Text.
- Markierungen gibt es nur auf Schritt-Seiten; die Gesamtansicht bleibt immer unmarkiert.
- HTML-Kommentare `<!-- … -->` werden ignoriert (für eigene Notizen).

## 3. Markierungsziele

Eine `@`-Zeile kann mehrere Ziele enthalten, getrennt durch Komma oder Semikolon;
mehrere `@`-Zeilen in einem Schritt sind ebenfalls erlaubt.

| Ziel | Bedeutung | Beispiel |
|---|---|---|
| `bN` | Textblock N der Folie (alle Zeilen) | `b3` |
| `bN.M` | Zeile M in Block N | `b4.2` |
| `bN-bK` | Blöcke N bis K | `b3-b5` |
| `bN.M-K` | Zeilen M bis K in Block N | `b4.2-4` |
| `iN` | Bild N | `i1` |
| `gN` | Grafik N (zusammenhängende Vektorzeichnung, z. B. Diagramm) | `g2` |
| `text="…"` | jede Stelle, an der der Text vorkommt | `text="Lernrate"` |
| `text="…"#K` | nur der K-te Treffer (von oben nach unten) | `text="w"#2` |
| `bereich=x0,y0,x1,y1` | Rechteck in Anteilen der Folienbreite und -höhe (0…1) | `bereich=0.52,0.30,0.95,0.80` |

Die IDs stehen in `arbeit/folien_text.md` vor jedem Textblock (mehrzeilige Blöcke mit
ihren Zeilennummern in eckigen Klammern) und als farbige Kästchen auf den Lagekarten
`arbeit/bilder/karte_NNN.png`. Das Raster der Lagekarte ist in Zehnteln beschriftet;
daraus liest man `bereich=`-Werte ab.

**Stil** – beides ist gelb wie ein Textmarker:
- `@markiere:` – Textmarker (TUDa-Gelb, multiplizierend, der Text bleibt schwarz
  lesbar). Bei Text wird jede Zeile einzeln markiert, wie mit einem echten Marker.
- `@rahmen:` – gelber Kasten um das ganze Element: hellgelbe Fläche, Kante im
  kräftigeren Gelb derselben Farbfamilie. Für Bilder, Diagramme, Tabellen, Formelblöcke
  und alles, was großflächig ist.

**Wahl des Ziels:**
- Text: lieber `bN.M` oder `text="…"` als einen ganzen Block, wenn nur ein Teil gemeint
  ist. Die Markierung soll genau das zeigen, worüber der Schritt spricht.
- Formeln sind im Folientext oft in viele Blöcke zerlegt (`b2`, `b3`, `b4` …). Dann
  einen Rahmen um alle Teile legen – `@rahmen: b3-b5` umschließt die Blöcke 3 bis 5
  gemeinsam – oder `@rahmen: bereich=…`, statt Bruchstücke zu markieren.
- Diagramme: `gN` oder `iN`, wenn die Lagekarte das Element sauber umfasst; sonst
  `bereich=`. Teile eines Diagramms (eine Achse, ein Pfad) über `bereich=` oder über die
  Beschriftung per `text="…"`.
- `bereich=` muss nicht millimetergenau sein: Der Build lässt den Bereich auf die
  Folienelemente einrasten. Was zu mindestens 40 % drinliegt, wird ganz aufgenommen;
  nur angeschnittene Beschriftungen schiebt eine Kante heraus, damit kein Rahmen durch
  Schrift läuft. Das Ergebnis trotzdem in der Vorschau ansehen.
- Aus PowerPoint exportierte Folien enthalten Formen oft als Bilder (viele `i…` auf der
  Lagekarte). Für Teile eines Diagramms ist `bereich=` dann meist einfacher als Bild-IDs.
- Folien ohne Textebene (Scans): nur `bereich=` funktioniert.
- `text="…"` findet keine Treffer, wenn die Folie den Text anders kodiert (Ligaturen,
  zusammengesetzte Umlaute aus alten LaTeX-Schriften) – dann ID oder `bereich=` nehmen.
- Der Build meldet Ziele mit mehreren Treffern; dann mit `#K` eingrenzen, falls nur
  eine Stelle gemeint ist.

## 4. Textformatierung

Eine kleine Markdown-Teilmenge, die zum Layout passt:

| Schreibweise | Ergebnis |
|---|---|
| Leerzeile | neuer Absatz |
| `**Begriff**` | fett – für Fachbegriffe an der Stelle, wo sie erklärt werden |
| `*Wort*` oder `_Wort_` | kursiv – für Betonung, englische Originalbegriffe |
| `` `code` `` | Festbreitenschrift |
| `- Punkt` / `1. Punkt` | Liste (eingerückt mit zwei Leerzeichen: zweite Ebene) |
| `### Zwischenüberschrift` | kleine Überschrift innerhalb eines langen Kommentars |
| `> **Merke:** …` | Kernaussage mit Akzentlinie (sparsam: höchstens eine je Folie) |
| `$x_i^2$` | Formel im Fließtext (LaTeX-Syntax von matplotlib-mathtext) |
| `$$J(w) = \frac{1}{2m}\sum_i r_i^2$$` | abgesetzte Formel, zentriert, eigene Zeile |

- Einfache Symbole direkt als Unicode schreiben (η, θ, ∑, ≤, →, x²) – das liest sich im
  Fließtext am besten. `$…$` für alles mit Indizes, Brüchen, Akzenten oder Fettdruck.
- Inline-Formeln klein halten. Brüche, Summen mit Grenzen und Matrizen als abgesetzte
  Formel (`$$…$$`), sonst vergrößert sich der Zeilenabstand.
- mathtext kennt die gängigen LaTeX-Befehle (`\frac`, `\sum`, `\partial`, `\nabla`,
  `\mathbf`, `\hat`, `\leftarrow`, `\mathbb{R}` …), aber keine Umgebungen wie `align`
  oder `matrix`. Eine fehlerhafte Formel bricht den Build mit Meldung ab.
- Anführungszeichen, Gedankenstriche und Auslassungspunkte werden typografisch gesetzt:
  `"Lernen"` → „Lernen“ (bei `sprache: de`), ` - ` → ` – `, `...` → `…`.
- Kein HTML, keine Tabellen, keine Bilder im Kommentar: Die Folie ist das Bild.
- Der Text steht unter der Folie und läuft die linke Spalte (gut 8,5 cm breit, TUDa:
  Zeilen höchstens 90 mm) bis zum Seitenende hinab. Erst wenn sie voll ist, geht es oben
  in der rechten Spalte weiter. Eine Spalte fasst bei 16:9-Folien etwa 170, bei
  4:3-Folien etwa 150 Wörter, die ganze Seite also gut das Doppelte.

## 5. Zusammenfassung am Ende

Nach der letzten Folie folgt genau ein Abschnitt `# Zusammenfassung`. Er wird zu einer
eigenen Seite ohne Folie am Ende des PDFs und ist Pflicht (fehlt er, bricht der Build
ab, außer mit `--entwurf`). Er bleibt kurz – eine Seite:

```markdown
# Zusammenfassung
Drei bis fünf Sätze: Worum ging es in der Vorlesung, welche Frage wurde beantwortet,
und wie hängen die Teile zusammen?

## Takeaways
- vier bis sieben Kernaussagen, je ein Satz, die man nach der Vorlesung wissen sollte

## Kernbegriffe
- **Begriff**: Erklärung in einem Satz (Folie 4)
- **Weiterer Begriff**: … (Folie 7)
```

- `## Takeaways` und `## Kernbegriffe` sind hier Zwischenüberschriften, keine Schritte.
- Kurzfassung und Takeaways stehen links, die Kernbegriffe beginnen die rechte Spalte.
- Kernbegriffe: die 6–12 wichtigsten Begriffe der Vorlesung, jeweils mit der Folie, auf
  der sie eingeführt werden. Grundlage ist die Begriffsliste `arbeit/begriffe.md`.
- Ein anderer Titel als „Das Wichtigste in Kürze“: `# Zusammenfassung: Titel`.

## 6. Meldungen des Builds

| Meldung | Ursache und Abhilfe |
|---|---|
| „Ohne Kommentar: Folie …“ | Jede Folie braucht einen Abschnitt `# Folie N`, auch Aufbaustufen und Titel |
| „Folie N ist doppelt kommentiert“ | Abschnitt kommt in zwei Dateien vor; einen entfernen |
| „bN gibt es auf dieser Folie nicht“ | ID aus `folien_text.md` der richtigen Folie nehmen |
| „text=… kommt auf der Folie nicht vor“ | Schreibweise prüfen (Groß/klein egal), sonst ID oder `bereich=` |
| „Schritt … hat keine Markierung“ | `@markiere:` oder `@rahmen:` direkt unter die `##`-Überschrift |
| „Markierungen gehören in einen Schritt“ | `@`-Zeile steht in der Gesamtansicht; einen `## Schritt` darüber anlegen |
| „ACHTUNG Überlauf“ | Kommentar zu lang für eine Seite: kürzen oder auf Schritte verteilen |
| „Formel nicht darstellbar“ | mathtext-Syntax prüfen, ggf. als Unicode schreiben |
| „Zusammenfassung fehlt“ | Abschnitt `# Zusammenfassung` am Ende ergänzen (Abschnitt 5) |
| „nur N Zeile(n) in der rechten Spalte“ | Kommentar knapp zu lang für eine Spalte: ein, zwei Sätze kürzen |
| „auf mehreren Folien fett …“ | Prüfen, ob ein Begriff mehrfach erklärt wird; nur beim ersten Auftreten erklären |
| „Zusammenfassung: 2 Seite(n)“ | Zusammenfassung auf eine Seite kürzen |
