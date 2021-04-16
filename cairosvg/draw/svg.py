import cairocffi as cairo
import cv2
import numpy as np
import os

from .. import helpers
from .modules import attrib, content
from .element import Element
from .structure import StructureElement

class SVG(StructureElement):
	attribs = StructureElement.attribs + attrib['DocumentEvents'] + ['x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType']
	content = StructureElement.content

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
