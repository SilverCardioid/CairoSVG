import math

from .element import _ShapeElement
from .path import Path
from .. import helpers
from ..helpers.coordinates import size2 as _size, point2 as _point

class Circle(_ShapeElement):
	attribs = _ShapeElement.attribs + ['cx','cy','r','transform']

	def __init__(self, r=helpers._intdef(0), cx=helpers._intdef(0),
	             cy=helpers._intdef(0), **attribs):
		self.tag = 'circle'
		super().__init__(r=r, cx=cx, cy=cy, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		vp = self._getViewport()
		r  = _size(self['r'] , vp, 'xy')
		cx = _size(self['cx'], vp, 'x')
		cy = _size(self['cy'], vp, 'y')
		if r > 0:
			with self.transform.applyContext(surface):
				surface.context.new_sub_path()
				surface.context.arc(cx, cy, r, 0, 2*math.pi)
				self._paint(surface)


class Ellipse(_ShapeElement):
	attribs = _ShapeElement.attribs + ['cx','cy','rx','ry','transform']

	def __init__(self, rx=helpers._intdef(0), ry=helpers._intdef(0),
	             cx=helpers._intdef(0), cy=helpers._intdef(0), **attribs):
		self.tag = 'ellipse'
		super().__init__(rx=rx, ry=ry, cx=cx, cy=cy, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		vp = self._getViewport()
		rx, ry = _size(self['rx'], vp, 'x'), _size(self['ry'], vp, 'y')
		cx, cy = _size(self['cx'], vp, 'x'), _size(self['cy'], vp, 'y')
		if cx > 0 or cy > 0:
			ratio = ry/rx
			with self.transform.applyContext(surface):
				surface.context.new_sub_path()
				surface.context.save()
				surface.context.scale(1, ratio)
				surface.context.arc(cx, cy/ratio, rx, 0, 2*math.pi)
				surface.context.restore()
				self._paint(surface)


class Line(_ShapeElement):
	attribs = _ShapeElement.attribs + ['x1','y1','x2','y2','transform']

	def __init__(self, x1=helpers._intdef(0), y1=helpers._intdef(0),
	             x2=helpers._intdef(0), y2=helpers._intdef(0), **attribs):
		self.tag = 'line'
		super().__init__(x1=x1, y1=y1, x2=x2, y2=y2, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		x1, y1, x2, y2 = self.vertices()
		with self.transform.applyContext(surface):
			surface.context.move_to(x1, y1)
			surface.context.line_to(x2, y2)
			self._paint(surface)

	def vertices(self):
		vp = self._getViewport()
		x1, y1 = _size(self['x1'], vp, 'x'), _size(self['y2'], vp, 'y')
		x2, y2 = _size(self['x2'], vp, 'x'), _size(self['y2'], vp, 'y')
		return [x1, y1, x2, y2]

	def vertexAngles(self):
		angle = helpers.point_angle(*self.vertices())
		return [angle, angle]


class Polygon(_ShapeElement):
	attribs = _ShapeElement.attribs + ['points','transform']

	def __init__(self, points=helpers._strdef(''), **attribs):
		self.tag = 'polygon'
		super().__init__(points=points, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		points = self.vertices()

		if len(points) > 0:
			with self.transform.applyContext(surface):
				surface.context.move_to(*points[0])
				for point in points[1:]:
					surface.context.line_to(*point)
				surface.context.close_path()
				self._paint(surface)

	def vertices(self):
		vp = self._getViewport()
		points = self._attribs.get('points', '')
		if isinstance(points, str):
			# convert string to points
			string = helpers.attribs.normalize(points)
			points = []
			while string:
				x, y, string = _point(string, vp)
				points.append((x, y))

		# convert array of strings to points
		points = points.copy()
		for i, point in enumerate(points):
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

	def vertexAngles(self):
		path = Path().polyline(self.vertices(), closed=True)
		return path.vertexAngles()


class Polyline(_ShapeElement):
	attribs = _ShapeElement.attribs + ['points','transform']

	def __init__(self, points=helpers._strdef(''), **attribs):
		self.tag = 'polyline'
		super().__init__(points=points, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		points = self.vertices()

		if len(points) > 0:
			with self.transform:
				surface.context.move_to(*points[0])
				for point in points[1:]:
					surface.context.line_to(*point)
				self._paint(surface)

	vertices = Polygon.vertices

	def vertexAngles(self):
		path = Path().polyline(self.vertices(), closed=False)
		return path.vertexAngles()


class Rect(_ShapeElement):
	attribs = _ShapeElement.attribs + ['x','y','width','height','rx','ry','transform']
	_strAttrib = {
		# omit if None
		'rx': lambda val: val,
		'ry': lambda val: val
	}

	def __init__(self, width=helpers._intdef(0), height=helpers._intdef(0),
	             x=helpers._intdef(0), y=helpers._intdef(0),
	             rx=None, ry=None, **attribs):
		self.tag = 'rect'
		super().__init__(width=width, height=height, x=x, y=y, rx=rx, ry=ry, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		vp = self._getViewport()
		width, height = _size(self['width'], vp, 'x'), _size(self['height'], vp, 'y')
		x, y = _size(self['x'], vp, 'x'), _size(self['y'], vp, 'y')

		# rx and ry default to each other's value if None
		rx, ry = self['rx'], self['ry']
		if rx is not None:
			rx = _size(rx, vp, 'x')
		if ry is not None:
			ry = _size(ry, vp, 'y')
		if ry is None:
			ry = rx or 0
		if rx is None:
			rx = ry or 0

		with self.transform.applyContext(surface):
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

			self._paint(surface)
