from __future__ import annotations
from contextlib import contextmanager
import math
import re
import typing as ty

import cairocffi as cairo

from ..helpers import attribs, coordinates, geometry

if ty.TYPE_CHECKING:
	from ..elements.element import _Element

class Transform:
	"""A class representing an affine transformation.
	Elements that support the `transform` attribute have a `Transform` object
	accessible through their `transform` property. The class can be used in a
	standalone way as well by instantiating it or using `copy()`.
	If a `Transform` object belongs to an element, operations on the object
	are reflected in the element's `transform` attribute.
	"""

	def __init__(self, source:_TransformSource = None):
		self._parent = None
		self._reset()
		if source is not None:
			self._transform(source)

	def _add_to_attr(self, string:str):
		if self._parent:
			val = self._parent._attribs.get('transform', None) or ''
			if val:
				val += ' '
			val += string
			self._parent['transform'] = val

	def _get_origin(self) -> ty.Tuple[float, float]:
		transform_origin = self._parent and self._parent.get_attribute('transform-origin', None) # todo: cascadable or not?
		if transform_origin:
			vp = self._parent and self._parent.get_viewport()
			width, height = vp.inner_size

			if isinstance(transform_origin, str):
				origin = transform_origin.split(' ')
			if len(origin) == 1:
				origin_x = origin[0]
				if origin_x in ('top', 'bottom'):
					origin_x, origin_y = width/2, origin_x
				else:
					origin_y = height/2
			elif len(origin) > 1:
				origin_x, origin_y = origin[:2]
				if origin_x in ('top', 'bottom'):
					origin_x, origin_y = origin_y, origin_x

			if   origin_x == 'center': origin_x = width/2
			elif origin_x == 'left':   origin_x = 0
			elif origin_x == 'right':  origin_x = width
			else:                      origin_x = coordinates.size(origin_x, vp, 'x')

			if   origin_y == 'center': origin_y = height/2
			elif origin_y == 'top':    origin_y = 0
			elif origin_y == 'bottom': origin_y = height
			else:                      origin_y = coordinates.size(origin_y, vp, 'y')

			return (origin_x, origin_y)
		else:
			return (0, 0)

	def __repr__(self) -> str:
		if self._parent:
			return 'Transform(\'' + self._parent._attribs.get('transform', '') + '\')'
		vals = [str(v).removesuffix('.0') for v in self._mat.as_tuple()]
		return 'Transform(\'matrix(' + ','.join(vals) + ')\')'

	def transform(self, source:_TransformSource, *params:coordinates.Length) -> Transform:
		"""Apply a transformation on top of the current transformation matrix.
		`source` can be:
		* a string, interpreted as an SVG transform string (e.g.,
		  `transform('translate(10,10) scale(2)')`);
		* a string with additional `params`, interpreted as an operation name
		  and values (e.g., `transform('translate', 10, 10)`);
		* a Cairo `Matrix` object or another `Transform` object.
		"""
		self._transform(source, *params)
		if self._parent and source is not None:
			# Append to transform attribute
			if isinstance(source, str):
				trans = source
				if len(params):
					trans += '(' + ','.join(str(v) for v in params) + ')'
			else: # Matrix or Transform
				matrix = source if isinstance(source, cairo.Matrix) else source._mat
				vals = [str(v).removesuffix('.0') for v in matrix.as_tuple()]
				trans = 'matrix(' + ','.join(vals) + ')'

			self._add_to_attr(trans)

		return self
	__call__ = transform

	def _transform(self, source:_TransformSource, *params:coordinates.Length):
		if source is None:
			return

		if isinstance(source, str):
			self._transform_string(source, *params)
			return

		if isinstance(source, cairo.Matrix):
			matrix = source
		elif isinstance(source, Transform):
			matrix = source._mat
		else:
			raise ValueError(f'Invalid transform source type: {type(source)}')
		self._mat = matrix * self._mat
			
	def _transform_string(self, string:str, *params:coordinates.Length):
		if len(params):
			# transform('type',values)
			transformations = [(string, params)]
		else:
			# transform('type(values)')
			transformations = re.findall(r'(\w+) ?\( ?(.*?) ?\)', attribs.normalize(string))

		for transformation_type, values in transformations:
			# Convert string values to numbers
			if isinstance(values, str):
				values = values.split(' ')
			for i, value in enumerate(values):
				if isinstance(value, str):
					values[i] = coordinates.size(value, units=False)

			if transformation_type == 'matrix':      self._matrix(*values)
			elif transformation_type == 'rotate':    self._rotate(*values)
			elif transformation_type == 'skewX':     self._skewX(*values)
			elif transformation_type == 'skewY':     self._skewY(*values)
			elif transformation_type == 'translate': self._translate(*values)
			elif transformation_type == 'scale':     self._scale(*values)

		#try:
		#	self._mat.invert()
		#except cairo.Error:
		#	# Matrix not invertible, clip the surface to an empty path
		#	active_path = surface.context.copy_path()
		#	surface.context.new_path()
		#	surface.context.clip()
		#	surface.context.append_path(active_path)
		#else:
		#	if gradient:
		#		# When applied on gradient use already inverted matrix (mapping
		#		# from user space to gradient space)
		#		matrix_now = gradient.get_matrix()
		#		gradient.set_matrix(matrix_now.multiply(self._mat))
		#	else:
		#		self._mat.invert()
		#		surface.context.transform(self._mat)

	@property
	def parent(self) -> ty.Optional[_Element]:
		"""Get the element linked to this transformation (if any)."""
		return self._parent

	@property
	def current_matrix(self) -> cairo.Matrix:
		"""Get the current transformation matrix as a Cairo matrix."""
		return self._mat.copy()

	def copy(self) -> Transform:
		"""Create a copy of this transformation.
		A copy of an element's `Transform` will not be linked to the element.
		"""
		return Transform(self._mat)

	def apply(self, surface:cairo.Surface):
		"""Apply this transformation to a Cairo surface."""
		origin_x, origin_y = self._get_origin()
		surface.context.translate(origin_x, origin_y)
		surface.context.transform(self._mat)
		surface.context.translate(-origin_x, -origin_y)

	@contextmanager
	def apply_context(self, surface:cairo.Surface):
		"""Apply this transformation to a Cairo surface.
		To be used as a context manager using the `with` keyword.
		"""
		if self._transformed:
			self.push(surface)
		try:
			yield self
		finally:
			if self._transformed:
				self.pop(surface)

	def save(self, surface:cairo.Surface):
		"""Push this transformation onto the Cairo surface's stack.
		Save the current state of the surface using the context's `save`
		method, then apply the transformation.
		"""
		surface.context.save()
		self.apply(surface)
	push = save

	def restore(self, surface:cairo.Surface):
		"""Restore the last saved transformation state of the Cairo surface.
		Pop the last state from the surface's stack using the context's
		`restore` method.
		"""
		surface.context.restore()
	pop = restore

	def transform_point(self, x:float, y:float) -> ty.Tuple[float, float]:
		"""Apply this transformation to a point."""
		return self._mat.transform_point(x, y)

	# The public version of each method changes
	# the parent's 'transform' attribute;
	# the private version (with '_') doesn't
	def translate(self, tx:float, ty:float = 0) -> Transform:
		"""Translate by an x and y offset."""
		self._translate(tx, ty)
		self._add_to_attr(f'translate({tx},{ty})' if ty != 0 else
		                  f'translate({tx})')
		return self
	def _translate(self, tx:float, ty:float = 0):
		self._mat.translate(tx, ty)
		self._transformed = True

	def scale(self, sx:float, sy:ty.Optional[float] = None) -> Transform:
		"""Scale by an x and y factor.
		If `sy` is None, scale uniformly.
		"""
		self._scale(sx, sy)
		self._add_to_attr(f'scale({sx},{sy})' if sy is not None else
		                  f'scale({sx})')
		return self
	def _scale(self, sx:float, sy:ty.Optional[float] = None):
		self._mat.scale(sx, sy)
		self._transformed = True

	def rotate(self, angle:float, cx:float = 0, cy:float = 0) -> Transform:
		"""Rotate around a point by an angle in degrees."""
		self._rotate(angle)
		self._add_to_attr(f'rotate({angle},{cx},{cy})' if cx != 0 or cy != 0 else
		                  f'rotate({angle})')
		return self
	def _rotate(self, angle:float, cx:float = 0, cy:float = 0):
		self._mat.translate(cx, cy)
		self._mat.rotate(math.radians(angle))
		self._mat.translate(-cx, -cy)
		self._transformed = True

	def skewX(self, angle:float) -> Transform:
		"""Skew horizontally by an angle in degrees."""
		self._skewX(angle)
		self._add_to_attr(f'skewX({angle})')
		return self
	def _skewX(self, angle:float):
		self._mat = cairo.Matrix(1, 0, math.tan(math.radians(angle)),
		                         1, 0, 0) * self._mat
		self._transformed = True

	def skewY(self, angle:float) -> Transform:
		"""Skew vertically by an angle in degrees."""
		self._skewY(angle)
		self._add_to_attr(f'skewY({angle})')
		return self
	def _skewY(self, angle:float):
		self._mat = cairo.Matrix(1, math.tan(math.radians(angle)), 0,
		                         1, 0, 0) * self._mat
		self._transformed = True

	def matrix(self, xx:float, yx:float, xy:float, yy:float, x0:float, y0:float) -> Transform:
		"""Apply a transformation matrix.
		Values are in SVG order, consisting of the columns of a 3x3
		transformation matrix without the (0,0,1) bottom row.
		"""
		self._matrix(xx, yx, xy, yy, x0, y0)
		self._add_to_attr(f'matrix({xx},{yx},{xy},{yy},{x0},{y0})')
		return self
	def _matrix(self, xx:float, yx:float, xy:float, yy:float, x0:float, y0:float):
		self._mat = cairo.Matrix(xx, yx, xy, yy, x0, y0) * self._mat
		self._transformed = True

	def reset(self) -> Transform:
		"""Reset this transformation to the identity matrix."""
		self._reset()
		if self._parent:
			self._parent['transform'] = ''
		return self
	def _reset(self):
		self._mat = cairo.Matrix()
		self._transformed = False

	def _transform_box(self, box:geometry.Box):
		new_box = geometry.Box()
		for x, y in box.vertices():
			new_box.add_point(*self.transform_point(x, y))
		return new_box

_TransformSource = ty.Union[str, Transform, cairo.Matrix, None]
