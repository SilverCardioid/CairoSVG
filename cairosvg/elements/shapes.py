import math
import typing as ty

from .element import _ShapeElement
from .path import Path
from .. import helpers
from ..helpers.coordinates import size as _size, point as _point
from ..helpers import types as ht

class Circle(_ShapeElement):
	"""<circle> element.
	A shape element that draws a circle.

	Main attributes:
	* r: the circle's radius.
	* cx, cy: the position of the circle's center.
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'circle'
	attribs = _ShapeElement.attribs + ['cx','cy','r','transform']
	_defaults = {**_ShapeElement._defaults,
		'r': 0,
		'cx': 0,
		'cy': 0
	}

	def __init__(self, r_:ty.Optional[ht.Length] = None,
	             cx_:ty.Optional[ht.Length] = None,
	             cy_:ty.Optional[ht.Length] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, r=r_, cx=cx_, cy=cy_)
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		vp = viewport or self._getViewport()
		r  = _size(self._getattrib('r') , vp, 'xy')
		cx = _size(self._getattrib('cx'), vp, 'x')
		cy = _size(self._getattrib('cy'), vp, 'y')
		if r > 0:
			with self._applyTransformations(surface):
				surface.context.new_sub_path()
				surface.context.arc(cx, cy, r, 0, 2*math.pi)
				if paint:
					self._paint(surface, viewport=viewport)

	def boundingBox(self, *, withTransform:bool = True) -> ht.Box:
		vp = self._getViewport()
		r  = _size(self._getattrib('r') , vp, 'xy')
		cx = _size(self._getattrib('cx'), vp, 'x')
		cy = _size(self._getattrib('cy'), vp, 'y')
		box = ht.Box(cx - r, cy - r, 2*r, 2*r)
		if withTransform: box = self._transformBox(box)
		return box


class Ellipse(_ShapeElement):
	"""<ellipse> element.
	A shape element that draws an ellipse, with its major and
	minor axes aligned with the current coordinate system.

	Main attributes:
	* rx, ry: the ellipse's radii along the x and y axes.
	* cx, cy: the position of the ellipse's center.
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'ellipse'
	attribs = _ShapeElement.attribs + ['cx','cy','rx','ry','transform']
	_defaults = {**_ShapeElement._defaults,
		'rx': 0,
		'ry': 0,
		'cx': 0,
		'cy': 0
	}

	def __init__(self, rx_:ty.Optional[ht.Length] = None,
	             ry_:ty.Optional[ht.Length] = None,
	             cx_:ty.Optional[ht.Length] = None,
	             cy_:ty.Optional[ht.Length] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, rx=rx_, ry=ry_, cx=cx_, cy=cy_)
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		vp = viewport or self._getViewport()
		rx = _size(self._getattrib('rx'), vp, 'x')
		ry = _size(self._getattrib('ry'), vp, 'y')
		cx = _size(self._getattrib('cx'), vp, 'x')
		cy = _size(self._getattrib('cy'), vp, 'y')
		if rx > 0 and ry > 0:
			ratio = ry/rx
			with self._applyTransformations(surface):
				surface.context.new_sub_path()
				surface.context.save()
				surface.context.scale(1, ratio)
				surface.context.arc(cx, cy/ratio, rx, 0, 2*math.pi)
				surface.context.restore()
				if paint:
					self._paint(surface, viewport=viewport)

	def boundingBox(self, *, withTransform:bool = True) -> ht.Box:
		vp = self._getViewport()
		rx = _size(self._getattrib('rx'), vp, 'x')
		ry = _size(self._getattrib('ry'), vp, 'y')
		cx = _size(self._getattrib('cx'), vp, 'x')
		cy = _size(self._getattrib('cy'), vp, 'y')
		box = ht.Box(cx - rx, cy - ry, 2*rx, 2*ry)
		if withTransform: box = self._transformBox(box)
		return box


