from __future__ import annotations
from contextlib import contextmanager
import math
import re
import sys
import typing as ty

from . import _creators
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content
from ..helpers import types as ht

class _Element:
	tag = ''
	namespace = helpers.namespaces.NS_SVG
	attribs = None
	content = None
	_defaults = {}
	_strAttrib = {}

	def __init__(self, *, parent:ty.Optional[_ElemType] = None, childIndex:ty.Optional[int] = None,
	             namespaces:ty.Optional[ty.Dict[str,str]] = None, **attribs):
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
			self._root = ht.Root(self, namespaces=namespaces)

		# Allowed children
		if self.__class__.content:
			for tag in self.__class__.content:
				try:
					setattr(self, tag, _creators[tag].__get__(self, self.__class__))
				except KeyError:
					pass

		# Attributes
		self._attribs = {}
		for key in attribs:
			attrib = self._parseAttribute(key)
			if (self.__class__.attribs and (not attrib or attrib[0] != '{') and
			    attrib not in self.__class__.attribs):
				print(f'warning: <{self.tag}> element doesn\'t take "{attrib}" attribute')
			self._attribs[attrib] = attribs[key]

		if 'id' in attribs:
			self._setID(attribs['id'])

		self.transform = None
		if self.__class__.attribs and 'transform' in self.__class__.attribs:
			self._setTransform()

	def _getOutgoingRefs(self) -> ty.List[ty.Tuple[_ElemType, str]]:
		refs = []
		clipPath = self._parseReference(self._attribs.get('clip-path', None))
		if clipPath:
			refs.append((clipPath, 'clip-path'))
		mask = self._parseReference(self._attribs.get('mask', None))
		if mask:
			refs.append((mask, 'mask'))
		return refs

	def _getViewport(self) -> ty.Optional[ht.Viewport]:
		elem = self.parent
		while elem and not hasattr(elem, 'viewport'):
			elem = elem.parent
		return elem and elem.viewport

	def _setTransform(self):
		self.transform = ht.Transform(self._attribs.get('transform', None),
		                              parent=self)

	def _setID(self, value):
		if value in self._root._ids:
			print('warning: duplicate ID ignored: ' + value)
		else:
			self._root._ids[value] = self

	def _getAutoID(self, prefix:ty.Optional[str] = None, idList:ty.Optional[ty.List[str]] = None) -> str:
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

	def _setAutoID(self, prefix:ty.Optional[str] = None, idList:ty.Optional[ty.List[str]] = None):
		eid = self._getAutoID(prefix, idList)
		self._attribs['id'] = eid
		self._setID(eid)

	def _tagCode(self, *, close:bool = True, namespaceDeclaration:bool = True) -> str:
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
			elif isinstance(val, ht._Default):
				# don't print
				continue
			attr = self._root.namespaces.qualifyName(attr, defaultName=self.namespace)
			string += f' {attr}="{val}"'

		string += '/>' if close else '>'
		return string

	def _parseAttribute(self, attrib:str) -> str:
		return helpers.attribs.parseAttribute(attrib, namespaces=self._root.namespaces,	
		                                      defaultName=self.namespace)

	def _getattrib(self, attrib:str) -> ty.Any:
		# with getDefault, no attrib parsing
		return self._attribs.get(attrib, self._defaults[attrib])

	def _parseReference(self, value:ty.Union[str,_ElemType,None]) -> ty.Optional[_ElemType]:
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
	def _applyTransformations(self, surface:ht.Surface):
		surface.context.save()
		try:
			if self.transform and self.transform._transformed:
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

	def __getitem__(self, attrib:str) -> ty.Any:
		return self._attribs[self._parseAttribute(attrib)]

	def __setitem__(self, attrib:str, value:ty.Any):
		attrib = self._parseAttribute(attrib)
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
		elif attrib == 'transform' and self.transform:
			self.transform._reset()
			self.transform._transform(value)
		return attrib

	def __delitem__(self, attrib:str):
		attrib = self._parseAttribute(attrib)
		value = self._attribs.get(attrib, None)
		del self._attribs[attrib]

		if attrib == 'id':
			try:
				del self._root._ids[value]
			except KeyError:
				pass
		elif attrib == 'transform' and self.transform:
			self.transform._reset()
		return attrib

	def __repr__(self) -> str:
		return self._tagCode(close=len(self._children) == 0,
		                     namespaceDeclaration=False)

	@property
	def parent(self) -> ty.Optional[_ElemType]:
		return self._parent
	@parent.setter
	def parent(self, elem:ty.Optional[_ElemType]):
		if elem:
			elem.addChild(self)
		else:
			self.detach()

	@property
	def children(self) -> ty.Tuple[_ElemType, ...]:
		return tuple(self._children)

	@property
	def depth(self) -> int:
		return 0 if self.isRoot() else self.parent.depth + 1

	@property
	def id(self) -> ty.Optional[str]:
		return self._attribs.get('id', None)
	@id.setter
	def id(self, value:str):
		self['id'] = value
	@id.deleter
	def id(self):
		del self['id']

	@property
	def root(self) -> _ElemType:
		return self._root.element

	def isRoot(self) -> bool:
		return self.root is self

	def changeID(self, newID:ty.Optional[str] = None, updateRefs:bool = True, *, auto:bool = False):
		curID = self.id
		refs = []
		if updateRefs:
			refs = self.getReferences()

		if newID:
			if newID in self._root._ids:
				if auto:
					# add number to newID
					self._setAutoID(newID)
				else:
					raise ValueError(f'ID already exists in the tree: {newID}')
			self.id = newID
		else:
			if auto:
				self._setAutoID()
			else:
				# remove if not updateRefs or no references
				if len(refs) > 0:
					raise ValueError('Removing ID with updateRefs=True when the element has references')
				del self.id

		for refElem, refAttrib in refs:
			if refAttrib in refElem._strAttrib:
				refElem[refAttrib] = refElem._strAttrib[refAttrib](self)
			else:
				refElem[refAttrib] = self

	def delete(self, recursive:bool = True):
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
			self._root = ht.Root(self)
			self._root._updateIDs()
			for eid in self._root._ids:
				del parent._root._ids[eid]
			for e in self.descendants():
				e._root = self._root

	def getAttribute(self, attrib:str, default:ty.Any = None, *,
	                 cascade:bool = False, getDefault:bool = False) -> ty.Any:
		"""Get the value of an attribute, inheriting the value from the element's ancestors if cascade=True"""
		attrib = self._parseAttribute(attrib)
		if getDefault:
			default = self._defaults.get(attrib, default)
		if cascade:
			node = self
			while attrib not in node._attribs or node._attribs[attrib] == 'inherit':
				node = node.parent
				if node is None:
					# root reached
					return default
			return node._attribs[attrib] #value if value is not None else default
		else:
			return self._attribs.get(attrib, default)
	setAttribute = __setitem__
	removeAttribute = __delitem__

	def hasAttribute(self, attrib:str) -> bool:
		return self._parseAttribute(attrib) in self._attribs

	def getReferences(self) -> ty.List[ty.Tuple[_ElemType, str]]:
		refs = []
		for e in self._root.element.descendants():
			outRefs = e._getOutgoingRefs()
			for refTarget, refAttrib in outRefs:
				if refTarget is self:
					refs.append((e, refAttrib))
		return refs

	def addChild(self, tag:ty.Union[str,_ElemType], *attribs,
	             childIndex:ty.Optional[int] = None, **kwattribs):
		"""Add a child element to this element"""
		if isinstance(tag, _Element):
			if tag in self.ancestors():
				raise ValueError('can\'t add an element\'s ancestor to itself')
			if (self.__class__.content and (not tag.tag or tag.tag[0] != '{') and
			    tag.tag not in self.__class__.content):
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
			nsName, nsPrefix, tag = helpers.namespaces._split(tag)
			if nsPrefix:
				nsName = self._root.namespaces.fromPrefix(nsPrefix)
				if not nsName:
					# Undefined prefix; keep prefix in tag
					print(f'undefined namespace prefix "{nsPrefix}:"')
					tag = nsPrefix + ':' + tag
			elif not nsName:
				nsName = self._root.namespaces.default

			if nsName == helpers.namespaces.NS_SVG and tag in elements:
				return elements[tag](parent=self, childIndex=childIndex, *attribs, **kwattribs)
			else:
				# Custom element
				print(f'<{tag}> node not supported; can be saved but not drawn')
				elem = CustomElement(tag, nsName, parent=parent, *attribs, **kwAttribs)

	def code(self, file:ty.Optional[ty.TextIO] = None, *, indent:ty.Optional[str] = '',
	         indentDepth:int = 0, newline:ty.Optional[str] = '\n',
	         xmlDeclaration:bool = False, namespaceDeclaration:bool = True):
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

	def descendants(self, includeSelf:bool = True) -> ty.Generator[_ElemType, None, None]:
		if includeSelf:
			yield self
		for child in self._children:
			yield from child.descendants(True)

	def ancestors(self, includeSelf:bool = True) -> ty.Generator[_ElemType, None, None]:
		if includeSelf:
			yield self
		anc = self.parent
		while anc:
			yield anc
			anc = anc.parent

	def find(self, function:ty.Callable[[_ElemType],bool], *, maxResults:ty.Optional[int] = None) -> ty.List[_ElemType]:
		results = []
		for elem in self.descendants():
			if function(elem):
				results.append(elem)
				if maxResults and len(results) >= maxResults:
					break
		return results

	def findID(self, id:str) -> ty.Optional[_ElemType]:
		res = self._root._ids.get(id, None)
		if res and self in res.ancestors():
			return res
		return None

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		# Default to drawing nothing
		return

	def boundingBox(self) -> ht.Box:
		# Default to no box
		return ht.Box()

	def _transformBox(self, box:ht.Box) -> ht.Box:
		# Apply the element's transformations to its bounding box
		if box.defined:
			#if self.transform and self.transform._transformed:
			#	# transform
			clipPath = self._attribs.get('clip-path', None)
			if clipPath:
				cpElem = self._parseReference(clipPath)
				if cpElem and cpElem.tag == 'clipPath':
					box = cpElem._clipBox(box)
			#mask = self._attribs.get('mask', None)
			#if mask:
			#	maskElem = self._parseReference(mask)
			#	if maskElem and maskElem.tag == 'mask':
			#		# mask
		return box

