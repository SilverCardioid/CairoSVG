from contextlib import contextmanager
import typing as ty

from .element import _Element
from .. import helpers
from ..helpers.coordinates import size as _size
from ..helpers.modules import attrib as _attrib, content as _content
from ..helpers import types as ht

class ClipPath(_Element):
	"""<clipPath> element.
	Define a binary clipping path. When applied to SVG content using the
	'clip-path' attribute, only parts of the target that lie within the
	clipping path will be visible.

	Main attributes:
	* clipPathUnits: set the coordinate system for the clipPath's contents.
	    If 'userSpaceOnUse' (default), use absolute coordinates as defined
	    by the nearest ancestor <svg> or other viewport.
	    If 'objectBoundingBox', use relative coordinates as if in a 1 by 1
	    unit viewBox, which is mapped to the target element's bounding box.
	"""
	tag = 'clipPath'
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Paint'] + _attrib['Font'] + _attrib['TextContent'] + _attrib['Text'] + _attrib['Opacity'] + _attrib['Graphics'] + _attrib['Mask'] + _attrib['GraphicalEvents'] + _attrib['Clip'] + ['transform', 'clipPathUnits']
	content = _content['Description'] + _content['Animation'] + _content['Shape'] + _content['Text'] + ['use']
	_defaults = {**_Element._defaults,
		'clipPathUnits': 'userSpaceOnUse'
	}

	def __init__(self, **attribs):
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, 
	         viewport:ty.Optional[ht.Viewport] = None):
		# Draw nothing
		return

	def apply(self, surface:ht.Surface, target:_Element):
		surface.context.save()
		cp_units = self._getattrib('clipPathUnits').strip()
		if cp_units == 'objectBoundingBox':
			tx, ty, tw, th = target.bounding_box(with_transform=False).xywh
			if tw > 0 and th > 0:
				surface.context.translate(tx, ty)
				surface.context.scale(tw, th)
			clip_vp = helpers.coordinates.Viewport(width=1, height=1)
		else:
			if cp_units != 'userSpaceOnUse':
				print(f'warning: invalid attribute value: clipPathUnits="{cp_units}"')
			clip_vp = target._get_viewport()

		for child in self.child_elements():
			child.draw(surface, paint=False, viewport=clip_vp)
		surface.context.restore()

		# TODO: fill rules are not handled by cairo for clips
		# fill_rule = self.get_attribute('fill-rule', 'nonzero', cascade=True)
		# assert fill_rule in helpers.attribs.FILL_RULES
		# surface.context.set_fill_rule(helpers.attribs.FILL_RULES[fill_rule])
		surface.context.clip()

	@contextmanager
	def apply_context(self, surface:ht.Surface, target:_Element):
		surface.context.save()
		try:
			self.apply(surface, target)
			yield self
		finally:
			surface.context.restore()

	def _clip_box(self, box:ht.Box):
		# Get the bounding box of the clipPath's contents
		cp_box = ht.Box()
		for child in self.child_elements():
			cp_box += child.bounding_box()
		# Intersect it with the given box
		return cp_box & box


class Mask(_Element):
	"""<mask> element.

	Main attributes:
	* maskUnits
	* maskContentUnits
	* x, y, width, height
	"""
	tag = 'mask'
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + ['maskUnits', 'maskContentUnits', 'x', 'y', 'width', 'height']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']
	_defaults = {**_Element._defaults,
		'x': '-10%',
		'y': '-10%',
		'width': '120%',
		'height': '120%',
		'maskUnits': 'objectBoundingBox',
		'maskContentUnits': 'userSpaceOnUse'
	}

	def __init__(self, **attribs):
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True,
	         viewport:ty.Optional[ht.Viewport] = None):
		# Draw nothing
		return

	def apply(self, surface:ht.Surface, target:_Element):
		mask_units = self._getattrib('maskUnits').strip()
		content_units = self._getattrib('maskContentUnits').strip()
		if mask_units == 'userSpaceOnUse':
			# The spec specifies the invoking element's viewport
			# (https://drafts.fxtf.org/css-masking/#element-attrdef-mask-maskunits);
			# MDN conflictingly specifies the mask's own viewport
			# (https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/maskUnits)
			vp = target._get_viewport()
			x      = _size(self._getattrib('x')     , vp, 'x')
			y      = _size(self._getattrib('y')     , vp, 'y')
			width  = _size(self._getattrib('width') , vp, 'x')
			height = _size(self._getattrib('height'), vp, 'y')
		else:
			# objectBoundingBox: fractions or percentages of target's size
			# (as if in a "0 0 1 1" viewbox)
			if mask_units != 'objectBoundingBox':
				print(f'warning: invalid attribute value: maskUnits="{mask_units}"')
			tx, ty, tw, th = target.bounding_box(with_transform=False).xywh
			x      = tw * _size(self._getattrib('x')     , reference=1) + tx
			y      = th * _size(self._getattrib('y')     , reference=1) + ty
			width  = tw * _size(self._getattrib('width') , reference=1)
			height = th * _size(self._getattrib('height'), reference=1)

		mask_surface = helpers.surface.create_surface(
			'recording', x=x, y=y, width=width, height=height)
		if content_units == 'objectBoundingBox':
			tx, ty, tw, th = target.bounding_box(with_transform=False).xywh
			if tw > 0 and th > 0:
				mask_surface.context.translate(tx, ty)
				mask_surface.context.scale(tw, th)
			mask_vp = helpers.coordinates.Viewport(width=1, height=1)
		else:
			if content_units != 'userSpaceOnUse':
				print(f'warning: invalid attribute value: maskContentUnits="{content_units}"')
			mask_vp = target._get_viewport()

		for child in self.child_elements():
			# todo: pass-through for viewport
			child.draw(mask_surface, viewport=mask_vp)

		# uses alpha instead of luminance?
		surface.context.mask_surface(mask_surface)

	@contextmanager
	def apply_context(self, surface:ht.Surface, target:_Element):
		surface.context.save()
		try:
			self.apply(surface, target)
			yield self
		finally:
			surface.context.restore()
