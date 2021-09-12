from .element import Element, StructureElement
from .modules import attrib, content
from . import transform

class Group(StructureElement):
	attribs = StructureElement.attribs + ['transform']
	content = StructureElement.content

	def __init__(self, **attribs):
		self.tag = 'g'
		Element.__init__(self, **attribs)
		self._setTransform()

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		with self.transform.applyContext(surface):
			for child in self.children:
				child.draw(surface)

class Use(Element):
	attribs = attrib['Core'] + attrib['Conditional'] + attrib['Style'] + attrib['XLinkEmbed'] + attrib['Presentation'] + attrib['GraphicalEvents'] + ['transform','x','y','width','height']
	content = content['Description'] + content['Animation']

	def __init__(self, href=None, x=0, y=0, width=0, height=0, **attribs):
		self.tag = 'use'
		Element.__init__(self, href=href, x=x, y=y, width=width, height=height, **attribs)
		self._setTransform()

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		target = self.attribs['xlink:href']
		if type(target) is str:
			if target[0] == '#':
				target = target[1:]
			try:
				target = self.root.globals['ids'][target]
			except KeyError:
				raise ValueError('<use> referencing unknown id: {}'.format(target))

		# Draw target element in the context of the <use>
		x, y = self.attribs['x'], self.attribs['y']
		targetParent = target.parent
		target.parent = self
		self.transform.translate(x, y)
		with self.transform.applyContext(surface):
			target.draw(surface)
		target.parent = targetParent
		self.transform.translate(-x, -y)
