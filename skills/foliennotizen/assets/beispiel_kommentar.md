---
titel: Lineare Regression und Gradientenabstieg
veranstaltung: Maschinelles Lernen I · VL 4
sprache: de
---

# Folie 1: Lineare Regression und Gradientenabstieg
Diese Vorlesung führt das einfachste Lernverfahren für Zahlenwerte ein, die lineare Regression, und den Gradientenabstieg – das Verfahren, mit dem sich nicht nur dieses, sondern fast jedes Modell trainieren lässt.

# Folie 2: Gliederung
Der rote Faden: ein Modell festlegen, seinen Fehler messen und diesen Fehler schrittweise verkleinern. Der Kern der Vorlesung ist der Gradientenabstieg (Punkt 4).

# Folie 3: Motivation: Mietpreise vorhersagen
Das Beispiel zieht sich durch die ganze Vorlesung: Aus der Wohnfläche soll die Kaltmiete vorhergesagt werden.

Die Daten sind $m$ Paare $(x^{(i)}, y^{(i)})$ – das hochgestellte $(i)$ ist kein Exponent, sondern die Nummer des Beispiels. $x$ ist das **Merkmal** (die Eingabe), $y$ der **Zielwert**. Gesucht ist eine Funktion $h$ mit $h(x) \approx y$; nur ungefähr, weil die Miete auch von Lage und Zustand abhängt.

**Überwachtes Lernen** heißt, dass die Trainingsdaten die richtigen Antworten bereits enthalten. **Regression** heißt, dass die Antwort eine Zahl ist und keine Kategorie – das wäre Klassifikation.

Im Streudiagramm ist jeder Punkt eine Wohnung. Die Punkte streuen um eine steigende Linie; die rote Gerade ist das Modell, das wir lernen wollen. Die kurzen gestrichelten Linien zeigen, wie weit einzelne Wohnungen von der Geraden abweichen – genau diese Abstände werden ab Folie 5 zum Fehlermaß.

# Folie 4: Das lineare Modell
Jetzt legen wir fest, wie $h$ aussieht: eine Gerade. Das ist die einfachste denkbare Wahl und trotzdem ein wichtiger Baustein – auch neuronale Netze bestehen aus vielen solchen linearen Teilen.

Die **Hypothese** $h_w(x) = w_0 + w_1 x$ hängt von den Parametern ab: Jede Wahl von $w_0$ und $w_1$ ergibt eine andere Gerade, und Lernen heißt hier, eine gute davon auszuwählen.

- $w_0$, der **Achsenabschnitt** (*bias*), ist die Miete bei 0 m² – eine Art Grundpreis.
- $w_1$, die Steigung oder das **Gewicht**, sagt, wie viel Euro jeder zusätzliche Quadratmeter kostet.

Bei mehreren Merkmalen wie Fläche, Baujahr und Lage fasst man Merkmale und Gewichte zu Vektoren zusammen. Der Kniff $x_0 = 1$ macht den Achsenabschnitt zu einem gewöhnlichen Gewicht, sodass das Modell kompakt als Skalarprodukt dasteht:

$$h_{\mathbf{w}}(\mathbf{x}) = w_0 \cdot 1 + w_1 x_1 + \dots + w_n x_n = \mathbf{w}^\top \mathbf{x}$$

Das **Lernproblem** im Kasten bleibt noch vage: Was heißt „möglichst nahe“? Das macht die nächste Folie präzise.

# Folie 5: Verlustfunktion: Mittlerer quadratischer Fehler
Um Geraden vergleichen zu können, brauchen wir eine Zahl, die misst, wie schlecht eine Gerade zu den Daten passt: die **Verlustfunktion** $J(w)$. Die Folie baut sich in drei Stufen auf.

Von innen nach außen gelesen: Für jedes Beispiel bilden wir die Differenz aus Vorhersage und echtem Wert, das **Residuum** $r^{(i)}$ – im Streudiagramm von Folie 3 der senkrechte Abstand zwischen Punkt und Gerade. Die Residuen werden quadriert, über alle $m$ Beispiele summiert und durch $2m$ geteilt. Das ergibt einen Mittelwert; das zusätzliche ½ erklärt Stufe 3.

Wichtig ist, wovon $J$ abhängt: von $w$, nicht von $x$. Die Daten liegen fest, verändern können wir nur die Parameter. Gesucht ist das $w$ mit dem kleinsten $J$.

# Folie 6: Verlustfunktion: Mittlerer quadratischer Fehler
Neu ist die Begründung für das Quadrat. Ohne Quadrat höben sich positive und negative Residuen auf: Eine Gerade, die die Hälfte der Wohnungen um 100 € über- und die andere Hälfte um 100 € unterschätzt, hätte den Fehler null.

Das Quadrat macht alle Beiträge positiv und gewichtet große Fehler überproportional – ein Residuum von 10 zählt 100, eines von 2 nur 4. Die Kehrseite: Einzelne Ausreißer können die Gerade stark zu sich ziehen.

# Folie 7: Verlustfunktion: Mittlerer quadratischer Fehler
Der Faktor ½ ist reine Bequemlichkeit: Beim Ableiten des Quadrats entsteht eine 2, die sich wegkürzt. Die Lage des Minimums ändert er nicht.

Wichtiger ist die letzte Zeile. **Konvex** heißt anschaulich: Die Fehlerfläche ist eine Schüssel ohne Nebentäler. Jedes lokale Minimum ist dann auch das globale – wer immer bergab geht, landet zwangsläufig dort. Genau das nutzt der Gradientenabstieg auf der nächsten Folie.

> **Merke:** $J(w)$ misst den mittleren quadratischen Abstand zwischen Gerade und Daten; die beste Gerade liegt am tiefsten Punkt dieser Schüssel.

