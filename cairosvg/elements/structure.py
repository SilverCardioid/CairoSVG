import typing as ty

from .element import _Element, _StructureElement
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content
from ..helpers.coordinates import size as _size
from ..helpers import types as ht

class G(_StructureElement):
	"""<g> element.
	A generic structure element to group content together.

	Main attributes:
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'g'
	attribs = _StructureElement.attribs + ['transform']
	content = _StructureElement.content

	def __init__(self, **attribs):
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		with self._applyTransformations(surface):
			for child in self._children:
				child.draw(surface, paint=paint, viewport=viewport)


class Defs(_StructureElement):
	"""<defs> element.
	A structure element whose contents are not drawn directly,
	but can still be referenced elsewhere in the document.
	
	Conventionally used for shapes and groups to be reused via
	<use> elements, as well as for definitions for clipPaths,
	gradients etc.
	"""
	tag = 'defs'
	attribs = _StructureElement.attribs + ['transform'] # can have transform according to spec?
	content = _StructureElement.content

	def __init__(self, **attribs):
		super().__init__(**attribs)

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		# Draw nothing
		return

	def boundingBox(self) -> ht.Box():
		# No box
		return ht.Box()

_HREF = f'{{{helpers.namespaces.NS_XLINK}}}href'
class Use(_Element):
	"""<use> element.
	An element that draws a copy of another element.

	Main attributes:
	* xlink:href: a reference to the target element. Can be a string of
	    the form '#target_id', or an element object.
	* x, y: translation offset; i.e., the position of the copy relative
	    to the target.
	* width, height: the size of the <use>. Only has a visual effect if
	    the target is an <svg> or <marker>; to change the size of other
	    elements, use the transform attribute.
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).

	Notes:
	Technically, the <use> contains a virtual copy of the target element
	and its descendants. This means the target's attribute values will
	not be overridden for the copy, but missing values will be inherited
	from the <use> and its ancestors instead of the target's ancestors.
	For example, to make a copy with a different fill color, you'd do:
	```
	<g fill="red">
	    <rect id="door" width="10" height="20"/>
	</g>
	<use xlink:href="#door" fill="black"/>
	```
	"""
	tag = 'use'
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['XLinkEmbed'] + _attrib['Presentation'] + _attrib['GraphicalEvents'] + ['transform','x','y','width','height']
	content = _content['Description'] + _content['Animation']
	_defaults = {**_Element._defaults,
		_HREF: None,
		'x': 0,
		'y': 0,
		'width': 0,
		'height': 0,
	}
	_strAttrib = {
		_HREF: lambda val: ('#' + val if val and val[0] != '#'
		                    else val) if isinstance(val, str) else \
		                    '#' + val.id if isinstance(val, _Element) \
		                    else ''
	}

	def __init__(self, href_:ty.Union[str,_Element,None] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, **{_HREF:href_})
		super().__init__(**attribs)

		# Make sure the target has an id, in case
		# an element object is passed for href
		target = self.target
		if target and not target.id:
			target._setAutoID()

	def __setitem__(self, key:str, value:ty.Any):
		super().__setitem__(key, value)
		if self._parseAttribute(key) == _HREF:
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
		x = _size(self._getattrib('x'), vp, 'x')
		y = _size(self._getattrib('y'), vp, 'y')
		targetParent = target._parent
		try:
			target._parent = self
			self.transform._translate(x, y)
			with self.transform.applyContext(surface):
				target.draw(surface, paint=paint, viewport=vp)
			self.transform._translate(-x, -y)
		finally:
			target._parent = targetParent

	def boundingBox(self) -> ht.Box:
		target = self.target
		if target is None:
			# Broken references have a bounding box according to the use's attributes
			x = _size(self._getattrib('x'), vp, 'x')
			y = _size(self._getattrib('y'), vp, 'y')
			width = _size(self._getattrib('width'), vp, 'x')
			height = _size(self._getattrib('height'), vp, 'y')
			return ht.Box(x, y, width, height)
		else:
			box = target.boundingBox()
			if box.defined:
				# Shift box according to x and y attribs
				vp = self._getViewport()
				x = _size(self._getattrib('x'), vp, 'x')
				y = _size(self._getattrib('y'), vp, 'y')
				box.x0 += x; box.y0 += y
				box.x1 += x; box.y1 += y
			return self._transformBox(box)
