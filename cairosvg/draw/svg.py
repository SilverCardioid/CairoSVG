from .element import Element, StructureElement

class SVG(StructureElement):
	attribs = ['Core','Conditional','Style','External','Presentation','GraphicalEvents','DocumentEvents','x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType']
	children = ['Description','Animation','Structure','Shape','Text','Image','View','Conditional','Hyperlink','Script','Style','Marker','Clip','Mask','Gradient','Pattern','Filter','Cursor','Font','ColorProfile']

	def __init__(self, width='auto', height='auto', *, x=0, y=0, viewBox=None, preserveAspectRatio='xMidYMid meet', **attribs):
		self.tag = 'svg'
		Element.__init__(self, width=width, x=x, y=y, viewBox=viewBox, preserveAspectRatio, preserveAspectRatio, **attribs)

	def path(self, d=None, **attribs):
		from .path import Path
		return Path(parent=self, d=d, **attribs)

	def rect(self): raise NotImplementedError()
	def circle(self): raise NotImplementedError()
	def clipPath(self): raise NotImplementedError()
	def defs(self): raise NotImplementedError()
	def ellipse(self): raise NotImplementedError()
	def g(self): raise NotImplementedError()
	def image(self): raise NotImplementedError()
	def line(self): raise NotImplementedError()
	def linearGradient(self): raise NotImplementedError()
	def radialGradient(self): raise NotImplementedError()
	def marker(self): raise NotImplementedError()
	def mask(self): raise NotImplementedError()
	def pattern(self): raise NotImplementedError()
	def polygon(self): raise NotImplementedError()
	def polyline(self): raise NotImplementedError()
	def style(self): raise NotImplementedError()
	def svg(self): raise NotImplementedError()
	def text(self): raise NotImplementedError()
	def title(self): raise NotImplementedError()
	def use(self): raise NotImplementedError()