class Line(_ShapeElement):
	"""<line> element.
	A shape element that draws a line segment between two points.

	Main attributes:
	* x1, y1: the start point.
	* x2, y2: the end point.
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'line'
	attribs = _ShapeElement.attribs + ['x1','y1','x2','y2','transform']
	_defaults = {**_ShapeElement._defaults,
		'x1': 0,
		'y1': 0,
		'x2': 0,
		'y2': 0
	}

	def __init__(self, x1_:ty.Optional[ht.Length] = None,
	             y1_:ty.Optional[ht.Length] = None,
	             x2_:ty.Optional[ht.Length] = None,
	             y2_:ty.Optional[ht.Length] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, x1=x1_, y1=y1_, x2=x2_, y2=y2_)
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		(x1, y1), (x2, y2) = self.vertices(viewport=viewport)
		with self._applyTransformations(surface):
			surface.context.move_to(x1, y1)
			surface.context.line_to(x2, y2)
			if paint:
				self._paint(surface, viewport=viewport)

	def vertices(self, *, viewport:ty.Optional[ht.Viewport] = None) -> ht.VertexList:
		"""Get the two points of the line as a list of (x,y) tuples."""
		vp = viewport or self._getViewport()
		x1 = _size(self._getattrib('x1'), vp, 'x')
		y1 = _size(self._getattrib('y1'), vp, 'y')
		x2 = _size(self._getattrib('x2'), vp, 'x')
		y2 = _size(self._getattrib('y2'), vp, 'y')
		return [(x1, y1), (x2, y2)]

	def vertexAngles(self):
		p1, p2 = self.vertices()
		angle = helpers.geometry.point_angle(*p1, *p2)
		return [angle, angle]

	def boundingBox(self, *, withTransform:bool = True) -> ht.Box:
		box = ht.Box()
		(x1, y1), (x2, y2) = self.vertices()
		box.addPoint(x1, y1)
		box.addPoint(x2, y2)
		if withTransform: box = self._transformBox(box)
		return box


class Polygon(_ShapeElement):
	"""<polygon> element.
	A shape element that draws a closed sequence of line segments
	through a series of points.

	Main attributes:
	* points: a list of points. Can be a string containing point coordinates
	    separated by whitespace and/or commas, or a sequence of points
	    (each as a string or sequence of an x and a y coordinate).
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'polygon'
	attribs = _ShapeElement.attribs + ['points','transform']
	_defaults = {**_ShapeElement._defaults,
		'points': ''
	}

	def __init__(self, points_:ty.Union[str,ty.Sequence[ht.Point],None] = None,
	             /, **attribs):
		attribs = helpers.attribs.merge(attribs, points=points_)
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		points = self.vertices(viewport=viewport)

		if len(points) > 0:
			with self._applyTransformations(surface):
				surface.context.move_to(*points[0])
				for point in points[1:]:
					surface.context.line_to(*point)
				surface.context.close_path()
				if paint:
					self._paint(surface, viewport=viewport)

	def vertices(self, viewport:ty.Optional[ht.Viewport] = None) -> ht.VertexList:
		"""Get the vertices of the polygon as a list of (x,y) tuples."""
		vp = viewport or self._getViewport()
		points = self._getattrib('points')
		if isinstance(points, str):
			# convert string to points
			string = helpers.attribs.normalize(points)
			points = []
			while string:
				x, y, string = _point(string, vp)
				points.append((x, y))
		else:
			# assume sequence; convert/copy to list
			points = list(points)

		for i, point in enumerate(points):
			# parse string points/coordinates
			if isinstance(point, str):
				x, y, string = _point(helpers.attribs.normalize(point), vp)
				points[i] = (x, y)
				if string:
					# point has too many values
					raise helpers.PointError
			if isinstance(point[0], str):
				point[0] = _size(point[0], vp, 'x')
			if isinstance(point[1], str):
				point[1] = _size(point[1], vp, 'y')
			assert len(point) == 2

		return points

	def vertexAngles(self) -> ty.List[float]:
		path = Path().polyline(self.vertices(), closed=True)
		return path.vertexAngles()

	def boundingBox(self, *, withTransform:bool = True) -> ht.Box:
		box = ht.Box()
		for x, y in self.vertices():
			box.addPoint(x, y)
		if withTransform: box = self._transformBox(box)
		return box


