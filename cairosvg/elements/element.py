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
	_attrib_to_str = {}

	def __init__(self, *, parent:ty.Optional[_ElemType] = None,
	             child_index:ty.Optional[int] = None,
	             namespaces:ty.Optional[ty.Dict[str,str]] = None, **attribs):
		# Tree structure
		self._parent = parent
		self._children = []
		if parent is not None:
			# child
			if (parent.__class__.content and (not self.tag or self.tag[0] != '{') and
			    self.tag not in parent.__class__.content):
				print(f'warning: <{parent.tag}> element doesn\'t take "{self.tag}" child element')
			if child_index is not None:
				self.parent._children.insert(child_index, self)
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
			attrib = self._parse_attribute(key)
			if (self.__class__.attribs and (not attrib or attrib[0] != '{') and
			    attrib not in self.__class__.attribs):
				print(f'warning: <{self.tag}> element doesn\'t take "{attrib}" attribute')
			self._attribs[attrib] = attribs[key]

		if 'id' in attribs:
			self._set_id(attribs['id'])

		self.transform = None
		if self.__class__.attribs and 'transform' in self.__class__.attribs:
			self._set_transform()

	def _get_outgoing_refs(self) -> ty.List[ty.Tuple[_ElemType, str]]:
		refs = []
		clip_path = self._parse_reference(self._attribs.get('clip-path', None))
		if clip_path:
			refs.append((clip_path, 'clip-path'))
		mask = self._parse_reference(self._attribs.get('mask', None))
		if mask:
			refs.append((mask, 'mask'))
		return refs

	def _get_viewport(self) -> ty.Optional[ht.Viewport]:
		elem = self.parent
		while elem and not hasattr(elem, 'viewport'):
			elem = elem.parent
		return elem and elem.viewport

	def _set_transform(self):
		self.transform = ht.Transform(self._attribs.get('transform', None),
		                              parent=self)

	def _set_id(self, value):
		if value in self._root._ids:
			print('warning: duplicate ID ignored: ' + value)
		else:
			self._root._ids[value] = self

	def _get_auto_id(self, prefix:ty.Optional[str] = None,
	                 id_list:ty.Optional[ty.List[str]] = None) -> str:
		# Find the first free ID of the form prefix+number
		prefix = prefix or self.tag
		if prefix[-1].isnumeric():
			# Add a separator if the prefix ends with a number
			prefix += '_'
		if id_list is None:
			id_list = self._root._ids.keys()

		i = 1
		eid = prefix + str(i)
		while eid in id_list:
			i += 1
			eid = prefix + str(i)
		return eid

	def _set_auto_id(self, prefix:ty.Optional[str] = None,
	                 id_list:ty.Optional[ty.List[str]] = None):
		eid = self._get_auto_id(prefix, id_list)
		self._attribs['id'] = eid
		self._set_id(eid)

	def _tag_code(self, *, close:bool = True,
	              namespace_declaration:bool = True) -> str:
		nss = self._root.namespaces
		ns_prefix = nss._get_prefix(self.namespace)
		if ns_prefix: ns_prefix += ':'
		string = '<' + ns_prefix + self.tag

		if namespace_declaration and self.is_root():
			ns_names = helpers.namespaces.get_namespaces(self)
			ns = [(nss._get_prefix(name), name) for name in ns_names]
			ns.sort()
			for ns_prefix, ns_name in ns:
				if ns_prefix == 'xml' and ns_name == helpers.namespaces.NS_XML:
					# xml: doesn't need to be declared
					continue
				key = 'xmlns:' + ns_prefix if ns_prefix else 'xmlns'
				string += f' {key}="{ns_name}"'

		for attr in self._attribs:
			val = self._attribs[attr]
			if attr in self.__class__._attrib_to_str:
				val = self.__class__._attrib_to_str[attr](val)
				if val is None:
					# don't print
					continue
			elif val is None:
				val = 'none'
			elif isinstance(val, ht._Default):
				# don't print
				continue
			attr = self._root.namespaces.qualify_name(
				attr, default_name=self.namespace)
			string += f' {attr}="{val}"'

		string += '/>' if close else '>'
		return string

	def _parse_attribute(self, attrib:str) -> str:
		return helpers.attribs.parse_attribute(
			attrib, namespaces=self._root.namespaces,
			default_name=self.namespace)

	def _getattrib(self, attrib:str) -> ty.Any:
		# with get_default, no attrib parsing
		return self._attribs.get(attrib, self._defaults[attrib])

	def _parse_reference(self, value:ty.Union[str,_ElemType,None]
	                     ) -> ty.Optional[_ElemType]:
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
	def _apply_transformations(self, surface:ht.Surface):
		transformed = self.transform and self.transform._transformed
		clip_path = self._attribs.get('clip-path', None)
		mask = self._attribs.get('mask', None)

		if transformed or clip_path or mask:
			surface.context.save()
			try:
				if transformed:
					self.transform.apply(surface)

				if clip_path:
					cp_elem = self._parse_reference(clip_path)
					if cp_elem and cp_elem.tag == 'clipPath':
						cp_elem.apply(surface, self)
					else:
						print(f'warning: invalid clip-path reference: {clip_path}')

				if mask:
					mask_elem = self._parse_reference(mask)
					if mask_elem and mask_elem.tag == 'mask':
						mask_elem.apply(surface, self)
					else:
						print(f'warning: invalid mask reference: {mask}')

				yield self
			finally:
				surface.context.restore()
		else:
			yield self

	def __getitem__(self, attrib:str) -> ty.Any:
		return self._attribs[self._parse_attribute(attrib)]

	def __setitem__(self, attrib:str, value:ty.Any):
		attrib = self._parse_attribute(attrib)
		if (self.__class__.attribs and (not attrib or attrib[0] != '{') and
		    attrib not in self.__class__.attribs):
			print(f'warning: <{self.tag}> element doesn\'t take "{attrib}" attribute')

		old_value = self._attribs.get(attrib, None)
		self._attribs[attrib] = value
		if attrib == 'id':
			try:
				del self._root._ids[old_value]
			except KeyError:
				pass
			self._set_id(value)
		elif attrib == 'transform' and self.transform:
			self.transform._reset()
			self.transform._transform(value)
		return attrib

	def __delitem__(self, attrib:str):
		attrib = self._parse_attribute(attrib)
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
		return self._tag_code(close=len(self._children) == 0,
		                     namespace_declaration=False)

	@property
	def parent(self) -> ty.Optional[_ElemType]:
		return self._parent
	@parent.setter
	def parent(self, elem:ty.Optional[_ElemType]):
		if elem:
			elem.add_child(self)
		else:
			self.detach()

	@property
	def children(self) -> ty.Tuple[_ElemType, ...]:
		return tuple(self._children)

	@property
	def depth(self) -> int:
		return 0 if self.is_root() else self.parent.depth + 1

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

	def is_root(self) -> bool:
		"""Check whether this element is the root of an element tree."""
		return self.root is self

	def change_id(self, new_id:ty.Optional[str] = None,
	              update_references:bool = True, *, auto:bool = False):
		"""Change an element's ID attribute.
		If `update_references` is True, change references to this element
		(e.g., <use> elements) to point to the new ID.
		* If `new_id` is a non-empty string and `auto` is False, set the
		    element's ID to `new_id`, raising a `ValueError` if the ID already
		    exists in the tree.
		* If `new_id` is a non-empty string and `auto` is True, set the
		    element's ID to `new_id`, appending a number if the ID already
		    exists in the tree.
		* If `new_id` is None and `auto` is False, remove the ID. This will
		    raise a `ValueError` if `update_references` is True and the element
		    has references.
		* If `new_id` is None and `auto` is True, assign an automatic ID based
		    on the element's tag name and a number.
		"""
		refs = []
		if update_references:
			refs = self.get_references()

		if new_id:
			if new_id in self._root._ids:
				if auto:
					# add number to new_id
					self._set_auto_id(new_id)
				else:
					raise ValueError(f'ID already exists in the tree: {new_id}')
			self.id = new_id
		else:
			if auto:
				self._set_auto_id()
			else:
				# remove if not update_references or no references
				if len(refs) > 0:
					raise ValueError('Removing ID with update_references=True when the element has references')
				del self.id

		for ref_elem, ref_attrib in refs:
			if ref_attrib in ref_elem._attrib_to_str:
				ref_elem[ref_attrib] = ref_elem._attrib_to_str[ref_attrib](self)
			else:
				ref_elem[ref_attrib] = self

	def delete(self, recursive:bool = True):
		"""Delete this element from the tree.
		Remove the element from its parent and children, without creating a
		new element tree. Further method calls on the element may fail.
		If `recursive` is True, the method will be called recursively on the
		element's descendants. Otherwise, its direct children will be detached
		into their own element trees.
		"""
		if self.parent:
			self.parent._children.remove(self)
			if self.id:
				del self._root._ids[self.id]

		if recursive:
			while len(self._children) > 0:
				self._children[-1].delete(True)
		else:
			while len(self._children) > 0:
				self._children[-1].detach()
			self._root._update_ids()

		self._parent = None
		self._root = None

	def detach(self):
		"""Disconnect this element from the tree.
		Remove the element from its parent, and make it the root of a new
		element tree including its descendants.
		"""
		parent = self.parent
		if parent:
			self._parent = None
			parent._children.remove(self)
			self._root = ht.Root(self)
			self._root._update_ids()
			for eid in self._root._ids:
				del parent._root._ids[eid]
			for e in self.descendants(False):
				e._root = self._root

	def get_attribute(self, attrib:str, default:ty.Any = None, *,
	                  cascade:bool = False, get_default:bool = False) -> ty.Any:
		"""Retrieve an attribute value.
		This method parses the attribute name, and returns the first value
		it finds after checking, in the following order:
		* The element's own attribute values;
		* if `cascade` is True, the attribute values of its ancestors,
		* if `get_default` is True, the element-specific default attribute values;
		* or the value of the `default` argument.
		"""
		attrib = self._parse_attribute(attrib)
		if get_default:
			default = self._defaults.get(attrib, default)
		if cascade:
			node = self
			while attrib not in node._attribs or node._attribs[attrib] == 'inherit':
				node = node.parent
				if node is None:
					# root reached
					return default
			return node._attribs[attrib]
		else:
			return self._attribs.get(attrib, default)
	set_attribute = __setitem__
	remove_attribute = __delitem__

	def has_attribute(self, attrib:str) -> bool:
		"""Check whether an element has an attribute set.
		This method parses the attribute name, and doesn't consider inheritance.
		"""
		return self._parse_attribute(attrib) in self._attribs

	def get_references(self) -> ty.List[ty.Tuple[_ElemType, str]]:
		"""List the references to this element.
		Return a list of elements in the tree that refer to this element
		through attributes such as "xlink:href" or "clip-path". Each item
		in the list is a tuple of the source element, and the name of the
		source element's attribute that contains the reference.
		"""
		refs = []
		for e in self._root.element.descendants(True):
			out_refs = e._get_outgoing_refs()
			for ref_target, ref_attrib in out_refs:
				if ref_target is self:
					refs.append((e, ref_attrib))
		return refs

	def add_child(self, tag:ty.Union[str,_ElemType], *attribs,
	              child_index:ty.Optional[int] = None, **kwattribs):
		"""Add a child element to this element.
		* If `tag` is a string, it specifies the tag name for a new element.
		    `attribs` and `kwattribs` are passed on to this element's
		    constructor. For example: `e.add_child('circle', r=10)`.
		* If `tag` is another element, it will be detached from its current
		    position in its tree and re-added as a child of this element. A
		    `ValueError` is raised if this would create a cycle in the tree
		    (e.g., `e.add_child(e.parent)`). `attribs` and `kwattribs` are ignored.
		`child_index` specifies the new element's position in the element's list of
		children. If `None`, the new element is appended to the end.
		"""
		if isinstance(tag, _Element):
			if tag in self.ancestors(True):
				raise ValueError('can\'t add an element\'s ancestor to itself')
			if (self.__class__.content and (not tag.tag or tag.tag[0] != '{') and
			    tag.tag not in self.__class__.content):
				print(f'warning: <{self.tag}> element doesn\'t take "{tag.tag}" child element')
			if tag.parent:
				tag.detach()
			if child_index is not None:
				self._children.insert(child_index, tag)
			else:
				self._children.append(tag)
			tag._parent = self

			id_conflicts = tag._root._ids.keys() & self._root._ids.keys()
			if id_conflicts:
				print('warning: duplicate ids changed: ' + ', '.join(id_conflicts))
				id_list = tag._root._ids.keys() | self._root._ids.keys()
				for eid in id_conflicts:
					elem = tag._root._ids[eid]
					new_id = elem._get_auto_id(eid, id_list)
					elem.change_id(new_id)
			self._root._ids.update(tag._root._ids)
			for e in tag.descendants(True):
				e._root = self._root

		else:
			from . import elements
			ns_name, ns_prefix, tag = helpers.namespaces._split(tag)
			if ns_prefix:
				ns_name = self._root.namespaces.from_prefix(ns_prefix)
				if not ns_name:
					# Undefined prefix; keep prefix in tag
					print(f'undefined namespace prefix "{ns_prefix}:"')
					tag = ns_prefix + ':' + tag
			elif not ns_name:
				ns_name = self._root.namespaces.default

			if ns_name == helpers.namespaces.NS_SVG and tag in elements:
				return elements[tag](parent=self, child_index=child_index,
				                     *attribs, **kwattribs)
			else:
				# Custom element
				print(f'<{tag}> node not supported; can be saved but not drawn')
				elem = CustomElement(tag, ns_name, parent=parent,
				                     *attribs, **kwattribs)

	def write_code(self, file:ty.Optional[ty.TextIO] = None, *,
	               indent:ty.Optional[str] = '', indent_depth:int = 0,
	               newline:ty.Optional[str] = '\n', xml_declaration:bool = False,
	               namespace_declaration:bool = True):
		"""Write the SVG code for this element's subtree to `file`.
		`file` is a file-like object with a `write` method. If None,
		print to stdout (the screen).
		If `xml_declaration` is True, include the declaration of the XML
		version and encoding at the start.
		If `namespace_declaration` is True and `self` is the root element,
		include `xmlns:` attributes for namespaces used in the tree.
		Pretty-print options:
		* `indent`: whitespace string used for indentation
		* `indent_depth`: starting indentation level
		* `newline`: whitespace string used between tags
		"""
		indent = indent or ''
		newline = newline or ''
		indentation = indent_depth*indent

		if not file:
			file = sys.stdout

		if xml_declaration:
			decl = '<?xml version="1.0" encoding="UTF-8"?>'
			file.write(f'{indentation}{decl}{newline}')

		tag_code = self._tag_code(close=len(self.children)==0,
		                          namespace_declaration=namespace_declaration)
		file.write(f'{indentation}{tag_code}{newline}')
		if len(self._children) > 0:
			for child in self._children:
				child.write_code(file, indent=indent,
				                 indent_depth=indent_depth + 1, newline=newline)
			tag_close = f'</{self.tag}>'
			file.write(f'{indentation}{tag_close}{newline}')

	def descendants(self, include_self:bool = True
	                ) -> ty.Generator[_ElemType, None, None]:
		"""A generator of the element's descendants.
		Traverses the element's subtree (children, grandchildren etc.), and
		yields elements depth-first. If `include_self` is True, start with the
		element itself.
		"""
		if include_self:
			yield self
		for child in self._children:
			yield from child.descendants(True)

	def ancestors(self, include_self:bool = True
	              ) -> ty.Generator[_ElemType, None, None]:
		"""A generator of the element's ancestors.
		Yields the element's parent, grandparent, etc., up to the root
		element. If `include_self` is True, start with the element itself.
		"""
		if include_self:
			yield self
		anc = self.parent
		while anc:
			yield anc
			anc = anc.parent

	def find(self, function:ty.Callable[[_ElemType],bool], *,
	         max_results:ty.Optional[int] = None) -> ty.List[_ElemType]:
		"""List descendant elements satisfying the given function.
		`function` is a callable that receives an element object, and should
		return a boolean. The function is evaluated on the element's descendants
		(depth-first), and a list is returned of those for which it returns True.
		If `max_results` is a positive number, return at most that many results.

		For example, to get all path elements among an element's descendants:
		`e.find(lambda x: x.tag == 'path')`
		"""
		results = []
		for elem in self.descendants(True):
			if function(elem):
				results.append(elem)
				if max_results and len(results) >= max_results:
					break
		return results

	def find_id(self, id:str) -> ty.Optional[_ElemType]:
		"""Find a descendant element with a specific ID.
		Returns None if no element was found, or if the element isn't a
		descendant of this element.
		"""
		res = self._root._ids.get(id, None)
		if res and self in res.ancestors(True):
			return res
		return None

	def draw(self, surface:ht.Surface, *, paint:bool = True,
	         viewport:ty.Optional[ht.Viewport] = None):
		"""Draw the element on a Cairo surface.
		`surface` is a surface object from the cairocffi library: `ImageSurface`,
		`PDFSurface`, `PSSurface`, `RecordingSurface` or `SVGSurface`.
		If `paint` is False, add the element's contents to the current path
		without applying fills or strokes.
		`viewport` is a `Viewport` object. Normally not necessary to specify if
		the root element has a viewport (such as an <svg> element).
		"""
		# Default to drawing nothing
		return

	def bounding_box(self, *, with_transform:bool = True) -> ht.Box:
		"""Calculate the element's bounding box.
		Returns a `Box` element representing the minimum bounding rectangle.
		If `with_transform` is True, apply the element's transform and clip-path
		attributes to the box.
		"""
		# Default to no box
		return ht.Box()

	def _transform_box(self, box:ht.Box) -> ht.Box:
		# Apply the element's transformations to its bounding box
		if box.defined:
			#if self.transform and self.transform._transformed:
			#	# transform
			clip_path = self._attribs.get('clip-path', None)
			if clip_path:
				cp_elem = self._parse_reference(clip_path)
				if cp_elem and cp_elem.tag == 'clipPath':
					box = cp_elem._clip_box(box)
			#mask = self._attribs.get('mask', None)
			#if mask:
			#	mask_elem = self._parse_reference(mask)
			#	if mask_elem and mask_elem.tag == 'mask':
			#		# mask
		return box

