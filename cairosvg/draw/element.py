class Element:
	def __init__(self, *, parent=None, **attribs):
		self.parent = None
		self.children = []
		self.root = self
		if parent is not None:
			# child
			self.parent = parent
			self.parent.children.append(self)
			self.root = parent.root
		else:
			# root
			self.globals = {'ids':{}}

		self.attribs = attribs
		if 'id'	in attribs:
			self.id = attribs['id']
			if self.id in self.root.globals['ids']:
				print('warning: duplicate ID ignored: ' + self.id)
			else:
				self.root.globals['ids'][self.id] = self

	def getAttribute(self, attrib, default=None):
		node = self
		while attrib not in node.attribs:
			node = node.parent
			if node is None:
				# root reached
				return default

		value = node.attribs[attrib]
		return value if value is not None else default

class StructureElement(Element):
	def draw(self, surface):
		for child in self.children:
			child.draw(surface)