# Vorlagenprofil (vorlage_&lt;MODULKUERZEL&gt;.json)

Ein Profil überschreibt einzelne Felder der generischen Vorlage. Was fehlt,
bleibt generisch. `analyse_altklausur.py` erzeugt einen Vorschlag; jedes Feld
lässt sich danach von Hand anpassen.

## Seite und Schrift

| Feld | Werte | Bedeutung |
|---|---|---|
| `gestaltung` | `schlicht`, `tuda` | Profile nutzen `schlicht` (Nachbildung); `tuda` ist die generische Gestaltung nach TUDa UI |
| `rand_mm` | `[l, r, o, u]` | Seitenränder in mm |
| `schrift_text` | `archivo`, `caladea`, `carlito`, `freeserif`, `freesans`, `dejavuserif`, `dejavusans` | Fließtext |
| `schrift_titel` | wie oben | Titel und Aufgabenüberschriften |
| `schrift_hilfe` | wie oben | Kopf-/Fußzeile, Tabellen, Beschriftungen |
| `groesse_text` | pt | Fließtext |
| `groesse_aufgabe` | pt | Aufgabenüberschrift |
| `groesse_titel` | pt | größte Titelzeile des Deckblatts |
| `groesse_kopf` | pt | Kopfzeile |
| `tinte`, `akzent`, `grau`, `haarlinie`, `flaeche` | Hex | Farben |

Zuordnung der Originalschriften: Times und verwandte → `freeserif`; Arial,
Helvetica → `freesans`; Calibri, Frutiger, Myriad, Segoe → `carlito`; Cambria,
Charter, Palatino, Garamond, Computer Modern und andere Serifen → `caladea`.

## Kopf, Fuß, Aufgaben

| Feld | Beispiel | Bedeutung |
|---|---|---|
| `kopfzeile.links` / `.rechts` | `"Probeklausur {modul}"` | Platzhalter siehe unten |
| `fusszeile.links` / `.rechts` | `"Seite {seite} von {seiten}"` | die Mitte ist dem KI-Hinweis vorbehalten |
| `kopflinie` | `haar`, `kraeftig`, `keine` | Linie unter der Kopfzeile |
| `aufgabe_titel` | `"Aufgabe {nr}: {titel} ({punkte} Punkte)"` | mit Titel |
| `aufgabe_titel_ohne` | `"Aufgabe {nr} ({punkte} Punkte)"` | ohne Titel |
| `aufgabe_punkte` | `"{punkte} Punkte"` oder `""` | rechts neben der Überschrift, entfällt wenn `{punkte}` im Titel steht |
| `aufgabe_linie` | `true`/`false` | Linie unter der Aufgabenüberschrift |
| `punktekasten` | `true`/`false` | Kästchen für erreichte Punkte |
| `teilaufgabe_format` | `"({nr})"`, `"{nr})"`, `"{nr}."` | Kennzeichnung |
| `teilpunkte_format` | `"({punkte} P.)"` | Punkte je Teilaufgabe |
| `teilpunkte_position` | `rechts`, `inline` | am Rand oder am Ende des Aufgabentexts |
| `neue_seite_je_aufgabe` | `true`/`false` | Seitenumbruch vor jeder Aufgabe |
| `antwortraum_stil` | `linien`, `kasten`, `raster`, `platz`, `keiner` | Standard des Moduls |
| `symbole` | `true`/`false` | Symbole an Überschriften (KI-Hinweis behält seines immer) |
| `logo` | `eigen`, `keins` | eigenes Zeichen (Fünffingerturm); fremde Logos gibt es nicht |
| `logo_mm` | mm | Größe des Zeichens; in Nachbildungen steht es freistehend in Tinte |
| `markenbalken` | `true`/`false` | TU-Balken oben auf jeder Seite (nur `tuda`) |
| `zeichen_name`, `zeichen_zeile` | Text | Name und zweite Zeile neben dem Zeichen auf dem Deckblatt (nur `tuda`; `meta.byline` hat Vorrang) |

## Deckblatt (`deckblatt.*`)

| Feld | Werte | Bedeutung |
|---|---|---|
| `ausrichtung` | `links`, `zentriert` | |
| `titelzeilen` | Liste | leer = Standardaufbau; sonst Zeilen mit Platzhaltern, erste groß, zweite halbgroß |
| `personalien` | Liste | Feldbeschriftungen; generisch leer |
| `grundlagen` | `true`/`false` | Block "Erstellt auf Grundlage von" auf dem Deckblatt; Standard an |
| `personalien_stil` | `unterzeile`, `zeile` | Beschriftung unter der Linie oder links davon |
| `punktetabelle` | `horizontal`, `vertikal`, `keine` | |
| `punktetabelle_titel` | Text, `""` oder weglassen | Überschrift über der Tabelle |
| `punktetabelle_zeilen` | `["Punkte", "erreicht"]` | Zeilenbeschriftungen der horizontalen Tabelle |
| `hinweise_stil` | `nummeriert`, `punkte` | |
| `hinweise_titel` | Text | |
| `hinweise_ausrichtung` | `links`, `zentriert` | Überschrift der Hinweise |
| `eckdaten` | `true`/`false` | Block mit Zeit, Punkten, Aufgaben, Hilfsmitteln |
| `linie` | `true`/`false` | Doppellinie unter dem Titel |
| `institution` | `true`/`false` | Hochschule und Fachbereich oben |
| `variante_zeile` | `true`/`false` | eigene Zeile mit der Variante |

## Platzhalter

`{modul}`, `{modulkuerzel}`, `{variante}`, `{semester}`, `{hochschule}`,
`{fachbereich}`, `{dozent}`, `{pruefungsdatum}`, in Kopf- und Fußzeile
zusätzlich `{seite}` und `{seiten}`, in Aufgabenmustern `{nr}`, `{titel}`,
`{punkte}`. Leere Platzhalter werden samt verwaister Trennzeichen entfernt.

## Was die Analyse automatisch entschärft

- `Klausur`, `Prüfung`, `Exam` in Kopf- und Titelzeilen → `Probeklausur`
- eine Titelzeile, die nur "Klausur" lautete → `{variante}`
- Semesterangaben → `{semester}`, Datumsangaben → `{pruefungsdatum}`
- der erkannte Modulname → `{modul}`
- Bilder aus dem Original werden nicht gelesen und nicht übernommen
