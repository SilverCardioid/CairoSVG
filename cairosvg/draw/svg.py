class SVG:
	def __init__(self, width='auto', height='auto', *, x=0, y=0, viewBox=None, preserveAspectRatio='xMidYMid meet', **globalAttributes):
		self.tag = 'svg'
		self.globals = {'ids':{}}
		#super().__init__(self, **globalAttributes)

	# Permitted children:
	# * Animation elements: <animate>, <animateColor>, <animateMotion>, <animateTransform>, <discard>, <mpath>, <set>
	# * Descriptive elements: <desc>, <metadata>, <title>
	# * Shape elements: <circle>, <ellipse>, <line>, <mesh>, <path>, <polygon>, <polyline>, <rect>
	# * Structural elements: <defs>, <g>, <svg>, <symbol>, <use>
	# * Gradient elememnts: <linearGradient>, <meshgradient>, <radialGradient>, <stop>
	# <a>, <altGlyphDef>, <clipPath>, <color-profile>, <cursor>, <filter>, <font>, <font-face>, <foreignObject>, <image>, <marker>, <mask>, <pattern>, <script>, <style>, <switch>, <text>, <view>

	def path(self): raise NotImplementedError()
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
