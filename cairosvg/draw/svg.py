import cairocffi as cairo
import cv2
import numpy as np
import os

from .. import helpers
from .element import Element
from .structure import StructureElement

class SVG(StructureElement):
	attribs = ['Core','Conditional','Style','External','Presentation','GraphicalEvents','DocumentEvents','x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType']
	children = ['Description','Animation','Structure','Shape','Text','Image','View','Conditional','Hyperlink','Script','Style','Marker','Clip','Mask','Gradient','Pattern','Filter','Cursor','Font','ColorProfile']

	def __init__(self, width, height, *, x=0, y=0, viewBox=None, preserveAspectRatio='xMidYMid meet', **attribs):
		self.tag = 'svg'
		Element.__init__(self, width=width, height=height, x=x, y=y, viewBox=viewBox, preserveAspectRatio=preserveAspectRatio, **attribs)
		self['xmlns'] = 'http://www.w3.org/2000/svg'
		if not self.surface: self.setSurface('Image')

	def setSurface(self, surfaceType, filename=None):
		self.surface = helpers.createSurface(surfaceType, self['width'], self['height'], filename)
		self.surfaceType = surfaceType

	def clearSurface(self):
		self.surface.context.set_operator(cairo.OPERATOR_CLEAR)
		self.surface.context.paint()
		self.surface.context.set_operator(cairo.OPERATOR_OVER)

	def export(self, filename, svgOptions={}):
		ext = os.path.splitext(filename)[1]
		if ext == '.pdf':
			surface = helpers.createSurface('PDF', self['width'], self['height'], filename)
			self.draw(surface)
			surface.finish()
		elif ext == '.png':
			self.clearSurface()
			self.draw()
			self.surface.write_to_png(filename)
		elif ext == '.ps':
			surface = helpers.createSurface('PS', self['width'], self['height'], filename)
			self.draw(surface)
			surface.finish()
		elif ext == '.svg':
			if svgOptions.get('useCairo', False):
				surface = helpers.createSurface('SVG', self['width'], self['height'], filename)
				self.draw(surface)
				surface.finish()
			else:
				with open(filename, 'w') as file:
					svgOptions['xmlDeclaration'] = svgOptions.get('xmlDeclaration', True)
					self.code(file, **svgOptions)
		else:
			raise ValueError('Unsupported file extension: {}'.format(ext))

	def pixels(self, alpha=False, bgr=False):
		self.clearSurface()
		self.draw()
		# based on github.com/Zulko/gizeh
		im = 0 + np.frombuffer(self.surface.get_data(), np.uint8)
		im.shape = (self['height'], self['width'], 4)
		if not bgr:
			im = im[:,:,[2,1,0,3]]
		if alpha:
			return im
		else:
			return im[:,:,:3]

	def show(self, windowName='svg', *, wait=0):
		cv2.imshow(windowName, self.pixels(bgr=True))
		close = False
		waitTime = wait if wait > 0 else 100 # ms
		while not close:
			key = cv2.waitKey(waitTime)
			if key >= 0 and (key & 0xFF) in [ord('q'), 27] \
			or cv2.getWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN) < 0:
				# Q or Esc key pressed or window manually closed (cv2.WND_PROP_VISIBLE doesn't work correctly)
				close = True
			elif wait > 0:
				# Specified time elapsed
				close = True
		if close:
			cv2.destroyWindow(windowName)

	def g(self, **attribs):
		from .structure import Group
		return Group(parent=self, **attribs)

	def use(self, href=None, x=0, y=0, width=0, height=0, **attribs):
		from .structure import Use
		return Use(parent=self, href=href, x=x, y=y, width=width, height=height, **attribs)

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