# Folie 8: Gradientenabstieg
Der **Gradientenabstieg** findet das Minimum von $J$ schrittweise. Er schaut nur auf die Steigung an der aktuellen Stelle und geht ein Stück bergab – wie jemand, der im Nebel mit dem Fuß ertastet, wo der Hang abfällt, und dann einen Schritt in diese Richtung macht. Links steht die Rechenvorschrift, rechts sieht man das Verfahren bei der Arbeit.

## Die Update-Regel
@rahmen: b3-b5
@markiere: b6-b9
Die partielle Ableitung $\partial J / \partial w_j$ gibt an, wie stark $J$ steigt, wenn man nur $w_j$ etwas vergrößert. Zusammen bilden die Ableitungen den **Gradienten** $\nabla J$, der in Richtung des steilsten Anstiegs zeigt. Deshalb das Minuszeichen: Wir gehen in die Gegenrichtung, also bergab.

Die **Lernrate** $\alpha$ bestimmt die Schrittweite und muss positiv sein. Abgebrochen wird, wenn $\|\nabla J\| < \varepsilon$ ist: Am Minimum ist der Gradient null, und ist er fast null, ändert sich kaum noch etwas.

„Für alle $j$ gleichzeitig“ heißt: erst alle Ableitungen mit den alten Werten berechnen, dann alle Parameter auf einmal ändern.

## Das Höhenliniendiagramm
@rahmen: i1
Das Diagramm zeigt $J$ von oben wie eine Wanderkarte. Die Achsen sind $w_0$ und $w_1$, jeder Punkt ist also eine Gerade. Die Ellipsen sind **Höhenlinien** gleichen Fehlers, der Stern ist das Minimum.

Der rote Pfad zeigt zwei typische Effekte: Er läuft zuerst fast senkrecht nach unten, weil $J$ in $w_1$-Richtung steiler ist. Und die Schritte werden kürzer, obwohl $\alpha$ gleich bleibt – die Schrittweite ist $\alpha$ mal Gradient, und der Gradient schrumpft zum Minimum hin.

# Folie 9: Lernrate und Konvergenz
Die Tabelle zeigt, was die Wahl der Lernrate bewirkt:

- **Zu klein:** Es geht zuverlässig bergab, aber so langsam, dass man unnötig viele Iterationen braucht.
- **Passend:** $J$ sinkt in jedem Schritt deutlich; das Verfahren **konvergiert**, nähert sich also dem Minimum.
- **Zu groß:** Man springt über das Tal hinweg auf den gegenüberliegenden Hang. Landet man dort höher als vorher, schaukelt sich das auf – das Verfahren **divergiert**, $J$ wächst immer weiter.

In der Praxis probiert man einige Werte aus und beobachtet, ob $J$ von Iteration zu Iteration sinkt.

Das Ablaufdiagramm darunter ist der vollständige Algorithmus: Startwerte wählen, dann Gradient berechnen und Parameter aktualisieren, bis das Abbruchkriterium von Folie 8 greift.

# Folie 10: Zusammenfassung
Die vier Punkte bilden das vollständige Rezept: ein Modell (Folie 4), ein Maß für seinen Fehler (Folien 5–7), ein Verfahren, das diesen Fehler minimiert (Folie 8), und dessen wichtigste Stellschraube (Folie 9). Dieses Schema aus Modell, Verlustfunktion und Optimierung kehrt bei fast allen Lernverfahren wieder.

Nächste Woche folgen die **Normalengleichung**, die das Minimum bei linearer Regression direkt in einem Rechenschritt liefert, und die **Regularisierung**, die verhindert, dass sich ein Modell zu eng an die Trainingsdaten anpasst.

# Zusammenfassung
Lineare Regression sagt einen Zahlenwert als lineare Funktion der Merkmale voraus. Welche Gerade am besten passt, entscheidet die Verlustfunktion, der mittlere quadratische Fehler. Weil diese für lineare Modelle konvex ist, findet der Gradientenabstieg ihr Minimum zuverlässig, indem er Schritt für Schritt gegen den Gradienten läuft. Ob und wie schnell das gelingt, steuert die Lernrate.

## Takeaways
- Lernen heißt hier: unter allen Geraden diejenige mit dem kleinsten Fehler auswählen.
- Der quadratische Fehler bestraft große Abweichungen überproportional und reagiert deshalb empfindlich auf Ausreißer.
- Konvexität garantiert: Wer immer bergab geht, landet im globalen Minimum.
- Der Gradient zeigt bergauf; jeder Schritt geht deshalb in die Gegenrichtung.
- Eine zu große Lernrate lässt das Verfahren divergieren, eine zu kleine macht es unnötig langsam.
- Modell, Verlustfunktion und Optimierung bilden das Grundschema fast aller Lernverfahren.

## Kernbegriffe
- **Überwachtes Lernen**: Lernen aus Beispielen, deren richtige Antwort bekannt ist (Folie 3)
- **Regression**: Vorhersage eines Zahlenwerts statt einer Kategorie (Folie 3)
- **Hypothese**: die Modellfunktion $h_w$ mit den Parametern $w$ (Folie 4)
- **Verlustfunktion**: misst den mittleren quadratischen Fehler einer Parameterwahl (Folie 5)
- **Residuum**: Differenz zwischen Vorhersage und echtem Wert (Folie 5)
- **Konvex**: schüsselförmig; jedes lokale Minimum ist zugleich global (Folie 7)
- **Gradient**: Vektor der partiellen Ableitungen, zeigt zum steilsten Anstieg (Folie 8)
- **Lernrate**: Schrittweite $\alpha$ des Gradientenabstiegs (Folie 8)
- **Konvergenz, Divergenz**: Annäherung an das Minimum bzw. unbegrenztes Anwachsen von $J$ (Folie 9)
