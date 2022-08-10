import sys
from . import _creators
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content

class _Element:
	_strAttrib = {}

	def __init__(self, *, parent=None, childIndex=None, surface=None, **attribs):
		# Tree structure
		self.parent = parent
		self.children = []
		if parent is not None:
			# child
			if childIndex is not None:
				self.parent.children.insert(childIndex, self)
			else:
				self.parent.children.append(self)
			self._root = parent._root
		else:
			# root
			self._root = helpers.root.Root(self)
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
			attrib = helpers.attribs.parseAttribute(key)
			if attrib in self.__class__.attribs:
				self._attribs[attrib] = attribs[key]
			else:
				raise AttributeError(f'<{self.tag}> element doesn\'t take {attrib} attribute')

		if 'id' in attribs:
			self._setID(attribs['id'])

		if 'transform' in self.__class__.attribs:
			self._setTransform()

	def _getOutgoingRefs(self):
		return []

	def _getSurface(self):
		if not self.root.surface:
			raise Exception('Surface needed for drawing')
		return self.root.surface

	def _getViewport(self):
		elem = self.parent
		while elem and not hasattr(elem, 'viewport'):
			elem = elem.parent
		return elem and elem.viewport

	def _setTransform(self):
		self.transform = helpers.transform.Transform(self._attribs.get('transform', None),
		                                             parent=self)

	def _setID(self, value):
		if value in self._root._ids:
			print('warning: duplicate ID ignored: ' + value)
		else:
			self._root._ids[value] = self

	def _setAutoID(self):
		# Find the first free ID of the form tag+number
		i = 1
		eid = self.tag + str(i)
		while eid in self._root._ids:
			i += 1
			eid = self.tag + str(i)
		self._attribs['id'] = eid
		self._setID(eid)

	def _tagCode(self, *, close=True, namespaceDeclaration=True):
		string = '<' + self.tag
		if namespaceDeclaration and self.isRoot():
			nss = ['xmlns'] + helpers.attribs.getNamespaces(self)
			for ns in nss:
				key = ns
				if key != 'xmlns':
					key = 'xmlns:' + key
				if ns not in helpers.attribs.NAMESPACES:
					print(f'warning: unknown namespace: {ns}')
					continue
				val = helpers.attribs.NAMESPACES[ns]
				if val:
					string += f' {key}="{val}"'
		for attr in self._attribs:
			val = self._attribs[attr]
			if attr in self.__class__._strAttrib:
				val = self.__class__._strAttrib[attr](val)
				if val is None:
					# don't print
					continue
			elif val is None:
				val = 'none'
			elif isinstance(val, helpers._Default):
				# don't print
				continue
			string += f' {attr}="{val}"'
		string += '/>' if close else '>'
		return string

	def __getitem__(self, key):
		return self._attribs[helpers.attribs.parseAttribute(key)]

	def __setitem__(self, key, value):
		attrib = helpers.attribs.parseAttribute(key)
		if attrib in self.__class__.attribs:
			prevValue = self._attribs.get(attrib, None)
			self._attribs[attrib] = value

			if attrib == 'id':
				try:
					del self._root._ids[prevValue]
				except KeyError:
					pass
				self._setID(value)
			elif attrib == 'transform':
				self.transform._clear()
				self.transform._transform(value)
		else:
			raise AttributeError(f'<{self.tag}> element doesn\'t take {attrib} attribute')

	def __delitem__(self, key):
		attrib = helpers.attribs.parseAttribute(key)
		value = self._attribs.get(attrib, None)
		del self._attribs[attrib]

		if attrib == 'id':
			try:
				del self._root._ids[value]
			except KeyError:
				pass
		elif attrib == 'transform':
			self.transform._clear()

	def __repr__(self):
		return self._tagCode()

	@property
	def id(self):
		return self._attribs.get('id', None)
	@id.setter
	def id(self, value):
		self['id'] = value
	@id.deleter
	def id(self):
		del self['id']

	@property
	def root(self):
		return self._root.element

	def isRoot(self):
		return self.root is self

	def delete(self, recursive=True):
		"""Delete this element from the tree"""
		if self.parent:
			self.parent.children.remove(self)
			if self.id:
				del self._root._ids[self.id]

		if recursive:
			for child in self.children:
				child.delete()
		else:
			for child in self.children:
				child.detach()
			self._root._updateIDs()

	def detach(self):
		"""Disconnect this element and its descendants from the tree"""
		parent = self.parent
		if parent:
			self.parent = None
			self._root = helpers.root.Root(self)
			self._root._updateIDs()
			for eid in self._root._ids:
				del parent._root._ids[eid]

	def getAttribute(self, attrib, default=None, *, cascade=True):
		"""Get the value of an attribute, inheriting the value from the element's ancestors if cascade=True"""
		attrib = helpers.attribs.parseAttribute(attrib)
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

	def getReferences(self):
		refs = []
		for e in self._root._element.descendants():
			outRefs = e._getOutgoingRefs()
			for refTarget, refAttrib in outRefs:
				if refTarget is self:
					refs.append((e, refAttrib))
		return refs

	def addChild(self, tag, *attribs, childIndex=None, **kwattribs):
		"""Add a child element to this element"""
		if isinstance(tag, _Element):
			if tag.parent:
				tag.detach()
			if childIndex is not None:
				self.children.insert(childIndex, tag)
			else:
				self.children.append(tag)
			tag.parent = self

			idConflicts = tag._root._ids.keys() & self._root._ids.keys()
			if idConflicts:
				print('warning: duplicate ids ignored: ' + ', '.join(idConflicts))
				for eid in idConflicts:
					del tag._root._ids[eid]
			self._root._ids.update(tag._root._ids)
			tag._root = self._root

		else:
			from . import elements
			if tag not in elements:
				raise ValueError('unknown tag: {}'.format(tag))
			return elements[tag](parent=self, childIndex=childIndex, *attribs, **kwattribs)

	def code(self, file=None, *, indent='', indentDepth=0, newline='\n',
	                             xmlDeclaration=False, namespaceDeclaration=True):
		"""Write the SVG code for this element and its children to the screen or to an opened file"""
		indent = indent or ''
		newline = newline or ''
		indentation = indentDepth*indent

		if not file:
			file = sys.stdout

		if xmlDeclaration:
			decl = '<?xml version="1.0" encoding="UTF-8"?>'
			file.write(f'{indentation}{decl}{newline}')

		tagCode = self._tagCode(close=len(self.children)==0, namespaceDeclaration=namespaceDeclaration)
		file.write(f'{indentation}{tagCode}{newline}')
		if len(self.children) > 0:
			for child in self.children:
				child.code(file, indent=indent, indentDepth=indentDepth+1, newline=newline)
			tagClose = f'</{self.tag}>'
			file.write(f'{indentation}{tagClose}{newline}')

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
		vp = self._getViewport()
		opacity = float(self.getAttribute('opacity', 1))
		assert 0 <= opacity <= 1
		fillOpacity = float(self.getAttribute('fill-opacity', 1))
		assert 0 <= fillOpacity <= 1
		strokeOpacity = float(self.getAttribute('stroke-opacity', 1))
		assert 0 <= strokeOpacity <= 1

		fill = helpers.colors.color(self.getAttribute('fill', '#000'), fillOpacity*opacity)
		fillRule = self.getAttribute('fill-rule', 'nonzero')
		assert fillRule in helpers.attribs.FILL_RULES

		stroke = helpers.colors.color(self.getAttribute('stroke', 'none'), strokeOpacity*opacity)
		strokeWidth = helpers.coordinates.size2(self.getAttribute('stroke-width', 1), vp, 'xy')
		strokeLinecap = self.getAttribute('stroke-linecap', 'butt')
		assert strokeLinecap in helpers.attribs.LINE_CAPS
		strokeLinejoin = self.getAttribute('stroke-linejoin', 'miter')
		assert strokeLinejoin in helpers.attribs.LINE_JOINS

		dashArray = helpers.attribs.normalize(self.getAttribute('stroke-dasharray', '')).split()
		if dashArray:
			dashes = [helpers.coordinates.size2(dash, vp, 'xy') for dash in dashArray]
			if sum(dashes):
				offset = helpers.coordinates.size2(self.getAttribute('stroke-dashoffset'), vp, 'xy')
				surface.context.set_dash(dashes, offset)

		surface.context.set_source_rgba(*fill)
		surface.context.set_fill_rule(helpers.attribs.FILL_RULES[fillRule])
		surface.context.fill_preserve()

		surface.context.set_source_rgba(*stroke)
		surface.context.set_line_width(strokeWidth)
		surface.context.set_line_cap(helpers.attribs.LINE_CAPS[strokeLinecap])
		surface.context.set_line_join(helpers.attribs.LINE_JOINS[strokeLinejoin])
		surface.context.stroke()

