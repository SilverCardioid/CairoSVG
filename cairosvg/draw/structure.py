from .element import _Element, _StructureElement
from .modules import attrib, content
from .. import helpers

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
	attribs = attrib['Core'] + attrib['Conditional'] + attrib['Style'] + attrib['XLinkEmbed'] + attrib['Presentation'] + attrib['GraphicalEvents'] + ['transform','x','y','width','height']
	content = content['Description'] + content['Animation']
	_strAttrib = {
		'xlink:href': lambda val: ('#' + val if val and val[0] != '#'
		                           else val) if type(val) is str else \
		                           '#' + val.id if isinstance(val, _Element) \
		                           else ''
	}

	def __init__(self, href=None, x=0, y=0, width=0, height=0, **attribs):
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
		if type(href) is str:
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
		target = self.target

		if target is None:
			href = self._attribs.get('xlink:href', None)
			if href:
				print('<use> referencing unknown id or invalid object: {}'.format(href))
			return

		# Draw target element in the context of the <use>
		x, y = self['x'], self['y']
		targetParent = target.parent
		target.parent = self
		self.transform._translate(x, y)
		with self.transform.applyContext(surface):
			target.draw(surface)
		target.parent = targetParent
		self.transform._translate(-x, -y)
