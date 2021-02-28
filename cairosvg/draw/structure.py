from .element import Element
from . import transform

class StructureElement(Element):
	def draw(self, surface=None):
		surface = surface or self._getSurface()
		for child in self.children:
			child.draw(surface)

class Group(StructureElement):
	attribs = ['Core','Conditional','Style','External','Presentation','GraphicalEvents','transform']
	children = ['Description','Animation','Structure','Shape','Text','Image','View','Conditional','Hyperlink','Script','Style','Marker','Clip','Mask','Gradient','Pattern','Filter','Cursor','Font','ColorProfile']

	def __init__(self, **attribs):
		self.tag = 'g'
		Element.__init__(self, **attribs)
		self.transform = transform.Transform(self.getAttribute('transform', None, False), parent=self)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		with self.transform.applyContext(surface):
			for child in self.children:
				child.draw(surface)

class Use(Element):
	attribs = ['Core','Conditional','Style','XLinkEmbed','Presentation','GraphicsElementEventAttrs','transform','x','y','width','height']
	children = ['Description','Animation']

	def __init__(self, href=None, x=0, y=0, width=0, height=0, **attribs):
		self.tag = 'use'
		Element.__init__(self, href=href, x=x, y=y, width=width, height=height, **attribs)
		self.transform = transform.Transform(self.getAttribute('transform', None, False), parent=self)
		self.transform.translate(x, y)

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		target = self.attribs['href']
		if type(target) is str:
			if target[0] == '#':
				target = target[1:]
			try:
				target = self.root.globals['ids'][target]
			except KeyError:
				raise ValueError('<use> referencing unknown id: {}'.format(target))

		# Draw target element in the context of the <use>
		targetParent = target.parent
		target.parent = self
		with self.transform.applyContext(surface):
			target.draw(surface)
		target.parent = targetParent
