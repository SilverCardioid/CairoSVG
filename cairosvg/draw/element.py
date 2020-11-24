class Element:
	def __init__(self, parent, **attributes):
		self.parent = parent
		self.root = parent.root if hasattr(parent, 'root') else parent

		# Core attributes: id, lang, tabindex, xml:base, xml:lang, xml:space
		if 'id'	in attributes:
			self.id = attributes['id']
			if self.id in self.root.globals['ids']:
				print('warning: duplicate ID ignored: ' + self.id)
			else:
				self.root.globals['ids'][self.id] = self
