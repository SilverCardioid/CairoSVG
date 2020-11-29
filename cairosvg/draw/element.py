from .path import Path

def path(parent, *args, **kwargs):
	return PathElement(parent, *args, **kwargs)
def svg(parent=None, *args, **kwargs):
	return SVGElement(parent, *args, **kwargs)



class Element:
	def __init__(self, parent, *args, **kwargs):
		self.children = []
		if parent is not None:
			self.parent = parent
			self.parent.children.append(self)
		self.root = parent.root if hasattr(parent, 'root') else parent

		# Core attributes: id, lang, tabindex, xml:base, xml:lang, xml:space
		if 'id'	in kwargs:
			self.id = kwargs['id']
			if self.id in self.root.globals['ids']:
				print('warning: duplicate ID ignored: ' + self.id)
			else:
				self.root.globals['ids'][self.id] = self

class SVGElement(Element):
	def __init__(self, parent=None, *args, **kwargs):
		Element.__init__(self, parent, *args, **kwargs)
	path = path

class PathElement(Path, Element):
	def __init__(self, parent, *args, **kwargs):
		Element.__init__(self, parent, *args, **kwargs)
		super().__init__(parent, *args, **kwargs)
