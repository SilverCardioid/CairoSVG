from contextlib import contextmanager
import math
import re
import sys

from . import _creators
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content

class _Element:
	_strAttrib = {}

	def __init__(self, *, parent=None, childIndex=None, **attribs):
		self.namespace = helpers.namespaces.NS_SVG

		# Tree structure
		self._parent = parent
		self._children = []
		if parent is not None:
			# child
			if (parent.__class__.content and (not self.tag or self.tag[0] != '{') and
			    self.tag not in parent.__class__.content):
				print(f'warning: <{parent.tag}> element doesn\'t take "{self.tag}" child element')
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
			attrib = helpers.attribs.parseAttribute(key, namespaces=self._root.namespaces)
			if (self.__class__.attribs and (not attrib or attrib[0] != '{') and
			    attrib not in self.__class__.attribs):
				print(f'warning: <{self.tag}> element doesn\'t take "{attrib}" attribute')
			self._attribs[attrib] = attribs[key]

		if 'id' in attribs:
			self._setID(attribs['id'])

		if 'transform' in self.__class__.attribs:
			self._setTransform()

	def _getOutgoingRefs(self):
		refs = []
		clipPath = self._parseReference(self._attribs.get('clip-path', None))
		if clipPath:
			refs.append(clipPath)
		mask = self._parseReference(self._attribs.get('mask', None))
		if mask:
			refs.append(mask)
		return refs

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
		nss = self._root.namespaces
		nsPrefix = nss._getPrefix(self.namespace)
		if nsPrefix: nsPrefix += ':'
		string = '<' + nsPrefix + self.tag

		if namespaceDeclaration and self.isRoot():
			nsNames = helpers.namespaces.getNamespaces(self)
			ns = [(nss._getPrefix(name), name) for name in nsNames]
			ns.sort()
			for nsPrefix, nsName in ns:
				if nsPrefix == 'xml' and nsName == helpers.namespaces.NS_XML:
					# xml: doesn't need to be declared
					continue
				key = 'xmlns:' + nsPrefix if nsPrefix else 'xmlns'
				string += f' {key}="{nsName}"'

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
			attr = self._root.namespaces.qualifyName(attr, defaultName=self.namespace)
			string += f' {attr}="{val}"'

		string += '/>' if close else '>'
		return string

	def _parseReference(self, value):
		if value is None or value == '':
			return None
		elif isinstance(value, str):
			value = re.sub(r'^url\(#(.+)\)$', r'\1', value)
			if value[0] == '#':
				value = value[1:]
			try:
				return self._root._ids[value]
			except KeyError:
				# not found
				return None
		elif isinstance(value, _Element):
			return value
		# unknown type
		return None

	@contextmanager
	def _applyTransformations(self, surface):
		surface.context.save()
		try:
			if hasattr(self, 'transform') and self.transform._transformed:
				self.transform.apply(surface)

			clipPath = self._attribs.get('clip-path', None)
			if clipPath:
				cpElem = self._parseReference(clipPath)
				if cpElem and cpElem.tag == 'clipPath':
					cpElem.apply(surface, self)
				else:
					print(f'warning: invalid clip-path reference: {clipPath}')

			mask = self._attribs.get('mask', None)
			if mask:
				maskElem = self._parseReference(mask)
				if maskElem and maskElem.tag == 'mask':
					maskElem.apply(surface, self)
				else:
					print(f'warning: invalid mask reference: {mask}')

			yield self
		finally:
			surface.context.restore()

	def __getitem__(self, key):
		return self._attribs[helpers.attribs.parseAttribute(key)]

	def __setitem__(self, key, value):
		attrib = helpers.attribs.parseAttribute(key)
		if (self.__class__.attribs and (not attrib or attrib[0] != '{') and
		    attrib not in self.__class__.attribs):
			print(f'warning: <{self.tag}> element doesn\'t take "{attrib}" attribute')

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

	def getAttribute(self, attrib, default=None, *, cascade=False):
		"""Get the value of an attribute, inheriting the value from the element's ancestors if cascade=True"""
		attrib = helpers.attribs.parseAttribute(attrib, namespaces=self.root.namespaces,
		                                        defaultName=self.namespace)
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
			if tag in self.ancestors():
				raise ValueError('can\'t add an element\'s ancestor to itself')
			if (self.__class__.content and (not tag.tag or tag.tag[0] != '{') and
			    attrib not in self.__class__.content):
				print(f'warning: <{self.tag}> element doesn\'t take "{tag.tag}" child element')
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

	def draw(self, surface, *, paint=True, viewport=None):
		# Default to drawing nothing
		return

	def boundingBox(self):
		# Default to no box
		return helpers.geometry.Box()


class _StructureElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + _attrib['GraphicalEvents']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['View'] + _content['Conditional'] + _content['Hyperlink'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']

	def draw(self, surface, *, paint=True, viewport=None):
		for child in self._children:
			child.draw(surface, paint=paint, viewport=viewport)

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

	def _paint(self, surface, *, viewport=None):
		vp = viewport or self._getViewport()
		opacity = helpers.attribs.getFloat(self, 'opacity', 1, range=[0, 1], cascade=True)
		fillOpacity = helpers.attribs.getFloat(self, 'fill-opacity', 1, range=[0, 1], cascade=True)
		strokeOpacity = helpers.attribs.getFloat(self, 'stroke-opacity', 1, range=[0, 1], cascade=True)

		fill = self.getAttribute('fill', '#000', cascade=True)
		fill = helpers.colors.color(fill, fillOpacity*opacity)
		fillRule = helpers.attribs.getEnum(self, 'fill-rule', 'nonzero',
		                                   helpers.attribs.FILL_RULES, cascade=True)

		stroke = self.getAttribute('stroke', 'none', cascade=True)
		stroke = helpers.colors.color(stroke, strokeOpacity*opacity)
		strokeWidth = self.getAttribute('stroke-width', 1, cascade=True)
		strokeWidth = helpers.coordinates.size2(strokeWidth, vp, 'xy')
		strokeLinecap = helpers.attribs.getEnum(self, 'stroke-linecap', 'butt',
		                                        helpers.attribs.LINE_CAPS, cascade=True)
		strokeLinejoin = helpers.attribs.getEnum(self, 'stroke-linejoin', 'miter',
		                                         helpers.attribs.LINE_JOINS, cascade=True)

		dashArray = self.getAttribute('stroke-dasharray', '', cascade=True)
		dashArray = helpers.attribs.normalize(dashArray).split()
		if dashArray:
			dashes = [helpers.coordinates.size2(dash, vp, 'xy') for dash in dashArray]
			if sum(dashes):
				offset = self.getAttribute('stroke-dashoffset', cascade=True)
				offset = helpers.coordinates.size2(offset, vp, 'xy')
				surface.context.set_dash(dashes, offset)

		surface.context.set_source_rgba(*fill)
		surface.context.set_fill_rule(fillRule)
		surface.context.fill_preserve()

		surface.context.set_source_rgba(*stroke)
		surface.context.set_line_width(strokeWidth)
		surface.context.set_line_cap(strokeLinecap)
		surface.context.set_line_join(strokeLinejoin)
		surface.context.stroke()