# Version for type hints
_ElemType = ty.TypeVar('Element', bound=_Element)


class _StructureElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + _attrib['GraphicalEvents']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['View'] + _content['Conditional'] + _content['Hyperlink'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']

	def draw(self, surface:ht.Surface, *, paint:bool = True, viewport:ty.Optional[ht.Viewport] = None):
		for child in self._children:
			child.draw(surface, paint=paint, viewport=viewport)

	def boundingBox(self) -> ht.Box:
		# todo: account for transformations
		# https://svgwg.org/svg2-draft/coords.html#bounding-box
		box = ht.Box()
		for child in self._children:
			box += child.boundingBox()
		return self._transformBox(box)


class _ShapeElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['GraphicalEvents'] + _attrib['Paint'] + _attrib['Opacity'] + _attrib['Graphics'] + _attrib['Cursor'] + _attrib['Filter'] + _attrib['Mask'] + _attrib['Clip']
	content = _content['Description'] + _content['Animation']
	_defaults = {**_Element._defaults,
		'opacity': 1,
		'fill-opacity': 1,
		'stroke-opacity': 1,
		'fill': 'black',
		'fill-rule': 'nonzero',
		'stroke': 'none',
		'stroke-width': 1,
		'stroke-linecap': 'butt',
		'stroke-linejoin': 'miter',
		'stroke-dasharray': '',
		'stroke-dashoffset': 0,
	}

	def _paint(self, surface:ht.Surface, *,
	           viewport:ty.Optional[ht.Viewport] = None):
		vp = viewport or self._getViewport()
		opacity = helpers.attribs.getFloat(
			self, 'opacity', range=[0, 1], cascade=True)
		fillOpacity = helpers.attribs.getFloat(
			self, 'fill-opacity', range=[0, 1], cascade=True)
		strokeOpacity = helpers.attribs.getFloat(
			self, 'stroke-opacity', range=[0, 1], cascade=True)

		fill = self.getAttribute(
			'fill', self._defaults['fill'], cascade=True)
		fill = helpers.colors.color(fill, fillOpacity*opacity)
		fillRule = helpers.attribs.getEnum(
			self, 'fill-rule', helpers.attribs.FILL_RULES, cascade=True)

		stroke = self.getAttribute(
			'stroke', self._defaults['stroke'], cascade=True)
		stroke = helpers.colors.color(stroke, strokeOpacity*opacity)
		strokeWidth = self.getAttribute(
			'stroke-width', self._defaults['stroke-width'], cascade=True)
		strokeWidth = helpers.coordinates.size(strokeWidth, vp, 'xy')
		strokeLinecap = helpers.attribs.getEnum(
			self, 'stroke-linecap', helpers.attribs.LINE_CAPS, cascade=True)
		strokeLinejoin = helpers.attribs.getEnum(
			self, 'stroke-linejoin', helpers.attribs.LINE_JOINS, cascade=True)

		dashArray = self.getAttribute('stroke-dasharray', '', cascade=True)
		dashArray = helpers.attribs.normalize(dashArray).split()
		if dashArray:
			dashes = [helpers.coordinates.size(dash, vp, 'xy')
			          for dash in dashArray]
			if sum(dashes):
				offset = self.getAttribute('stroke-dashoffset', cascade=True)
				offset = helpers.coordinates.size(offset, vp, 'xy')
				surface.context.set_dash(dashes, offset)

		surface.context.set_source_rgba(*fill)
		surface.context.set_fill_rule(fillRule)
		surface.context.fill_preserve()

		surface.context.set_source_rgba(*stroke)
		surface.context.set_line_width(strokeWidth)
		surface.context.set_line_cap(strokeLinecap)
		surface.context.set_line_join(strokeLinejoin)
		surface.context.stroke()


class CustomElement(_Element):
	"""A placeholder or custom element with any tag name."""

	def __init__(self, tag:str, namespace:str = helpers.namespaces.NS_SVG, **attribs):
		self.tag = tag
		self.namespace = namespace
		super().__init__(**attribs)
