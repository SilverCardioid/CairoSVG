from .element import Element
from ..colors import color
from .. import helpers
#.path conditionally imported below


class ShapeElement(Element):
	def _paint(self, surface):
		opacity = float(self.getAttribute('opacity', 1))
		assert 0 <= opacity <= 1
		fillOpacity = float(self.getAttribute('fillOpacity', 1))
		assert 0 <= fillOpacity <= 1
		strokeOpacity = float(self.getAttribute('strokeOpacity', 1))
		assert 0 <= strokeOpacity <= 1

		fill = color(self.getAttribute('fill', '#000'), fillOpacity*opacity)
		fillRule = self.getAttribute('fillRule', 'nonzero')
		assert fillRule in helpers.FILL_RULES

		stroke = color(self.getAttribute('stroke', 'none'), strokeOpacity*opacity)
		strokeWidth = float(self.getAttribute('strokeWidth', 1))
		strokeLinecap = self.getAttribute('strokeLinecap', 'butt')
		assert strokeLinecap in helpers.LINE_CAPS
		strokeLinejoin = self.getAttribute('strokeLinejoin', 'miter')
		assert strokeLinejoin in helpers.LINE_JOINS
		# TODO: add dash

		surface.context.set_source_rgba(*fill)
		surface.context.set_fill_rule(helpers.FILL_RULES[fillRule])
		surface.context.fill_preserve()

		surface.context.set_source_rgba(*stroke)
		surface.context.set_line_width(strokeWidth)
		surface.context.set_line_cap(helpers.LINE_CAPS[strokeLinecap])
		surface.context.set_line_join(helpers.LINE_JOINS[strokeLinejoin])
		surface.context.stroke()

class Circle(ShapeElement):
	def __init__(self, r=0, cx=0, cy=0, **attribs):
		self.tag = 'circle'
		Element.__init__(self, r=r, cx=cx, cy=cy, **attribs)

	def draw(self, surface):
		surface.context.new_sub_path()
		surface.context.arc(self.attribs['cx'], self.attribs['cy'], self.attribs['r'], 0, 2 * pi)


class Ellipse(ShapeElement):
	def __init__(self, rx=0, ry=0, cx=0, cy=0, **attribs):
		self.tag = 'ellipse'
		Element.__init__(self, rx=rx, ry=ry, cx=cx, cy=cy, **attribs)

	def draw(self, surface):
		ratio = self.attribs['ry'] / self.attribs['rx']
		surface.context.new_sub_path()
		surface.context.save()
		surface.context.scale(1, ratio)
		surface.context.arc(self.attribs['cx'], self.attribs['cy'] / ratio, self.attribs['rx'], 0, 2 * pi)
		surface.context.restore()
		self._paint(surface)


class Line(ShapeElement):
	def __init__(self, x1=0, y1=0, x2=0, y2=0, **attribs):
		self.tag = 'line'
		Element.__init__(self, x1=x1, y1=y1, x2=x2, y2=y2, **attribs)

	def draw(self, surface):
		surface.context.move_to(self.attribs['x1'], self.attribs['y1'])
		surface.context.line_to(self.attribs['x2'], self.attribs['y2'])
		self._paint(surface)


class Polygon(ShapeElement):
	def __init__(self, points=[], **attribs):
		self.tag = 'polygon'
		if type(points) is str:
			from .path import Path
			points = Path(d='M'+points+'z').vertices()
		Element.__init__(self, points=points, **attribs)

	def draw(self, surface):
		points = self.attribs['points']
		if len(points) > 0:
			surface.context.move_to(*points[0])
			for point in points[1:]:
				surface.context.line_to(*point)
			surface.context.close_path()
		self._paint(surface)


class Polyline(ShapeElement):
	def __init__(self, points=[], **attribs):
		self.tag = 'polyline'
		if type(points) is str:
			from .path import Path
			points = Path(d='M'+points).vertices()
		Element.__init__(self, points=points, **attribs)

	def draw(self, surface):
		points = self.attribs['points']
		if len(points) > 0:
			surface.context.move_to(*points[0])
			for point in points[1:]:
				surface.context.line_to(*point)
		self._paint(surface)


class Rect(ShapeElement):
	def __init__(self, width=0, height=0, x=0, y=0, rx=None, ry=None, **attribs):
		self.tag = 'rect'
		if ry is None:
			ry = rx or 0
		if rx is None:
			rx = ry or 0
		Element.__init__(width=width, height=height, x=x, y=y, rx=rx, ry=ry, **attribs)

	def draw(self, surface):
		width, height = elf.attribs['width'], self.attribs['height']
		x, y = self.attribs['x'], self.attribs['y']
		rx, ry = self.attribs['rx'], self.attribs['ry']
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
