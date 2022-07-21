import sys
from . import _creators, transform
from .modules import attrib as _attrib, content as _content
from .. import colors, helpers

class _Element:
	_strAttrib = {}

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
			self._globals = {'ids':{}}
			self.surface = surface

		# Allowed children
		for tag in self.__class__.content:
			try:
				setattr(self, tag, _creators[tag].__get__(self, self.__class__))
			except KeyError:
				pass

		# Attributes
		self._attribs = {}
		for key in attribs:
			attrib = helpers.parseAttribute(key)
			if attrib in self.__class__.attribs:
				self._attribs[attrib] = attribs[key]
			else:
				raise AttributeError(f'<{self.tag}> element doesn\'t take {attrib} attribute')

		if 'id' in attribs:
			self._setID(attribs['id'])

		if 'transform' in self.__class__.attribs:
			self._setTransform()

	def _getSurface(self):
		if not self.root.surface:
			raise Exception('Surface needed for drawing')
		return self.root.surface

	def _setTransform(self):
		self.transform = transform.Transform(self._attribs.get('transform', None),
		                                     parent=self)

	def _setID(self, value):
		if value in self.root._globals['ids']:
			print('warning: duplicate ID ignored: ' + value)
		else:
			self.root._globals['ids'][value] = self

	def _setAutoID(self):
		# Find the first free ID of the form tag+number
		i = 1
		eid = self.tag + str(i)
		while eid in self.root._globals['ids']:
			i += 1
			eid = self.tag + str(i)
		self._attribs['id'] = eid
		self._setID(eid)

	def __getitem__(self, key):
		return self._attribs[helpers.parseAttribute(key)]

	def __setitem__(self, key, value):
		attrib = helpers.parseAttribute(key)
		if attrib in self.__class__.attribs:
			prevValue = self._attribs.get(attrib, None)
			self._attribs[attrib] = value

			if attrib == 'id':
				try:
					del self.root._globals['ids'][prevValue]
				except KeyError:
					pass
				self._setID(value)
			elif attrib == 'transform':
				self.transform._clear()
				self.transform._transform(value)
		else:
			raise AttributeError(f'<{self.tag}> element doesn\'t take {attrib} attribute')

	def __delitem__(self, key):
		attrib = helpers.parseAttribute(key)
		value = self._attribs.get(attrib, None)
		del self._attribs[attrib]

		if attrib == 'id':
			try:
				del self.root._globals['ids'][value]
			except KeyError:
				pass
		elif attrib == 'transform':
			self.transform._clear()

	@property
	def id(self):
		return self._attribs.get('id', None)
	@id.setter
	def id(self, value):
		self['id'] = value
	@id.deleter
	def id(self):
		del self['id']

	def delete(self, recursive=True):
		"""Delete this element from the tree"""
		if self.parent: self.parent.children.remove(self)
		if recursive:
			for child in self.children: child.delete()
		else:
			for child in self.children: child.parent = None

	def getAttribute(self, attrib, default=None, *, cascade=True):
		"""Get the value of an attribute, inheriting the value from the element's ancestors if cascade=True"""
		attrib = helpers.parseAttribute(attrib)
		if cascade:
			node = self
			while attrib not in node._attribs:
				node = node.parent
				if node is None:
					# root reached
					return default
			return node._attribs[attrib] #value if value is not None else default
		else:
			return self._attribs.get(attrib, default)

	def addChild(self, tag, *attribs, **kwattribs):
		"""Add a child element to this element"""
		from . import elements
		try:
			return elements[tag](parent=self, *attribs, **kwattribs)
		except KeyError:
			raise ValueError('unknown tag: {}'.format(tag))

	def code(self, file=None, *, indent='', indentDepth=0, newline='\n', xmlDeclaration=False):
		"""Write the SVG code for this element and its children to the screen or to an opened file"""
		indent = indent or ''
		newline = newline or ''

		if not file:
			file = sys.stdout

		if xmlDeclaration:
			file.write('<?xml version="1.0" encoding="UTF-8"?>{}'.format(newline))

		file.write('{}<{}'.format(indentDepth*indent, self.tag))
		for attr in self._attribs:
			val = self._attribs[attr]
			if attr in self.__class__._strAttrib:
				val = self.__class__._strAttrib[attr](val)
			elif val is None:
				val = 'none'
			file.write(' {}="{}"'.format(attr, val))
		if len(self.children) == 0:
			file.write('/>{}'.format(newline))
		else:
			file.write('>{}'.format(newline))
			for child in self.children:
				child.code(file, indent=indent, indentDepth=indentDepth+1, newline=newline)
			file.write('{}</{}>{}'.format(indentDepth*indent, self.tag, newline))

	def descendants(self):
		yield self
		for child in self.children:
			yield from child.descendants()

	def find(self, function, *, maxResults=None):
		results = []
		for elem in self.descendants():
			if function(elem):
				results.append(elem)
				if maxResults and len(results) >= maxResults:
					break
		return results


class _StructureElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + _attrib['GraphicalEvents']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['View'] + _content['Conditional'] + _content['Hyperlink'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		for child in self.children:
			child.draw(surface)


class _ShapeElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['GraphicalEvents'] + _attrib['Paint'] + _attrib['Opacity'] + _attrib['Graphics'] + _attrib['Cursor'] + _attrib['Filter'] + _attrib['Mask'] + _attrib['Clip']
	content = _content['Description'] + _content['Animation']

	def _paint(self, surface):
		opacity = float(self.getAttribute('opacity', 1))
		assert 0 <= opacity <= 1
		fillOpacity = float(self.getAttribute('fill-opacity', 1))
		assert 0 <= fillOpacity <= 1
		strokeOpacity = float(self.getAttribute('stroke-opacity', 1))
		assert 0 <= strokeOpacity <= 1

		fill = colors.color(self.getAttribute('fill', '#000'), fillOpacity*opacity)
		fillRule = self.getAttribute('fill-rule', 'nonzero')
		assert fillRule in helpers.FILL_RULES

		stroke = colors.color(self.getAttribute('stroke', 'none'), strokeOpacity*opacity)
		strokeWidth = float(self.getAttribute('stroke-width', 1))
		strokeLinecap = self.getAttribute('stroke-linecap', 'butt')
		assert strokeLinecap in helpers.LINE_CAPS
		strokeLinejoin = self.getAttribute('stroke-linejoin', 'miter')
		assert strokeLinejoin in helpers.LINE_JOINS

		dashArray = helpers.normalize(self.getAttribute('stroke-dasharray', '')).split()
		if dashArray:
			dashes = [helpers.size(surface, dash) for dash in dashArray]
			if sum(dashes):
				offset = helpers.size(surface, self.getAttribute('stroke-dashoffset'))
				surface.context.set_dash(dashes, offset)

		surface.context.set_source_rgba(*fill)
		surface.context.set_fill_rule(helpers.FILL_RULES[fillRule])
		surface.context.fill_preserve()

		surface.context.set_source_rgba(*stroke)
		surface.context.set_line_width(strokeWidth)
		surface.context.set_line_cap(helpers.LINE_CAPS[strokeLinecap])
		surface.context.set_line_join(helpers.LINE_JOINS[strokeLinejoin])
		surface.context.stroke()

