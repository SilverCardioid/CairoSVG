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
	* preserveAspectRatio: set the method for mapping the viewBox to the
	    <svg>'s size, in the format '{align} {meetOrSlice}' (default:
	    'xMidYMid meet'). {align} can be 'none' to stretch the image to fit the
	    <svg>'s dimensions, or a string of the form 'x{xalign}Y{yalign}' to
	    preserve the aspect ratio and use the specified alignment ('Mid', 'Min'
	    or 'Max' for either axis). {meetOrSlice} can be 'meet' to pad the
	    viewBox with empty space, or 'slice' to let it extend outside the outer
	    viewport (possibly cutting it off).
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
		#attrib = self._parse_attribute(attrib)
		attrib = super().__setitem__(attrib, value)
		if attrib in ('width', 'height', 'viewBox', 'preserveAspectRatio'):
			self.viewport._attribs[attrib] = value
		return attrib
	def __delitem__(self, attrib:str):
		#attrib = self._parse_attribute(attrib)
		attrib = super().__delitem__(attrib)
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

	def draw(self, surface:ht.Surface, *, paint:bool = True,
	         viewport:ty.Optional[ht.Viewport] = None):
		vp_transform = self.viewport.get_transform()

		x, y = 0, 0
		if not self.is_root():
			# Nested SVG: use the element's x and y attributes
			vp = viewport or self._get_viewport()
			x = _size(self.get_attribute('x', 0), vp, 'x')
			y = _size(self.get_attribute('y', 0), vp, 'y')

		surface.context.translate(x, y)
		with vp_transform.apply_context(surface):
			for child in self.child_elements():
				child.draw(surface, paint=paint, viewport=viewport)
		surface.context.translate(-x, -y)

	def export(self, filename:str, *, surface:ty.Optional[ht.Surface] = None,
	           use_cairo:bool = False, **svg_options):
		"""Export the document to `filename`.
		If `filename` has a '.svg' extension (case-insensitive) and `use_cairo` is
		False, directly write the SVG code to that file using the `save()` method.
		`**svg_options` will be passed on to that method.

		Otherwise, draw the document on a new cairocffi surface of the appropriate
		type (or the given `surface` if not None). '.png', '.pdf', '.ps' and '.svg'
		files (case-insensitive) can be saved directly using Cairo; other extensions
		will be assumed to be an image format and saved using OpenCV. A `ValueError`
		is raised if OpenCV doesn't support the extension or otherwise fails to
		write the image.
		"""
		ext = os.path.splitext(filename)[1].lower()
		width, height = self.viewport.get_absolute_size()
		width, height = round(width), round(height)

		if ext == '.pdf':
			surface = surface or helpers.surface.create_surface(
				'PDF', width, height, filename)
			try:
				self.draw(surface)
			finally:
				surface.finish()

		elif ext == '.png':
			surface = surface or helpers.surface.create_surface(
				'Image', width, height, filename)
			try:
				self.draw(surface)
			finally:
				surface.write_to_png(filename)

		elif ext == '.ps':
			surface = surface or helpers.surface.create_surface(
				'PS', width, height, filename)
			try:
				self.draw(surface)
			finally:
				surface.finish()

		elif ext == '.svg':
			if use_cairo:
				surface = surface or helpers.surface.create_surface(
					'SVG', width, height, filename)
				try:
					self.draw(surface)
				finally:
					surface.finish()
			else:
				self.save(filename, **svg_options)

		else:
			# Other format: try saving image with cv2
			try:
				# Try drawing an empty file first to test the extension
				# before bothering to draw the actual image
				cv2.imwrite(filename, np.zeros((10, 10), dtype='uint8'))
				img = self.pixels(surface=surface, bgr=True)
				cv2.imwrite(filename, img)
			except cv2.error:
				raise ValueError(f'Failed to write image with extension: {ext}')

	def save(self, filename:str, *, indent:ty.Optional[str] = '',
	         newline:ty.Optional[str] = '\n', xml_declaration:bool = True):
		"""Save the document as a .svg file.
		Open the given filename, and call `write_code()` to write the SVG code
		to it. The keyword parameters are passed on to that method.
		"""
		with open(filename, 'w', encoding='utf-8') as file:
			self.write_code(file, indent=indent, newline=newline,
			                xml_declaration=xml_declaration,
			                namespace_declaration=True)

	def pixels(self, *, surface:ty.Optional[ht.Surface] = None,
	           alpha:bool = False, bgr:bool = False) -> np.ndarray:
		"""Return the rendered image as a numpy array.
		For a document with width W and height H (rounded), the array's shape will
		be `H×W×4` if `alpha` is True, or `H×W×3` otherwise. Its datatype is uint8.
		If `alpha` is True, include the alpha (opacity) channel, else, omit it.
		if `bgr` is True, put the channels in OpenCV's BGR order, else, in RGB order.
		`surface` is a Cairo surface to draw on; if None, create a new one.
		"""
		width, height = self.viewport.get_absolute_size()
		surface = surface or helpers.surface.create_surface(
			'Image', round(width), round(height))
		self.draw(surface)
		return helpers.surface.pixels(surface, alpha=alpha, bgr=bgr)

	def show(self, window_name:str = 'svg', *,
	         surface:ty.Optional[ht.Surface] = None, wait:int = 0):
		"""Show the image in a pop-up window.
		The window can be closed by pressing the 'close' button normally, or by
		pressing the Q or Esc key.
		`window_name` is the title of the window, and should be unique among windows
		that are open at the same time.
		If `wait` is a positive number , automatically close the window after the
		given time in milliseconds.
		`surface` is passed through to the `pixels()` method.
		"""
		helpers.surface.show(self.pixels(surface=surface, bgr=True),
		                     window_name=window_name, wait=wait)

	@classmethod
	def read(cls, source:ty.Union[str, ty.TextIO]):
		"""Read an SVG file.
		`source` can be a filename or a file object.
		Raises a `ValueError` if the document's root element isn't <svg>.
		"""
		root = helpers.parse.read(source)
		if root.tag != 'svg':
			raise ValueError('SVG document without <svg> root element')
		return root
