import os

import cv2
import numpy as np

from . import _creators
from .element import _Element, _StructureElement
from .. import helpers
from ..helpers import coordinates
from ..helpers.coordinates import size as _size
from ..helpers.modules import attrib as _attrib

class SVG(_StructureElement):
	tag = 'svg'
	attribs = _StructureElement.attribs + _attrib['DocumentEvents'] + ['x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType','xmlns','xmlns:xlink']
	content = _StructureElement.content

	def __init__(self, width, height, *, x=helpers._intdef(0), y=helpers._intdef(0),
	             viewBox=helpers._strdef('none'), preserveAspectRatio=helpers._strdef('xMidYMid meet'),
	             **attribs):
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

	@property
	def namespaces(self):
		return self._root.namespaces

	def draw(self, surface, *, paint=True, viewport=None):
		viewportTransform = self.viewport.getTransform()

		x, y = 0, 0
		if not self.isRoot():
			# Nested SVG: use the element's x and y attributes
			vp = viewport or self._getViewport()
			x = _size(self.getAttribute('x', 0), vp, 'x')
			y = _size(self.getAttribute('y', 0), vp, 'y')

		surface.context.translate(x, y)
		with viewportTransform.applyContext(surface):
			for child in self._children:
				child.draw(surface, paint=paint, viewport=viewport)
		surface.context.translate(-x, -y)

	def export(self, filename, *, surface=None, useCairo=False, **svgOptions):
		ext = os.path.splitext(filename)[1].lower()
		width, height = round(self.width), round(self.height)

		if ext == '.pdf':
			surface = surface or helpers.surface.createSurface('PDF', width, height, filename)
			try:
				self.draw(surface)
			finally:
				surface.finish()

		elif ext == '.png':
			surface = surface or helpers.surface.createSurface('Image', width, height, filename)
			try:
				self.draw(surface)
			finally:
				surface.write_to_png(filename)

		elif ext == '.ps':
			surface = surface or helpers.surface.createSurface('PS', width, height, filename)
			try:
				self.draw(surface)
			finally:
				surface.finish()

		elif ext == '.svg':
			if useCairo:
				surface = surface or helpers.surface.createSurface('SVG', width, height, filename)
				try:
					self.draw(surface)
				finally:
					surface.finish()
			else:
				self.save(filename, **svgOptions)

		else:
			# Other format: try saving image with cv2
			try:
				# Try drawing an empty file first to test the extension
				# before bothering to draw the actual image
				cv2.imwrite(filename, np.zeros((10, 10), dtype='uint8'))
				img = self.pixels(surface=surface, bgr=True)
				cv2.imwrite(filename, img)
			except cv2.error:
				raise ValueError('Unsupported file extension: {}'.format(ext))

	def save(self, filename, *, indent='', newline='\n', xmlDeclaration=True):
		with open(filename, 'w') as file:
			self.code(file, indent=indent, newline=newline, xmlDeclaration=xmlDeclaration)

	def pixels(self, *, surface=None, alpha=False, bgr=False):
		surface = surface or helpers.surface.createSurface('Image', round(self.width), round(self.height))
		self.draw(surface)
		return helpers.surface.pixels(surface, alpha=alpha, bgr=bgr)

	def show(self, windowName='svg', *, surface=None, wait=0):
		helpers.surface.show(self.pixels(surface=surface, bgr=True), windowName=windowName, wait=wait)

	@classmethod
	def read(cls, source):
		root = helpers.parse.read(source)
		assert root.tag == 'svg'
		return root
