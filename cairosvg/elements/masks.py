from contextlib import contextmanager
import typing as ty

from .element import _Element
from .. import helpers
from ..helpers.coordinates import size as _size
from ..helpers.modules import attrib as _attrib, content as _content
from ..helpers import types as ht

class ClipPath(_Element):
	tag = 'clipPath'
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Paint'] + _attrib['Font'] + _attrib['TextContent'] + _attrib['Text'] + _attrib['Opacity'] + _attrib['Graphics'] + _attrib['Mask'] + _attrib['GraphicalEvents'] + _attrib['Clip'] + ['transform', 'clipPathUnits']
	content = _content['Description'] + _content['Animation'] + _content['Shape'] + _content['Text'] + ['use']
	def __init__(self, clipPathUnits:str = ht._strdef('userSpaceOnUse'), **attribs):
		super().__init__(clipPathUnits=clipPathUnits, **attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		# Draw nothing
		return

	def apply(self, surface:ht.Surface, target:_Element):
		surface.context.save()
		clipPathUnits = self['clipPathUnits'].strip()
		if clipPathUnits == 'objectBoundingBox':
			tx, ty, tw, th = target.boundingBox().xywh
			surface.context.translate(tx, ty)
			surface.context.scale(tw, th)
			clipVP = helpers.coordinates.Viewport(width=1, height=1)
		else:
			if clipPathUnits != 'userSpaceOnUse':
				print(f'warning: invalid attribute value: clipPathUnits="{clipPathUnits}"')
			clipVP = target._getViewport()

		for child in self._children:
			child.draw(surface, paint=False, viewport=clipVP)
		surface.context.restore()

		# TODO: fill rules are not handled by cairo for clips
		# fillRule = self.getAttribute('fill-rule', 'nonzero', cascade=True)
		# assert fillRule in helpers.attribs.FILL_RULES
		# surface.context.set_fill_rule(helpers.attribs.FILL_RULES[fillRule])
		surface.context.clip()

	@contextmanager
	def applyContext(self, surface:ht.Surface, target:_Element):
		surface.context.save()
		try:
			self.apply(surface, target)
			yield self
		finally:
			surface.context.restore()


class Mask(_Element):
	tag = 'mask'
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + ['maskUnits', 'maskContentUnits', 'x', 'y', 'width', 'height']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']

	def __init__(self, x:ht.Length = ht._strdef('-10%'), y:ht.Length = ht._strdef('-10%'),
	             width:ht.Length = ht._strdef('120%'), height:ht.Length = ht._strdef('120%'), *,
	             maskUnits:str = ht._strdef('objectBoundingBox'),
	             maskContentUnits:str = ht._strdef('userSpaceOnUse'), **attribs):
		super().__init__(maskUnits=maskUnits, maskContentUnits=maskContentUnits,
		                 x=x, y=y, width=width, height=height, **attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		# Draw nothing
		return

	def apply(self, surface:ht.Surface, target:_Element):
		maskUnits = self['maskUnits'].strip()
		maskContentUnits = self['maskContentUnits'].strip()
		if maskUnits == 'userSpaceOnUse':
			# The spec specifies the invoking element's viewport
			# (https://drafts.fxtf.org/css-masking/#element-attrdef-mask-maskunits);
			# MDN conflictingly specifies the mask's own viewport
			# (https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/maskUnits)
			vp = target._getViewport()
			x      = _size(self['x']     , vp, 'x')
			y      = _size(self['y']     , vp, 'y')
			width  = _size(self['width'] , vp, 'x')
			height = _size(self['height'], vp, 'y')
		else:
			# objectBoundingBox: fractions or percentages of target's size
			# (as if in a "0 0 1 1" viewbox)
			if maskUnits != 'objectBoundingBox':
				print(f'warning: invalid attribute value: maskUnits="{maskUnits}"')
			tx, ty, tw, th = target.boundingBox().xywh
			x      = tw * _size(self['x']     , reference=1) + tx
			y      = th * _size(self['y']     , reference=1) + ty
			width  = tw * _size(self['width'] , reference=1)
			height = th * _size(self['height'], reference=1)

		maskSurface = helpers.surface.createSurface('recording', x=x, y=y, width=width, height=height)
		if maskContentUnits == 'objectBoundingBox':
			tx, ty, tw, th = target.boundingBox().xywh
			maskSurface.context.translate(tx, ty)
			maskSurface.context.scale(tw, th)
			maskVP = helpers.coordinates.Viewport(width=1, height=1)
		else:
			if maskContentUnits != 'userSpaceOnUse':
				print(f'warning: invalid attribute value: maskContentUnits="{maskContentUnits}"')
			maskVP = target._getViewport()

		for child in self._children:
			# todo: pass-through for viewport
			child.draw(maskSurface, viewport=maskVP)

		# uses alpha instead of luminance?
		surface.context.mask_surface(maskSurface)

	@contextmanager
	def applyContext(self, surface:ht.Surface, target:_Element):
		surface.context.save()
		try:
			self.apply(surface, target)
			yield self
		finally:
			surface.context.restore()
