_creators = {}

from . import structure, svg, shapes, path
from .. import helpers

elements = {
	'circle': shapes.Circle,
	'defs': structure.Defs,
	'ellipse': shapes.Ellipse,
	'g': structure.G,
	'line': shapes.Line,
	'path': path.Path,
	'polygon': shapes.Polygon,
	'polyline': shapes.Polyline,
	'rect': shapes.Rect,
	'svg': svg.SVG,
	'use': structure.Use
}

_creators.update({
	'circle':   lambda self, r=helpers._intdef(0), cx=helpers._intdef(0),
	                   cy=helpers._intdef(0), **attribs: \
	            	shapes.Circle(parent=self, r=r, cx=cx, cy=cy, **attribs),
	'defs':     lambda self, **attribs: \
	            	structure.Defs(parent=self, **attribs),
	'ellipse':  lambda self, rx=helpers._intdef(0), ry=helpers._intdef(0),
	                   cx=helpers._intdef(0), cy=helpers._intdef(0), **attribs: \
	            	shapes.Ellipse(parent=self, rx=rx, ry=ry, cx=cx, cy=cy, **attribs),
	'g':        lambda self, **attribs: \
	            	structure.G(parent=self, **attribs),
	'line':     lambda self, x1=helpers._intdef(0), y1=helpers._intdef(0),
	                   x2=helpers._intdef(0), y2=helpers._intdef(0), **attribs: \
	            	shapes.Line(parent=self, x1=x1, y1=y1, x2=x2, y2=y2, **attribs),
	'path':     lambda self, d=helpers._strdef(''), **attribs: \
	            	path.Path(parent=self, d=d, **attribs),
	'polygon':  lambda self, points=helpers._strdef(''), **attribs: \
	            	shapes.Polygon(parent=self, points=points, **attribs),
	'polyline': lambda self, points=helpers._strdef(''), **attribs: \
	            	shapes.Polyline(parent=self, points=points, **attribs),
	'rect':     lambda self, width=helpers._intdef(0), height=helpers._intdef(0),
	                   x=helpers._intdef(0), y=helpers._intdef(0),
	                   rx=None, ry=None, **attribs: \
	            	shapes.Rect(parent=self, width=width, height=height, x=x, y=y, rx=rx, ry=ry, **attribs),
	'svg':      lambda self, width, height, *, x=helpers._intdef(0), y=helpers._intdef(0),
	                   viewBox=helpers._strdef('none'), preserveAspectRatio=helpers._strdef('xMidYMid meet'),
	                   **attribs: \
	            	svg.SVG(parent=self, width=width, height=height, x=x, y=y,
	            	     viewBox=viewBox, preserveAspectRatio=preserveAspectRatio, **attribs),
	'use':      lambda self, href=helpers._strdef(''), *, x=helpers._intdef(0), y=helpers._intdef(0),
	                   width=helpers._intdef(0), height=helpers._intdef(0), **attribs: \
	            	structure.Use(parent=self, href=href, x=x, y=y, width=width, height=height, **attribs)
})
for tag in _creators:
	_creators[tag].__doc__ = f'Add a <{tag}> as a child of this element'
del tag

