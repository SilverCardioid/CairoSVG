import math
import sys

from . import _creators
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content

class _Element:
	_strAttrib = {}

	def __init__(self, *, parent=None, childIndex=None, **attribs):
		# Tree structure
		self._parent = parent
		self._children = []
		if parent is not None:
			# child
			if childIndex is not None:
				self.parent._children.insert(childIndex, self)
			else:
				self.parent._children.append(self)
			self._root = parent._root
		else:
			# root
			self._root = helpers.root.Root(self)

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

	def _getAutoID(self, prefix=None, idList=None):
		# Find the first free ID of the form prefix+number
		prefix = prefix or self.tag
		if prefix[-1].isnumeric():
			# Add a separator if the prefix ends with a number
			prefix += '_'
		if idList is None:
			idList = self._root._ids.keys()

		i = 1
		eid = prefix + str(i)
		while eid in idList:
			i += 1
			eid = prefix + str(i)
		return eid

	def _setAutoID(self, prefix=None, idList=None):
		eid = self._getAutoID(prefix, idList)
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
		return self._tagCode(namespaceDeclaration=False)

	@property
	def parent(self):
		return self._parent
	@parent.setter
	def parent(self, elem):
		elem.addChild(self)

	@property
	def children(self):
		return tuple(self._children)

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

	def changeID(self, newID=None, updateRefs=True):
		curID = self.id
		if curID and updateRefs:
			refs = self.getReferences()

		if newID:
			self.id = newID
		else:
			self._setAutoID(curID)

		if curID and updateRefs:
			for refElem, refAttrib in refs:
				if refAttrib in refElem._strAttrib:
					refElem[refAttrib] = refElem._strAttrib[refAttrib](self)
				else:
					refElem[refAttrib] = self

	def delete(self, recursive=True):
		"""Delete this element from the tree"""
		if self.parent:
			self.parent._children.remove(self)
			if self.id:
				del self._root._ids[self.id]

		if recursive:
			while len(self._children) > 0:
				self._children[-1].delete()
		else:
			while len(self._children) > 0:
				self._children[-1].detach()
			self._root._updateIDs()

	def detach(self):
		"""Disconnect this element and its descendants from the tree"""
		parent = self.parent
		if parent:
			self._parent = None
			parent._children.remove(self)
			self._root = helpers.root.Root(self)
			self._root._updateIDs()
			for eid in self._root._ids:
				del parent._root._ids[eid]
			for e in self.descendants():
				e._root = self._root

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
		for e in self._root.element.descendants():
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
				self._children.insert(childIndex, tag)
			else:
				self._children.append(tag)
			tag._parent = self

			idConflicts = tag._root._ids.keys() & self._root._ids.keys()
			if idConflicts:
				print('warning: duplicate ids changed: ' + ', '.join(idConflicts))
				idList = tag._root._ids.keys() | self._root._ids.keys()
				for eid in idConflicts:
					elem = tag._root._ids[eid]
					newID = elem._getAutoID(eid, idList)
					elem.changeID(newID)
			self._root._ids.update(tag._root._ids)
			for e in tag.descendants():
				e._root = self._root

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
		if len(self._children) > 0:
			for child in self._children:
				child.code(file, indent=indent, indentDepth=indentDepth+1, newline=newline)
			tagClose = f'</{self.tag}>'
			file.write(f'{indentation}{tagClose}{newline}')

	def descendants(self, includeSelf=True):
		if includeSelf:
			yield self
		for child in self._children:
			yield from child.descendants(True)

	def ancestors(self, includeSelf=True):
		if includeSelf:
			yield self
		anc = self.parent
		while anc:
			yield anc
			anc = anc.parent

	def find(self, function, *, maxResults=None):
		results = []
		for elem in self.descendants():
			if function(elem):
				results.append(elem)
				if maxResults and len(results) >= maxResults:
					break
		return results

	def findID(self, id):
		res = self._root._ids.get(id, None)
		if res and self in res.ancestors():
			return res
		return None

	def boundingBox(self):
		# Default to no box
		return helpers.geometry.Box()


class _StructureElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + _attrib['GraphicalEvents']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['View'] + _content['Conditional'] + _content['Hyperlink'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']

	def draw(self, surface):
		for child in self._children:
			child.draw(surface)

	def boundingBox(self):
		# todo: account for transformations
		# https://svgwg.org/svg2-draft/coords.html#bounding-box
		box = helpers.geometry.Box()
		for child in self._children:
			box += child.boundingBox()
		return box


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

