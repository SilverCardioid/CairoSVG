class Element:
	def __init__(self, *, parent=None, **kwargs):
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

		if 'id'	in kwargs:
			self.id = kwargs['id']
			if self.id in self.root.globals['ids']:
				print('warning: duplicate ID ignored: ' + self.id)
			else:
				self.root.globals['ids'][self.id] = self
