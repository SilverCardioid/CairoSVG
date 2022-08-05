from .element import _Element, _StructureElement
from .. import helpers
from ..helpers.coordinates import size2 as _size
from ..helpers.modules import attrib as _attrib, content as _content

class Group(_StructureElement):
	attribs = _StructureElement.attribs + ['transform']
	content = _StructureElement.content

	def __init__(self, **attribs):
		self.tag = 'g'
		_Element.__init__(self, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		with self.transform.applyContext(surface):
			for child in self.children:
				child.draw(surface)

class Defs(_StructureElement):
	attribs = _StructureElement.attribs + ['transform'] # can have transform according to spec?
	content = _StructureElement.content

	def __init__(self, **attribs):
		self.tag = 'defs'
		_Element.__init__(self, **attribs)

	def draw(self, surface=None):
		# Draw nothing
		return

class Use(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['XLinkEmbed'] + _attrib['Presentation'] + _attrib['GraphicalEvents'] + ['transform','x','y','width','height']
	content = _content['Description'] + _content['Animation']
	_strAttrib = {
		'xlink:href': lambda val: ('#' + val if val and val[0] != '#'
		                           else val) if isinstance(val, str) else \
		                           '#' + val.id if isinstance(val, _Element) \
		                           else ''
	}

	def __init__(self, href=helpers._strdef(''), *, x=helpers._intdef(0), y=helpers._intdef(0),
	             width=helpers._intdef(0), height=helpers._intdef(0), **attribs):
		self.tag = 'use'
		_Element.__init__(self, href=href, x=x, y=y, width=width, height=height, **attribs)

		# Make sure the target has an id, in case
		# an element object is passed for href
		target = self.target
		if target and not target.id:
			target._setAutoID()

	def __setitem__(self, key, value):
		super().__setitem__(key, value)
		if helpers.parseAttribute(key) == 'xlink:href':
			target = self.target
			if target and not target.id:
				target._setAutoID()

	@property
	def target(self):
		href = self._attribs.get('xlink:href', None)
		if isinstance(href, str):
			if href[0] == '#':
				href = href[1:]
			try:
				return self.root._globals['ids'][href]
			except KeyError:
				# not found
				return None
		elif isinstance(href, _Element):
			return href
		# unknown type
		return None

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		vp = self._getViewport()
		target = self.target

		if target is None:
			href = self._attribs.get('xlink:href', None)
			if href:
				print('<use> referencing unknown id or invalid object: {}'.format(href))
			return

		# Draw target element in the context of the <use>
		x, y = _size(self['x'], vp, 'x'), _size(self['y'], vp, 'y')
		targetParent = target.parent
		target.parent = self
		self.transform._translate(x, y)
		with self.transform.applyContext(surface):
			target.draw(surface)
		target.parent = targetParent
		self.transform._translate(-x, -y)