class Polyline(_ShapeElement):
	"""<polyline> element.
	A shape element that draws a sequence of line segments through a
	series of points. Similar to <polygon>, but doesn't draw a line
	segment from the final point back to the initial point.

	Main attributes:
	* points: a list of points. Can be a string containing point coordinates
	    separated by whitespace and/or commas, or a sequence of points
	    (each as a string or sequence of an x and a y coordinate).
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'polyline'
	attribs = _ShapeElement.attribs + ['points','transform']
	_defaults = {**_ShapeElement._defaults,
		'points': ''
	}

	def __init__(self, points_:ty.Union[str,ty.Sequence[ht.Point],None] = None,
	             /, **attribs):
		attribs = helpers.attribs.merge(attribs, points=points_)
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		points = self.vertices(viewport=viewport)

		if len(points) > 0:
			with self._applyTransformations(surface):
				surface.context.move_to(*points[0])
				for point in points[1:]:
					surface.context.line_to(*point)
				if paint:
					self._paint(surface, viewport=viewport)

	vertices = Polygon.vertices
	vertices.__doc__ = vertices.__doc__.replace('polygon', 'polyline')
	boundingBox = Polygon.boundingBox

	def vertexAngles(self) -> ty.List[float]:
		path = Path().polyline(self.vertices(), closed=False)
		return path.vertexAngles()


class Rect(_ShapeElement):
	"""<rect> element.
	A shape element that draws a rectangle, optionally with rounded corners.

	Main attributes:
	* width, height: the rectangle's size.
	* x, y: the coordinates of rectangle's top left vertex.
	* rx, ry: elliptical arc radii for corner rounding. If only one of the
	    two is set, use circular arcs with the given radius. If neither is
	    set, draw a normal rectangle without rounded corners.
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'rect'
	attribs = _ShapeElement.attribs + ['x','y','width','height','rx','ry','transform']
	_defaults = {**_ShapeElement._defaults,
		'width': 0,
		'height': 0,
		'x': 0,
		'y': 0,
		'rx': None,
		'ry': None
	}
	_strAttrib = {
		# omit if None
		'rx': lambda val: val,
		'ry': lambda val: val
	}

	def __init__(self, width_:ty.Optional[ht.Length] = None,
	             height_:ty.Optional[ht.Length] = None,
	             x_:ty.Optional[ht.Length] = None,
	             y_:ty.Optional[ht.Length] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, width=width_, height=height_, x=x_, y=y_)
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		vp = viewport or self._getViewport()
		width = _size(self._getattrib('width'), vp, 'x')
		height = _size(self._getattrib('height'), vp, 'y')
		x = _size(self._getattrib('x'), vp, 'x')
		y = _size(self._getattrib('y'), vp, 'y')

		# rx and ry default to each other's value if None
		rx, ry = self._getattrib('rx'), self._getattrib('ry')
		if rx is not None:
			rx = _size(rx, vp, 'x')
		if ry is not None:
			ry = _size(ry, vp, 'y')
		if ry is None:
			ry = rx or 0
		if rx is None:
			rx = ry or 0

		with self._applyTransformations(surface):
			if rx == 0 or ry == 0:
				surface.context.rectangle(x, y, width, height)
			else:
				if rx > width / 2:
					rx = width / 2
				if ry > height / 2:
					ry = height / 2

				# Inspired by Cairo Cookbook
				# http://cairographics.org/cookbook/roundedrectangles/
				ARC_TO_BEZIER = 4 * (2 ** .5 - 1) / 3
				c1 = ARC_TO_BEZIER * rx
				c2 = ARC_TO_BEZIER * ry

				surface.context.new_path()
				surface.context.move_to(x + rx, y)
				surface.context.rel_line_to(width - 2 * rx, 0)
				surface.context.rel_curve_to(c1, 0, rx, c2, rx, ry)
				surface.context.rel_line_to(0, height - 2 * ry)
				surface.context.rel_curve_to(0, c2, c1 - rx, ry, -rx, ry)
				surface.context.rel_line_to(-width + 2 * rx, 0)
				surface.context.rel_curve_to(-c1, 0, -rx, -c2, -rx, -ry)
				surface.context.rel_line_to(0, -height + 2 * ry)
				surface.context.rel_curve_to(0, -c2, rx - c1, -ry, rx, -ry)
				surface.context.close_path()

			if paint:
				self._paint(surface, viewport=viewport)

	def boundingBox(self, *, withTransform:bool = True) -> ht.Box:
		vp = self._getViewport()
		width = _size(self._getattrib('width'), vp, 'x')
		height = _size(self._getattrib('height'), vp, 'y')
		x = _size(self._getattrib('x'), vp, 'x')
		y = _size(self._getattrib('y'), vp, 'y')
		box = ht.Box(x, y, width, height)
		if withTransform: box = self._transformBox(box)
		return box
