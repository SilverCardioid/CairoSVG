Testcases for changes to CairoSVG's mechanism for path angles and markers.

Column explanation:
* **[Inkscape](https://inkscape.org/)**'s export-to-PNG function as a reference
* **Kozea**: current version of the [original CairoSVG library](https://github.com/Kozea/CairoSVG)
* **AgC/main**: this repo's [`main`](https://github.com/SilverCardioid/CairoSVG/) branch, my own work-in-progress fork of CairoSVG (currently functionally the same)
* **AgC/master**: the [`master`](https://github.com/SilverCardioid/CairoSVG/tree/master) branch, used for proposing minor changes to Kozea/CairoSVG and otherwise kept in sync with it

The rightmost images are visualisations of the `node.vertices` array, which is internally used for the marker positions and angles. For each vertex, the calculated direction of the outgoing path segment is green, and that of the incoming segment (pointing away from it) is purple. Grey means the two overlap.

## Lines
|     |     |     |
| :-: | :-: | :-: |
| ![](lines-ink.png)<br/>**Inkscape** | ![](kozea-2020-11-23/lines-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/lines-vertices.png)<br/>**Kozea (vertices)** |
| ![](lines-agc.png)<br/>**AgC/main**| ![](lines-kozea.png)<br/>**AgC/master**  | ![](lines-vertices.png)<br/>**AgC/master (vertices)** |

## Beziers
This test file includes a few degenerate curves, of which some or all control points coincide with vertices. In the current Kozea version, they result in a mathematically undefined `math.atan2(0,0)` (although that function returns an angle of zero degrees, hence all the arrows to the right in Kozea/vertices). The newer version fixes this by noting that the angles correspond to those of the lower-degree Bezier created by removing those control points. The extreme case, a zero-length segment (including those made with `L` or `A`), does not give correct angles yet.
|     |     |     |
| :-: | :-: | :-: |
| ![](beziers-ink.png)<br/>**Inkscape** | ![](kozea-2020-11-23/beziers-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/beziers-vertices.png)<br/>**Kozea (vertices)** |
| ![](beziers-agc.png)<br/>**AgC/main**| ![](beziers-kozea.png)<br/>**AgC/master**  | ![](beziers-vertices.png)<br/>**AgC/master (vertices)** |

## Circular arcs
In the two arc test files, the central segments of each sub-path are arcs with zero radius, which according to [the SVG specification](https://www.w3.org/Graphics/SVG/1.1/implnote.html#ArcOutOfRangeParameters) should be treated as a straight line. Inkscape [fails to render this](arcs-ink.png) (apparently painting a large solid black or white rectangle instead of the path), so its images were made with versions of the files that use an `L` instead.
|     |     |     |
| :-: | :-: | :-: |
| ![](arcs-ink-fix.png)<br/>**Inkscape** | ![](kozea-2020-11-23/arcs-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/arcs-vertices.png)<br/>**Kozea (vertices)** |
| ![](arcs-agc.png)<br/>**AgC/main**| ![](arcs-kozea.png)<br/>**AgC/master**  | ![](arcs-vertices.png)<br/>**AgC/master (vertices)** |

## Elliptic arcs
|     |     |     |
| :-: | :-: | :-: |
| ![](elliptic-ink-fix.png)<br/>**Inkscape** | ![](kozea-2020-11-23/elliptic-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/elliptic-vertices.png)<br/>**Kozea (vertices)** |
| ![](elliptic-agc.png)<br/>**AgC/main**| ![](elliptic-kozea.png)<br/>**AgC/master**  | ![](elliptic-vertices.png)<br/>**AgC/master (vertices)** |

## Moveto, closepath and marker types
|     |     |     |
| :-: | :-: | :-: |
| ![](start_end-ink.png)<br/>**Inkscape** | ![](kozea-2020-11-23/start_end-kozea.png)<br/>**Kozea** | ![](kozea-2020-11-23/start_end-vertices.png)<br/>**Kozea (vertices)** |
| ![](start_end-agc.png)<br/>**AgC/main**| ![](start_end-kozea.png)<br/>**AgC/master**  | ![](start_end-vertices.png)<br/>**AgC/master (vertices)** |

## Discrepancies with Inkscape
|     |     |     |
| :-: | :-: | :-: |
| ![](start_end-ink.png)<br/>**Inkscape** | ![](start_end-firefox.png)<br/>**Firefox** | ![](start_end-kozea.png)<br/>**AgC/master** |
| ![](overlap-ink.png)<br/>**Inkscape** | ![](overlap-firefox.png)<br/>**Firefox** | ![](overlap-kozea.png)<br/>**AgC/master** |

On the initial vertex of closed sub-paths, Inkscape doesn't average the angles of the adjoining segments as [the specification](https://www.w3.org/Graphics/SVG/1.1/painting.html#Markers) stipulates (which AgC/master follows, as do [Firefox] and the few other browsers I've tried), but instead places two markers in the direction of the first and last segments, as if the path had been "manually closed" with an `L`.

Contrary to what I originally assumed, Firefox actually also draws two overlapping markers, although obviously only one will be visible if their shape and orientation are the same. This is in line with the specification ("for a 'path' element which ends with a closed sub-path, (...) if 'marker-end' does not equal none, then it is possible that two markers will be rendered on the given vertex."), and is made clear in the second row of the comparison, in which the three marker types (start, mid and end) use differently sized circles.