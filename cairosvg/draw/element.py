import sys
from . import _creators
from .. import helpers

class Element:
	def __init__(self, *, parent=None, surface=None, **attribs):
		# Tree structure
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
			self.surface = surface

		# Allowed children
		for tag in self.__class__.content:
			try:
				setattr(self, tag, _creators[tag].__get__(self, self.__class__))
			except KeyError:
				pass

		# Attributes
		self.attribs = {}
		for key in attribs:
			attrib = helpers.parseAttribute(key)
			if attrib in self.__class__.attribs:
				self.attribs[attrib] = attribs[key]
			else:
				raise AttributeError(f'{self.tag} element doesn\'t take {attrib} attribute')

		if 'id'	in attribs:
			self.id = attribs['id']
			if self.id in self.root.globals['ids']:
				print('warning: duplicate ID ignored: ' + self.id)
			else:
				self.root.globals['ids'][self.id] = self

	def _getSurface(self):
		if not self.root.surface:
			raise Exception('Surface needed for drawing')
		return self.root.surface

	def __getitem__(self, key):
		return self.attribs[key]

	def __setitem__(self, key, value):
		self.attribs[key] = value

	def __delitem__(self, key):
		del self.attribs[key]

	def delete(self, recursive=True):
		if self.parent: self.parent.children.remove(self)
		if recursive:
			for child in self.children: child.delete()
		else:
			for child in self.children: child.parent = None

	def getAttribute(self, attrib, default=None, cascade=True):
		if cascade:
			node = self
			while attrib not in node.attribs:
				node = node.parent
				if node is None:
					# root reached
					return default
			value = node.attribs[attrib]
			return value if value is not None else default
		else:
			return self.attribs.get(attrib, default)

	def addChild(self, tag, *attribs, **kwattribs):
		from .elements import elements
		try:
			return elements[tag](parent=self, *attribs, **kwattribs)
		except KeyError:
			raise ValueError('unknown tag: {}'.format(tag))

	def code(self, file=sys.stdout, indent='', indentDepth=0, newline='\n', xmlDeclaration=False):
		indent = indent or ''
		newline = newline or ''

		if xmlDeclaration:
			file.write('<?xml version="1.0" encoding="UTF-8"?>{}'.format(newline))

		file.write('{}<{}'.format(indentDepth*indent, self.tag))
		for attr in self.attribs:
			file.write(' {}="{}"'.format(attr, self.attribs[attr]))
		if len(self.children) == 0:
			file.write('/>{}'.format(newline))
		else:
			file.write('>{}'.format(newline))
			for child in self.children:
				child.code(file, indent, indentDepth+1, newline)
			file.write('{}</{}>{}'.format(indentDepth*indent, self.tag, newline))
