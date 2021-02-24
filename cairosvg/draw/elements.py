from .path import Path
from .shapes import Circle, Ellipse, Line, Polygon, Polyline, Rect
from .structure import Group, Use
from .svg import SVG

elements = {
	'circle': Circle,
	'ellipse': Ellipse,
	'g': Group,
	'line': Line,
	'path': Path,
	'polygon': Polygon,
	'polyline': Polyline,
	'rect': Rect,
	'svg': SVG,
	'use': Use
}