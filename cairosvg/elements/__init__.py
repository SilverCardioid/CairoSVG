_creators = {}

from .element import CustomElement
from .masks import ClipPath, Mask
from .path import Path
from .shapes import Circle, Ellipse, Line, Polygon, Polyline, Rect
from .structure import Defs, G, Use
from .svg import SVG
from .. import helpers
from ..helpers import types as ht

elements = {
	'circle': Circle,
	'clipPath': ClipPath,
	'defs': Defs,
	'ellipse': Ellipse,
	'g': G,
	'line': Line,
	'mask': Mask,
	'path': Path,
	'polygon': Polygon,
	'polyline': Polyline,
	'rect': Rect,
	'svg': SVG,
	'use': Use,
	'custom': CustomElement
}

_creators.update({
	'circle':   lambda self, r_=None, cx_=None, cy_=None, /, **attribs: \
	            	Circle(r_, cx_, cy_, parent=self, **attribs),
	'clipPath': lambda self, **attribs: \
	            	ClipPath(parent=self, **attribs),
	'defs':     lambda self, **attribs: \
	            	Defs(parent=self, **attribs),
	'ellipse':  lambda self, rx_=None, ry_=None,
	                   cx_=None, cy_=None, /, **attribs: \
	            	Ellipse(rx_, ry_, cx_, cy_, parent=self, **attribs),
	'g':        lambda self, **attribs: \
	            	G(parent=self, **attribs),
	'line':     lambda self, x1_=None, y1_=None,
	                   x2_=None, y2_=None, /, **attribs: \
	            	Line(x1_, y1_, x2_, y2_, parent=self, **attribs),
	'mask':     lambda self, **attribs: \
	            	Mask(parent=self, **attribs),
	'path':     lambda self, d_=None, /, **attribs: \
	            	Path(d_, parent=self, **attribs),
	'polygon':  lambda self, points_=None, /, **attribs: \
	            	Polygon(points_, parent=self, **attribs),
	'polyline': lambda self, points_=None, /, **attribs: \
	            	Polyline(points_, parent=self, **attribs),
	'rect':     lambda self, width_=None, height_=None,
	                   x_=None, y_=None, /, **attribs: \
	            	Rect(width_, height_, x_, y_, parent=self, **attribs),
	'svg':      lambda self, width_=None, height_=None, /, **attribs: \
	            	SVG(width_, height_, parent=self, **attribs),
	'use':      lambda self, href_=None, /, **attribs: \
	            	Use(href_, parent=self, **attribs),
	'custom':   lambda self, tag, namespace=helpers.namespaces.NS_SVG, **attribs: \
	            	CustomElement(parent=self, tag=tag, namespace=namespace, **attribs)
})
for tag in _creators:
	if tag == 'custom':
		_creators[tag].__doc__ = f'Add a custom element as a child of this element.'
	else:
		# Copy docstring from respective class, replacing the first line
		docLines = elements[tag].__doc__.split('\n', 1) if tag in elements else ['']
		docLines[0] = f'Add a <{tag}> as a child of this element.'
		_creators[tag].__doc__ = '\n'.join(docLines)
del tag