# Version for type hints
_ElemType = ty.TypeVar('Element', bound=_Element)


class _StructureElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + _attrib['GraphicalEvents']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['View'] + _content['Conditional'] + _content['Hyperlink'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']

	def draw(self, surface:ht.Surface, *, paint:bool = True,
	         viewport:ty.Optional[ht.Viewport] = None):
		for child in self._children:
			child.draw(surface, paint=paint, viewport=viewport)

	def bounding_box(self, *, with_transform:bool = True) -> ht.Box:
		# todo: account for transformations
		# https://svgwg.org/svg2-draft/coords.html#bounding-box
		box = ht.Box()
		for child in self._children:
			box += child.bounding_box()
		if with_transform: box = self._transform_box(box)
		return box


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
		vp = viewport or self._get_viewport()
		opacity = helpers.attribs.get_float(
			self, 'opacity', range=[0, 1], cascade=True)
		fill_opacity = helpers.attribs.get_float(
			self, 'fill-opacity', range=[0, 1], cascade=True)
		stroke_opacity = helpers.attribs.get_float(
			self, 'stroke-opacity', range=[0, 1], cascade=True)

		fill = self.get_attribute(
			'fill', self._defaults['fill'], cascade=True)
		fill = helpers.colors.color(fill, fill_opacity*opacity)
		fill_rule = helpers.attribs.get_enum(
			self, 'fill-rule', helpers.attribs.FILL_RULES, cascade=True)

		stroke = self.get_attribute(
			'stroke', self._defaults['stroke'], cascade=True)
		stroke = helpers.colors.color(stroke, stroke_opacity*opacity)
		stroke_width = self.get_attribute(
			'stroke-width', self._defaults['stroke-width'], cascade=True)
		stroke_width = helpers.coordinates.size(stroke_width, vp, 'xy')
		stroke_linecap = helpers.attribs.get_enum(
			self, 'stroke-linecap', helpers.attribs.LINE_CAPS, cascade=True)
		stroke_linejoin = helpers.attribs.get_enum(
			self, 'stroke-linejoin', helpers.attribs.LINE_JOINS, cascade=True)

		stroke_dasharray = self.get_attribute(
			'stroke-dasharray', '', cascade=True)
		stroke_dasharray = helpers.attribs.normalize(stroke_dasharray).split()
		if stroke_dasharray:
			dashes = [helpers.coordinates.size(dash, vp, 'xy')
			          for dash in stroke_dasharray]
			if sum(dashes):
				stroke_dashoffset = self.get_attribute(
					'stroke-dashoffset', cascade=True)
				stroke_dashoffset = helpers.coordinates.size(
					stroke_dashoffset, vp, 'xy')
				surface.context.set_dash(dashes, stroke_dashoffset)

		surface.context.set_source_rgba(*fill)
		surface.context.set_fill_rule(fill_rule)
		surface.context.fill_preserve()

		surface.context.set_source_rgba(*stroke)
		surface.context.set_line_width(stroke_width)
		surface.context.set_line_cap(stroke_linecap)
		surface.context.set_line_join(stroke_linejoin)
		surface.context.stroke()


class CustomElement(_Element):
	"""A placeholder or custom element with any tag name."""

	def __init__(self, tag:str, namespace:str = helpers.namespaces.NS_SVG,
	             **attribs):
		self.tag = tag
		self.namespace = namespace
		super().__init__(**attribs)
