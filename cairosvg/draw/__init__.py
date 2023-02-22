_creators = {}

from . import element, masks, path, shapes, structure, svg
from .. import helpers

elements = {
	'circle': shapes.Circle,
	'clipPath': masks.ClipPath,
	'defs': structure.Defs,
	'ellipse': shapes.Ellipse,
	'g': structure.G,
	'line': shapes.Line,
	'mask': masks.Mask,
	'path': path.Path,
	'polygon': shapes.Polygon,
	'polyline': shapes.Polyline,
	'rect': shapes.Rect,
	'svg': svg.SVG,
	'use': structure.Use,
	'custom': element.CustomElement
}

_creators.update({
	'circle':   lambda self, r=helpers._intdef(0), cx=helpers._intdef(0),
	                   cy=helpers._intdef(0), **attribs: \
	            	shapes.Circle(parent=self, r=r, cx=cx, cy=cy, **attribs),
	'clipPath': lambda self, clipPathUnits=helpers._strdef('userSpaceOnUse'), **attribs: \
	            	masks.ClipPath(parent=self, clipPathUnits=clipPathUnits, **attribs),
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
	'mask':     lambda self, x=helpers._strdef('-10%'), y=helpers._strdef('-10%'),
	                   width=helpers._strdef('120%'), height=helpers._strdef('120%'), *,
	                   maskUnits=helpers._strdef('objectBoundingBox'),
	                   maskContentUnits=helpers._strdef('userSpaceOnUse'), **attribs: \
	            	masks.Mask(parent=self, x=x, y=y, width=width, height=height,
	            	           maskUnits=maskUnits, maskContentUnits=maskContentUnits, **attribs),
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
	            	structure.Use(parent=self, href=href, x=x, y=y, width=width, height=height, **attribs),
	'custom':   lambda self, tag, namespace=helpers.namespaces.NS_SVG, **attribs: \
	            	element.CustomElement(parent=self, tag=tag, namespace=namespace, **attribs)
})
for tag in _creators:
	_creators[tag].__doc__ = f'Add a <{tag}> as a child of this element'
del tag

