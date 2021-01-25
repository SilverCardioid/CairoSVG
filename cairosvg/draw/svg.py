import cairocffi as cairo
from .element import Element, StructureElement

class SVG(StructureElement):
	attribs = ['Core','Conditional','Style','External','Presentation','GraphicalEvents','DocumentEvents','x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType']
	children = ['Description','Animation','Structure','Shape','Text','Image','View','Conditional','Hyperlink','Script','Style','Marker','Clip','Mask','Gradient','Pattern','Filter','Cursor','Font','ColorProfile']

	def __init__(self, width, height, *, x=0, y=0, viewBox=None, preserveAspectRatio='xMidYMid meet', **attribs):
		self.tag = 'svg'
		Element.__init__(self, width=width, height=height, x=x, y=y, viewBox=viewBox, preserveAspectRatio=preserveAspectRatio, **attribs)
		self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		self.surface.context = cairo.Context(self.surface)

	def export(self, filename):
		self.draw(self.surface)
		self.surface.write_to_png(filename)

	def path(self, d=None, **attribs):
		from .path import Path
		return Path(parent=self, d=d, **attribs)

	def circle(self, r=0, cx=0, cy=0, **attribs):
		from .shapes import Circle
		return Circle(parent=self, r=r, cx=cx, cy=cy, **attribs)

	def ellipse(self, rx=0, ry=0, cx=0, cy=0, **attribs):
		from .shapes import Ellipse
		return Ellipse(parent=self, rx=rx, ry=ry, cx=cx, cy=cy, **attribs)

	def line(self, x1=0, y1=0, x2=0, y2=0, **attribs):
		from .shapes import Line
		return Line(parent=self, x1=x1, y1=y1, x2=x2, y2=y2, **attribs)

	def polygon(self, points=[], **attribs):
		from .shapes import Polygon
		return Polygon(parent=self, points=points, **attribs)

	def polyline(self, points=[], **attribs):
		from .shapes import Polyline
		return Polyline(parent=self, points=points, **attribs)

	def rect(self, width=0, height=0, x=0, y=0, rx=None, ry=None, **attribs):
		from .shapes import Rect
		return Rect(parent=self, width=width, height=height, x=x, y=y, rx=rx, ry=ry, **attribs)


	def clipPath(self): raise NotImplementedError()
	def defs(self): raise NotImplementedError()
	def g(self): raise NotImplementedError()
	def image(self): raise NotImplementedError()
	def linearGradient(self): raise NotImplementedError()
	def radialGradient(self): raise NotImplementedError()
	def marker(self): raise NotImplementedError()
	def mask(self): raise NotImplementedError()
	def pattern(self): raise NotImplementedError()
	def style(self): raise NotImplementedError()
	def svg(self): raise NotImplementedError()
	def text(self): raise NotImplementedError()
	def title(self): raise NotImplementedError()
	def use(self): raise NotImplementedError()
