import typing as ty

from .element import _Element, _StructureElement
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content
from ..helpers.coordinates import size as _size
from ..helpers import types as ht

class G(_StructureElement):
	tag = 'g'
	attribs = _StructureElement.attribs + ['transform']
	content = _StructureElement.content

	def __init__(self, **attribs):
		_Element.__init__(self, **attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		with self._applyTransformations(surface):
			for child in self._children:
				child.draw(surface, paint=paint, viewport=viewport)


class Defs(_StructureElement):
	tag = 'defs'
	attribs = _StructureElement.attribs + ['transform'] # can have transform according to spec?
	content = _StructureElement.content

	def __init__(self, **attribs):
		_Element.__init__(self, **attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		# Draw nothing
		return

	def boundingBox(self) -> ht.Box():
		# No box
		return ht.Box()

_HREF = f'{{{helpers.namespaces.NS_XLINK}}}href'
class Use(_Element):
	tag = 'use'
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['XLinkEmbed'] + _attrib['Presentation'] + _attrib['GraphicalEvents'] + ['transform','x','y','width','height']
	content = _content['Description'] + _content['Animation']
	_strAttrib = {
		_HREF: lambda val: ('#' + val if val and val[0] != '#'
		                    else val) if isinstance(val, str) else \
		                    '#' + val.id if isinstance(val, _Element) \
		                    else ''
	}

	def __init__(self, href:ty.Union[str,_Element,None] = ht._strdef(''), *,
	             x:ht.Length = ht._intdef(0), y:ht.Length = ht._intdef(0),
	             width:ht.Length = ht._intdef(0), height:ht.Length = ht._intdef(0), **attribs):
		_Element.__init__(self, href=href, x=x, y=y, width=width, height=height, **attribs)

		# Make sure the target has an id, in case
		# an element object is passed for href
		target = self.target
		if target and not target.id:
			target._setAutoID()

	def __setitem__(self, key:str, value:ty.Any):
		super().__setitem__(key, value)
		if helpers.attribs.parseAttribute(key) == _HREF:
			target = self.target
			if target and not target.id:
				target._setAutoID()

	def _getOutgoingRefs(self) -> ty.List[ty.Tuple[_Element, str]]:
		refs = super()._getOutgoingRefs()
		target = self.target
		if target:
			refs.append((target, _HREF))
		return refs

	@property
	def target(self) -> ty.Optional[_Element]:
		href = self._attribs.get(_HREF, None)
		if isinstance(href, str):
			if href[0] == '#':
				href = href[1:]
			try:
				return self._root._ids[href]
			except KeyError:
				# not found
				return None
		elif isinstance(href, _Element):
			return href
		# unknown type
		return None

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		vp = viewport or self._getViewport()
		target = self.target

		if target is None:
			href = self._attribs.get(_HREF, None)
			if href:
				print('<use> referencing unknown id or invalid object: {}'.format(href))
			return

		# Draw target element in the context of the <use>
		x, y = _size(self['x'], vp, 'x'), _size(self['y'], vp, 'y')
		targetParent = target._parent
		target._parent = self
		self.transform._translate(x, y)
		with self.transform.applyContext(surface):
			target.draw(surface, paint=paint, viewport=vp)
		target._parent = targetParent
		self.transform._translate(-x, -y)

	def boundingBox(self) -> ht.Box:
		target = self.target
		if target is None:
			# Broken references have a bounding box according to the use's attributes
			x, y = _size(self['x'], vp, 'x'), _size(self['y'], vp, 'y')
			width, height = _size(self['width'], vp, 'x'), _size(self['height'], vp, 'y')
			return ht.Box(x, y, width, height)
		else:
			box = target.boundingBox()
			if box.defined:
				# Shift box according to x and y attribs
				vp = self._getViewport()
				x, y = _size(self['x'], vp, 'x'), _size(self['y'], vp, 'y')
				box.x0 += x; box.y0 += y
				box.x1 += x; box.y1 += y
			return self._transformBox(box)
