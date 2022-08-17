import cairocffi as cairo
import cv2
import numpy as np
import os

from . import _creators
from .element import _Element, _StructureElement
from .. import helpers
from ..helpers import coordinates
from ..helpers.coordinates import size2 as _size
from ..helpers.modules import attrib as _attrib
from ..parse import parser

class SVG(_StructureElement):
	attribs = _StructureElement.attribs + _attrib['DocumentEvents'] + ['x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType','xmlns','xmlns:xlink']
	content = _StructureElement.content

	def __init__(self, width, height, *, x=helpers._intdef(0), y=helpers._intdef(0),
	             viewBox=helpers._strdef('none'), preserveAspectRatio=helpers._strdef('xMidYMid meet'),
	             **attribs):
		self.tag = 'svg'
		_Element.__init__(self, width=width, height=height, x=x, y=y,
		                  viewBox=viewBox, preserveAspectRatio=preserveAspectRatio,
		                  **attribs)
		self.viewport = coordinates.Viewport(parent=self, width=width, height=height,
		                                     viewBox=viewBox, preserveAspectRatio=preserveAspectRatio)

	def __setitem__(self, key, value):
		super().__setitem__(key, value)
		if key in ('width', 'height', 'viewBox', 'preserveAspectRatio'):
			self.viewport._attribs[key] = value

	# todo: delitem

	@property
	def width(self):
		return self.viewport.width

	@property
	def height(self):
		return self.viewport.height

	def draw(self, surface):
		viewportTransform = self.viewport.getTransform()

		x, y = 0, 0
		if not self.isRoot():
			# Nested SVG: use the element's x and y attributes
			vp = self._getViewport()
			x = _size(self.getAttribute('x', 0, cascade=False), vp, 'x')
			y = _size(self.getAttribute('y', 0, cascade=False), vp, 'y')

		surface.context.translate(x, y)
		with viewportTransform.applyContext(surface):
			for child in self._children:
				child.draw(surface)
		surface.context.translate(-x, -y)

	def export(self, filename, *, surface=None, useCairo=False,
	           indent='', newline='\n', xmlDeclaration=True):
		ext = os.path.splitext(filename)[1]
		width, height = round(self.width), round(self.height)
		if ext == '.pdf':
			surface = surface or helpers.surface.createSurface('PDF', width, height, filename)
			self.draw(surface)
			surface.finish()
		elif ext == '.png':
			surface = surface or helpers.surface.createSurface('Image', width, height, filename)
			self.draw(surface)
			surface.write_to_png(filename)
		elif ext == '.ps':
			surface = surface or helpers.surface.createSurface('PS', width, height, filename)
			self.draw(surface)
			surface.finish()
		elif ext == '.svg':
			if useCairo:
				surface = surface or helpers.surface.createSurface('SVG', width, height, filename)
				self.draw(surface)
				surface.finish()
			else:
				with open(filename, 'w') as file:
					self.code(file, indent=indent, newline=newline, xmlDeclaration=xmlDeclaration)
		else:
			raise ValueError('Unsupported file extension: {}'.format(ext))

	def pixels(self, *, surface=None, alpha=False, bgr=False):
		surface = surface or helpers.surface.createSurface('Image', round(self.width), round(self.height))
		self.draw(surface)
		# based on github.com/Zulko/gizeh
		im = 0 + np.frombuffer(surface.get_data(), np.uint8)
		im.shape = (surface.get_height(), surface.get_width(), 4)
		if not bgr:
			im = im[:,:,[2,1,0,3]]
		if alpha:
			return im
		else:
			return im[:,:,:3]

	def show(self, windowName='svg', *, surface=None, wait=0):
		cv2.imshow(windowName, self.pixels(surface=surface, bgr=True))
		close = False
		waitTime = wait if wait > 0 else 100 # ms
		try:
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
		except cv2.error as e:
			# ignore null pointer exception for already-closed window
			if not (e.code == -27):
				raise

	@classmethod
	def read(cls, filename, unsafe=False):
		tree = parser.Tree(url=filename, unsafe=unsafe)
		assert tree.tag == 'svg'
		#print(f'<{tree.tag}> attribs: {dict(tree)}')
		svg = cls(**tree)
		elementQueue = [(tree, svg)]
		while len(elementQueue) > 0:
			curNode, curElem = elementQueue.pop()
			for childNode in curNode._children:
				if childNode.tag in _creators:
					#print(f'<{childNode.tag}> attribs: {dict(childNode)}')
					childElem = _creators[childNode.tag](curElem, **childNode)
					elementQueue.append((childNode, childElem))
				else:
					print(f'<{childNode.tag}> node skipped')
		return svg