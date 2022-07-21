from .element import _Element, _StructureElement
from .modules import attrib, content

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

	def __init__(self, href=None, x=0, y=0, width=0, height=0, **attribs):
		self.tag = 'use'
		_Element.__init__(self, href=href, x=x, y=y, width=width, height=height, **attribs)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		target = self['xlink:href']
		if type(target) is str:
			if target[0] == '#':
				target = target[1:]
			try:
				target = self.root._globals['ids'][target]
			except KeyError:
				raise ValueError('<use> referencing unknown id: {}'.format(target))

		# Draw target element in the context of the <use>
		x, y = self['x'], self['y']
		targetParent = target.parent
		target.parent = self
		self.transform._translate(x, y)
		with self.transform.applyContext(surface):
			target.draw(surface)
		target.parent = targetParent
		self.transform._translate(-x, -y)
