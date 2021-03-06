import math

from .element import ShapeElement
from .modules import attrib
from .path import Path
from .. import helpers

class Circle(ShapeElement):
	attribs = ShapeElement.attribs + ['cx','cy','r','transform']

	def __init__(self, r=0, cx=0, cy=0, **attribs):
		self.tag = 'circle'
		super().__init__(r=r, cx=cx, cy=cy, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		with self.transform.applyContext(surface):
			surface.context.new_sub_path()
			surface.context.arc(self.attribs['cx'], self.attribs['cy'], self.attribs['r'], 0, 2 * math.pi)
			self._paint(surface)


class Ellipse(ShapeElement):
	attribs = ShapeElement.attribs + ['cx','cy','rx','ry','transform']

	def __init__(self, rx=0, ry=0, cx=0, cy=0, **attribs):
		self.tag = 'ellipse'
		super().__init__(rx=rx, ry=ry, cx=cx, cy=cy, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		ratio = self.attribs['ry'] / self.attribs['rx']
		with self.transform.applyContext(surface):
			surface.context.new_sub_path()
			surface.context.save()
			surface.context.scale(1, ratio)
			surface.context.arc(self.attribs['cx'], self.attribs['cy'] / ratio, self.attribs['rx'], 0, 2 * math.pi)
			surface.context.restore()
			self._paint(surface)


class Line(ShapeElement):
	attribs = ShapeElement.attribs + ['x1','y1','x2','y2','transform']

	def __init__(self, x1=0, y1=0, x2=0, y2=0, **attribs):
		self.tag = 'line'
		super().__init__(x1=x1, y1=y1, x2=x2, y2=y2, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		with self.transform.applyContext(surface):
			surface.context.move_to(self.attribs['x1'], self.attribs['y1'])
			surface.context.line_to(self.attribs['x2'], self.attribs['y2'])
			self._paint(surface)

	def vertices(self):
		return [[self.attribs['x1'], self.attribs['y1']],
		        [self.attribs['x2'], self.attribs['y2']]]

	def vertexAngles(self):
		angle = helpers.point_angle(self.attribs['x1'], self.attribs['y1'], self.attribs['x2'], self.attribs['y2'])
		return [angle, angle]


class Polygon(ShapeElement):
	attribs = ShapeElement.attribs + ['points','transform']

	def __init__(self, points=[], **attribs):
		self.tag = 'polygon'
		self._path = Path()
		if type(points) is str:
			self._path.d('M' + points + 'z')
			points = self._path.vertices()
		else:
			self._path.polyline(points, True)
		super().__init__(points=points, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		points = self.attribs['points']
		if len(points) > 0:
			with self.transform.applyContext(surface):
				surface.context.move_to(*points[0])
				for point in points[1:]:
					surface.context.line_to(*point)
				surface.context.close_path()
				self._paint(surface)

	def vertices(self):
		return self._path.vertices()

	def vertexAngles(self):
		return self._path.vertexAngles()


class Polyline(ShapeElement):
	attribs = ShapeElement.attribs + ['points','transform']

	def __init__(self, points=[], **attribs):
		self.tag = 'polyline'
		self._path = Path()
		if type(points) is str:
			self._path.d('M' + points)
			points = self._path.vertices()
		else:
			self._path.polyline(points, False)
		super().__init__(points=points, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		points = self.attribs['points']
		if len(points) > 0:
			with self.transform:
				surface.context.move_to(*points[0])
				for point in points[1:]:
					surface.context.line_to(*point)
				self._paint(surface)

	def vertices(self):
		return self._path.vertices()

	def vertexAngles(self):
		return self._path.vertexAngles()


class Rect(ShapeElement):
	attribs = ShapeElement.attribs + ['x','y','width','height','rx','ry','transform']

	def __init__(self, width=0, height=0, x=0, y=0, rx=None, ry=None, **attribs):
		self.tag = 'rect'
		if ry is None:
			ry = rx or 0
		if rx is None:
			rx = ry or 0
		super().__init__(width=width, height=height, x=x, y=y, rx=rx, ry=ry, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		width, height = self.attribs['width'], self.attribs['height']
		x, y = self.attribs['x'], self.attribs['y']
		rx, ry = self.attribs['rx'], self.attribs['ry']

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
