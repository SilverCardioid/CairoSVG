import re
import sys
from .. import helpers

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

		self.attribs = {}
		for key in attribs:
			attrib = helpers.parseAttrib(key)
			self.attribs[attrib] = attribs[key]

		if 'id'	in attribs:
			self.id = attribs['id']
			if self.id in self.root.globals['ids']:
				print('warning: duplicate ID ignored: ' + self.id)
			else:
				self.root.globals['ids'][self.id] = self

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

	def addChild(self, tag, **attribs):
		from .elements import elements
		try:
			return elements[tag](parent=self, **attribs)
		except KeyError:
			raise ValueError('unknown tag: {}'.format(tag))

	def code(self, file=sys.stdout):
		file.write('<{}'.format(self.tag))
		for attr in self.attribs:
			file.write(' {}="{}"'.format(attr, self.attribs[attr]))
		if len(self.children) == 0:
			file.write('/>/n')
		else:
			file.write('>/n')
			for child in self.children:
				child.code(file)
			file.write('</{}>/n'.format(self.tag))
