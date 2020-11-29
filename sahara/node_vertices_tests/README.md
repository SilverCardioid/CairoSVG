Testcases for changes to CairoSVG's mechanism for path angles and markers.

Column explanation:
* *[Inkscape](https://inkscape.org/)*'s export-to-PNG function as a reference
* *Kozea*: this repo's [`master`](https://github.com/SilverCardioid/CairoSVG/tree/master) branch, used for proposing minor changes to [Kozea's original library](https://github.com/Kozea/CairoSVG) and otherwise kept in sync with it
* *AgC*: the [`main`](https://github.com/SilverCardioid/CairoSVG/) branch, my own work-in-progress fork (currently functionally the same)
* *vertices*: visualisation of the `node.vertices` array, which is internally used for the marker positions and angles

For each vertex in the rightmost images, the calculated direction of the outgoing path segment is green, and that of the incoming segment (pointing away from it) is purple. Grey means the two overlap.

== Lines (L, H, V) ==
| Inkscape | Kozea | AgC | vertices
| :------: | :---: | :-: | :------:
| ![](lines-ink.png) | ![](lines-kozea.png) | ![](lines-agc.png) | ![](lines-vertices.png)

== Beziers (Q, C, T, S) ==
Includes a few degenerate curves with some or all control points coinciding with vertices.
| Inkscape | Kozea | AgC | vertices
| :------: | :---: | :-: | :------:
| ![](beziers-ink.png) | ![](beziers-kozea.png) | ![](beziers-agc.png) | ![](beziers-vertices.png)

== Elliptical arcs (A) ==
The central segment is an arc with zero radius, which according to [the SVG specification](https://www.w3.org/Graphics/SVG/1.1/implnote.html#ArcOutOfRangeParameters) should be treated as a straight line. Inkscape fails to render this (apparently painting a large solid black or white rectangle instead of the path), so the leftmost image was made with a version of the file that replaces the arc with an `L`.
| Inkscape | Kozea | AgC | vertices
| :------: | :---: | :-: | :------:
| ![](arcs-ink-fix.png) | ![](arcs-kozea.png) | ![](arcs-agc.png) | ![](arcs-vertices.png)
