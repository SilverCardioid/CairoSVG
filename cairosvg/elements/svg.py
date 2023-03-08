import os
import typing as ty

import cv2
import numpy as np

from . import _creators
from .element import _StructureElement
from .. import helpers
from ..helpers import coordinates
from ..helpers.modules import attrib as _attrib
from ..helpers.coordinates import size as _size
from ..helpers import types as ht

class SVG(_StructureElement):
	"""<svg> element.
	The main container element for an SVG document.
	Establishes a viewport and coordinate system.

	Main attributes:
	* width, height: the displayed size of the document. Default 'auto',
	    or 100% of its parent viewport (0 if there is no parent viewport).
	* x, y: position within its parent viewport (default 0).
	    Only useful for <svg>s that aren't the root element.
	* viewBox: coordinate system for the <svg>'s contents, in the form
	    'x y width height'. Defines a rectangular area that will be scaled
	    and translated to fit the <svg>'s display size. Default 'none'.
	* preserveAspectRatio: set the method for mapping the viewBox to the <svg>'s
	    size, in the format '{align} {meetOrSlice}' (default: 'xMidYMid meet').
	    {align} can be 'none' to stretch the image to fit the <svg>'s dimensions,
	    or a string of the form 'x{xalign}Y{yalign}' to preserve the aspect ratio
	    and use the specified alignment ('Mid', 'Min' or 'Max' for either axis).
	    {meetOrSlice} can be 'meet' to pad the viewBox with empty space, or 'slice'
	    to let it extend outside the outer viewport (possibly cutting it off).
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'svg'
	attribs = _StructureElement.attribs + _attrib['DocumentEvents'] + ['x','y','width','height','viewBox','preserveAspectRatio','zoomAndPan','version','baseProfile','contentScriptType','contentStyleType','xmlns','xmlns:xlink']
	content = _StructureElement.content
	_defaults = {**_StructureElement._defaults,
		'width': 'auto',
		'height': 'auto',
		'x': 0,
		'y': 0,
		'viewBox': 'none',
		'preserveAspectRatio': 'xMidYMid meet',
	}

	def __init__(self, width_:ty.Optional[ht.Length] = None,
	             height_:ty.Optional[ht.Length] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, width=width_, height=height_)
		super().__init__(**attribs)
		self.viewport = coordinates.Viewport(parent=self)

	def __setitem__(self, attrib:str, value:ty.Any):
		#attrib = self._parseAttribute(attrib)
		attrib = super().__setitem__(attrib, value)
		if attrib in ('width', 'height', 'viewBox', 'preserveAspectRatio'):
			self.viewport._attribs[attrib] = value
		return attrib
	def __delitem__(self, attrib:str):
		#attrib = self._parseAttribute(attrib)
		attrib = super().__delitem__(attrib, value)
		if attrib in ('width', 'height', 'viewBox', 'preserveAspectRatio'):
			self.viewport._attribs[attrib] = self._defaults[attrib]
		return attrib

	@property
	def width(self) -> float:
		return self.viewport.width
	@width.setter
	def width(self, value:ht.Length):
		self['width'] = value
	@width.deleter
	def width(self):
		del self['width']

	@property
	def height(self) -> float:
		return self.viewport.height
	@height.setter
	def height(self, value:ht.Length):
		self['height'] = value
	@height.deleter
	def height(self):
		del self['height']

	@property
	def namespaces(self) -> ht.Namespaces:
		return self._root.namespaces

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
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

	def export(self, filename:str, *, surface:ty.Optional[ht.Surface] = None,
	           useCairo:bool = False, **svgOptions):
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

	def save(self, filename:str, *, indent:ty.Optional[str] = '', newline:ty.Optional[str] = '\n', xmlDeclaration:bool = True):
		with open(filename, 'w') as file:
			self.code(file, indent=indent, newline=newline, xmlDeclaration=xmlDeclaration)

	def pixels(self, *, surface:ty.Optional[ht.Surface] = None, alpha:bool = False, bgr:bool = False):
		surface = surface or helpers.surface.createSurface('Image', round(self.width), round(self.height))
		self.draw(surface)
		return helpers.surface.pixels(surface, alpha=alpha, bgr=bgr)

	def show(self, windowName:str = 'svg', *, surface:ty.Optional[ht.Surface] = None, wait:int = 0):
		helpers.surface.show(self.pixels(surface=surface, bgr=True), windowName=windowName, wait=wait)

	@classmethod
	def read(cls, source:ty.Union[str, ty.TextIO]):
		root = helpers.parse.read(source)
		assert root.tag == 'svg'
		return root
