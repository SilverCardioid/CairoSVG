_creators = {}

from . import structure, svg, shapes, path

elements = {
	'circle': shapes.Circle,
	'defs': structure.Defs,
	'ellipse': shapes.Ellipse,
	'g': structure.Group,
	'line': shapes.Line,
	'path': path.Path,
	'polygon': shapes.Polygon,
	'polyline': shapes.Polyline,
	'rect': shapes.Rect,
	'svg': svg.SVG,
	'use': structure.Use
}

_creators.update({
	'circle':   lambda self, r=0, cx=0, cy=0, **attribs: \
	            	shapes.Circle(parent=self, r=r, cx=cx, cy=cy, **attribs),
	'defs':     lambda self, **attribs: \
	            	structure.Defs(parent=self, **attribs),
	'ellipse':  lambda self, rx=0, ry=0, cx=0, cy=0, **attribs: \
	            	shapes.Ellipse(parent=self, rx=rx, ry=ry, cx=cx, cy=cy, **attribs),
	'g':        lambda self, **attribs: \
	            	structure.Group(parent=self, **attribs),
	'line':     lambda self, x1=0, y1=0, x2=0, y2=0, **attribs: \
	            	shapes.Line(parent=self, x1=x1, y1=y1, x2=x2, y2=y2, **attribs),
	'path':     lambda self, d=None, **attribs: \
	            	path.Path(parent=self, d=d, **attribs),
	'polygon':  lambda self, points=[], **attribs: \
	            	shapes.Polygon(parent=self, points=points, **attribs),
	'polyline': lambda self, points=[], **attribs: \
	            	shapes.Polyline(parent=self, points=points, **attribs),
	'rect':     lambda self, width=0, height=0, x=0, y=0, rx=None, ry=None, **attribs: \
	            	shapes.Rect(parent=self, width=width, height=height, x=x, y=y, rx=rx, ry=ry, **attribs),
	'use':      lambda self, href=None, x=0, y=0, width=0, height=0, **attribs: \
	            	structure.Use(parent=self, href=href, x=x, y=y, width=width, height=height, **attribs)
})
for tag in _creators:
	_creators[tag].__doc__ = f'Add a <{tag}> as a child of this element'
del tag

