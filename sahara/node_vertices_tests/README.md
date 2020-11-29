Testcases for changes to CairoSVG's mechanism for path angles and markers.

Column explanation:
* **[Inkscape](https://inkscape.org/)**'s export-to-PNG function as a reference
* **Kozea**: current version of the [original CairoSVG library](https://github.com/Kozea/CairoSVG)
* **AgC/main**: this repo's [`main`](https://github.com/SilverCardioid/CairoSVG/) branch, my own work-in-progress fork of CairoSVG (currently functionally the same)
* **AgC/master**: the [`master`](https://github.com/SilverCardioid/CairoSVG/tree/master) branch, used for proposing minor changes to Kozea/CairoSVG and otherwise kept in sync with it

The rightmost images are visualisations of the `node.vertices` array, which is internally used for the marker positions and angles. For each vertex, the calculated direction of the outgoing path segment is green, and that of the incoming segment (pointing away from it) is purple. Grey means the two overlap.

## Still to fix in AgC/master
* [ ] Determining marker angles from vertex angles
* [ ] Elliptic curve angles
* [ ] Degenerate curve angles
* [ ] Closepath angles
* [ ] Start/end vs. mid markers

## Lines (L, H, V)
|     |     |     |
| :-: | :-: | :-: |
| ![](lines-ink.png)<br/>**Inkscape** | ![](kozea-2020-11-23/lines-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/lines-vertices.png)<br/>**Kozea (vertices)** |
| ![](lines-agc.png)<br/>**AgC/main**| ![](lines-kozea.png)<br/>**AgC/master**  | ![](lines-vertices.png)<br/>**AgC/master (vertices)** |

## Beziers (Q, C, T, S)
Includes a few degenerate curves with some or all control points coinciding with vertices.
|     |     |     |
| :-: | :-: | :-: |
| ![](beziers-ink.png)<br/>**Inkscape** | ![](kozea-2020-11-23/beziers-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/beziers-vertices.png)<br/>**Kozea (vertices)** |
| ![](beziers-agc.png)<br/>**AgC/main**| ![](beziers-kozea.png)<br/>**AgC/master**  | ![](beziers-vertices.png)<br/>**AgC/master (vertices)** |

## Circular arcs (A)
The central segment is an arc with zero radius, which according to [the SVG specification](https://www.w3.org/Graphics/SVG/1.1/implnote.html#ArcOutOfRangeParameters) should be treated as a straight line. Inkscape fails to render this (apparently painting a large solid black or white rectangle instead of the path), so the leftmost image was made with a version of the file that replaces the arc with an `L`.
|     |     |     |
| :-: | :-: | :-: |
| ![](arcs-ink-fix.png)<br/>**Inkscape** | ![](kozea-2020-11-23/arcs-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/arcs-vertices.png)<br/>**Kozea (vertices)** |
| ![](arcs-agc.png)<br/>**AgC/main**| ![](arcs-kozea.png)<br/>**AgC/master**  | ![](arcs-vertices.png)<br/>**AgC/master (vertices)** |

## Elliptic arcs (A)
|     |     |     |
| :-: | :-: | :-: |
| ![](elliptic-ink-fix.png)<br/>**Inkscape** | ![](kozea-2020-11-23/elliptic-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/elliptic-vertices.png)<br/>**Kozea (vertices)** |
| ![](elliptic-agc.png)<br/>**AgC/main**| ![](elliptic-kozea.png)<br/>**AgC/master**  | ![](elliptic-vertices.png)<br/>**AgC/master (vertices)** |
