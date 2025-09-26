from __future__ import annotations
from contextlib import contextmanager
import re
import sys
import typing as ty

from . import node, _creators
from .. import helpers
from ..helpers.modules import attrib as _attrib, content as _content
from ..helpers import attribs as att, options as opt, types as ht

class _Element(node._Node):
	"""Base class for elements.
	Should not be instantiated directly.
	"""
	is_element = True
	tag = ''
	namespace = helpers.namespaces.NS_SVG
	attribs = None
	content = None
	_open_tag = False
	_defaults = {}
	_attrib_to_str = {
		'clip-path': lambda val: (f'url({val})' if val and val[0] == '#'
		                          else val) if isinstance(val, str) else \
		                          f'url(#{val.id})' if isinstance(val, _Element) \
		                          else 'none',
		'mask': lambda val: (f'url({val})' if val and val[0] == '#'
		                     else val) if isinstance(val, str) else \
		                     f'url(#{val.id})' if isinstance(val, _Element) \
		                     else 'none'
	}

	def __init__(self, *, parent:ty.Optional[node._Node] = None,
	             child_index:ty.Optional[int] = None,
	             namespaces:ty.Optional[ty.Dict[str,str]] = None, **attribs):
		# Tree structure
		super().__init__(parent=parent, child_index=child_index,
		                 namespaces=namespaces)

		# Methods for creating children
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
				print(f'warning: {self._node_str()} element doesn\'t take "{attrib}" attribute')
			self._attribs[attrib] = attribs[key]

		if 'id' in attribs:
			self._set_id(attribs['id'])

		self.transform = None
		if self.__class__.attribs and 'transform' in self.__class__.attribs:
			self._set_transform()

	def _can_have_child(self, child:node._Node) -> bool:
		if (child.__class__.is_element and self.__class__.content and
		    #(not child.tag or child.tag[0] != '{') and
		    child.namespace == helpers.namespaces.NS_SVG and
		    child.tag not in self.__class__.content):
			print(f'warning: {self._node_str()} element doesn\'t take {child._node_str()} child node')
		return True

	def _get_outgoing_refs(self) -> ty.List[ty.Tuple[_Element, str]]:
		refs = []
		for attrib in att.url_attribs:
			ref = self._parse_reference(self._attribs.get(attrib, None))
			if ref:
				refs.append((ref, attrib))
		return refs

	def _get_viewport(self) -> ty.Optional[ht.Viewport]:
		elem = self.parent
		while elem and not hasattr(elem, 'viewport'):
			elem = elem.parent
		return elem and elem.viewport

	def _set_transform(self):
		self.transform = ht.Transform(self._attribs.get('transform', None))
		self.transform._parent = self

	def _get_auto_id(self, prefix:ty.Optional[str] = None,
	                 id_list:ty.Optional[ty.List[str]] = None) -> str:
		return super()._get_auto_id(prefix or self.tag, id_list)

	def _set_auto_id(self, prefix:ty.Optional[str] = None,
	                 id_list:ty.Optional[ty.List[str]] = None) -> str:
		eid = self._get_auto_id(prefix, id_list)
		self._attribs['id'] = eid
		self._set_id(eid)
		return eid

	def _parse_attribute(self, attrib:str) -> str:
		return helpers.attribs.parse_attribute(
			attrib, namespaces=self._root.namespaces,
			default_name=self.namespace)

	def _getattrib(self, attrib:str) -> ty.Any:
		# with get_default, no attrib parsing
		return self._attribs.get(attrib, self.__class__._defaults[attrib])

	def _parse_reference(self, value:ty.Union[str,_Element,None]
	                     ) -> ty.Optional[_Element]:
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
			print(f'warning: {self._node_str()} element doesn\'t take "{attrib}" attribute')

		old_value = self._attribs.get(attrib, None)
		self._attribs[attrib] = value
		if attrib == 'id':
			try:
				del self._root._ids[old_value]
			except KeyError:
				pass
			if value:
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
		return self.code(close=len(self._children) == 0,
		                 options=opt._repr_format)

	def _node_str(self) -> str:
		return '<' + self._qualify_tag_name() + '>'

	@property
	def id(self) -> ty.Optional[str]:
		"""Get, set or delete the element's ID attribute.
		Getting the ID returns None if the element doesn't have an ID set.
		Use `change_id()` for more options, including updating references.
		"""
		return self._attribs.get('id', None)
	@id.setter
	def id(self, value:str):
		self['id'] = value
	@id.deleter
	def id(self):
		del self['id']

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
		* If `new_id` is None or empty and `auto` is False, remove the ID. This
		    will raise a `ValueError` if `update_references` is True and the
		    element has references.
		* If `new_id` is None or empty and `auto` is True, assign an automatic
		    ID based on the element's tag name and a number.
		"""
		refs = []
		if update_references:
			# Skip refs with the actual element as the attribute value
			refs = [(el,attr) for el,attr in self.get_references()
			        if isinstance(el[attr], str)]

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
			if ref_attrib in ref_elem.__class__._attrib_to_str:
				ref_elem[ref_attrib] = ref_elem.__class__._attrib_to_str[ref_attrib](self)
			else:
				ref_elem[ref_attrib] = self

	def get_attribute(self, attrib:str, default:ty.Any = None, *,
	                  cascade:bool = False, get_default:bool = False) -> ty.Any:
		"""Retrieve an attribute value.
		This method parses the attribute name, and returns the first value
		it finds after checking, in the following order:
		* The element's own attribute values;
		* if `cascade` is True, the attribute values of its ancestors;
		* if `get_default` is True, the element-specific default attribute values;
		* or the value of the `default` argument.
		"""
		attrib = self._parse_attribute(attrib)
		if get_default:
			default = self.__class__._defaults.get(attrib, default)
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

	def get_references(self) -> ty.List[ty.Tuple[_Element, str]]:
		"""List the references to this element.
		Return a list of elements in the tree that refer to this element
		through attributes such as "xlink:href" or "clip-path". Each item
		in the list is a tuple of the source element, and the name of the
		source element's attribute that contains the reference.
		"""
		refs = []
		for e in self._root.element.descendants(True, elements_only=True):
			out_refs = e._get_outgoing_refs()
			for ref_target, ref_attrib in out_refs:
				if ref_target is self:
					refs.append((e, ref_attrib))
		return refs

	def add_child(self, tag:ty.Union[str,node._Node], *attribs,
	              child_index:ty.Optional[int] = None, **kwattribs) -> node._Node:
		"""Add a child element to this element, and return it.
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
		if isinstance(tag, node._Node):
			super().add_child(tag, child_index)
			return tag

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
				print(f'<{tag}> element not supported; can be saved but not drawn')
				return CustomElement(tag, ns_name, parent=self,
				                     *attribs, **kwattribs)

	def _qualify_tag_name(self) -> str:
		ns_prefix = self._root.namespaces._get_prefix(self.namespace)
		if ns_prefix: ns_prefix += ':'
		return ns_prefix + self.tag

	def code(self, *, close:bool = True,
	         options:ty.Optional[opt.SVGOutputOptions] = None) -> str:
		"""Generate the SVG code for this element.
		Return an XML tag for this element with its attributes.
		If `close` is True, make a self-closing tag (e.g. <path/>);
		else, make an open tag (<path>).
		`options` is an optional `SVGOutputOptions` object.
		"""
		options = options or opt.SVGOutputOptions()
		out = ['<' + self._qualify_tag_name()]

		if options.namespace_declaration and self.is_root():
			ns_names = helpers.namespaces.get_namespaces(self)
			ns = [(self._root.namespaces._get_prefix(name), name)
			      for name in ns_names]
			ns.sort()
			for ns_prefix, ns_name in ns:
				if ns_prefix == 'xml' and ns_name == helpers.namespaces.NS_XML:
					# xml: doesn't need to be declared
					continue
				key = 'xmlns:' + ns_prefix if ns_prefix else 'xmlns'
				out.append(f' {key}="{ns_name}"')

		for attr in self._attribs:
			val = self._attribs[attr]
			if attr in self.__class__._attrib_to_str:
				val = self.__class__._attrib_to_str[attr](val)
				if val is None:
					# don't print
					continue

			if val is None:
				val = 'none'
			elif options.precision is not None:
				if isinstance(val, str):
					val = options._roundString(val)
				elif isinstance(val, int) or isinstance(val, float):
					val = options._roundNumber(val)

			attr = self._root.namespaces.qualify_name(
				attr, default_name=self.namespace)
			out.append(f' {attr}="{val}"')

		out.append('/>' if close else '>')
		return ''.join(out)

	def write_code(self, file:ty.Optional[ty.TextIO] = None,
	               options:ty.Optional[opt.SVGOutputOptions] = None):
		"""Write the SVG code for this element's subtree to `file`.
		`file` is a file-like object with a `write` method. If None,
		print to stdout (the screen).
		`options` is an optional `SVGOutputOptions` object.
		"""
		file = file or sys.stdout
		options = options or opt.SVGOutputOptions()
		if options.xml_declaration:
			decl = '<?xml version="1.0" encoding="UTF-8"?>'
			file.write(f'{decl}{options.newline}')

		# Create IDs for referenced elements without them
		for e in self._root.element.descendants(True, elements_only=True):
			out_refs = e._get_outgoing_refs()
			for ref_target, ref_attrib in out_refs:
				if not ref_target.id and ref_target in self.descendants():
					ref_target._set_auto_id()

		self._write_code(file, options, indent_depth=0)

	def _write_code(self, file:ty.TextIO, options:opt.SVGOutputOptions, *,
	                indent_depth:int = 0):
		indentation = indent_depth * options.indent

		is_closed = len(self._children) == 0 and not self.__class__._open_tag
		tag_code = self.code(close=is_closed, options=options)
		file.write(f'{indentation}{tag_code}')
		if is_closed or len(self._children) > 0:
			file.write(options.newline)
		if not is_closed:
			# Write children & closing tag
			for child in self._children:
				child._write_code(file, options, indent_depth=indent_depth + 1)
			qualified_tag = self._qualify_tag_name()
			file.write(f'{indentation}</{qualified_tag}>{options.newline}')

	def find(self, function:ty.Callable[[node._Node],bool], *,
	         elements_only:bool = True, max_results:ty.Optional[int] = None
	         ) -> ty.List[node._Node]:
		"""List descendant elements satisfying the given function.
		`function` is a callable that receives an element object, and should
		return a boolean. The function is evaluated on the element's descendants
		(depth-first), and a list is returned of those for which it returns True.
		If `elements_only` is False, also evaluate text nodes and comments.
		If `max_results` is a positive number, return at most that many results.

		For example, to get all path elements among an element's descendants:
		`e.find(lambda x: x.tag == 'path')`
		"""
		results = []
		for elem in self.descendants(True, elements_only=elements_only):
			if function(elem):
				results.append(elem)
				if max_results and len(results) >= max_results:
					break
		return results

	def find_id(self, id:str) -> ty.Optional[_Element]:
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
		Returns a `Box` object representing the minimum bounding rectangle.
		If `with_transform` is True, apply the element's transform and clip-path
		attributes to the box.
		"""
		# Default to no box
		return ht.Box()

	def _transform_box(self, box:ht.Box) -> ht.Box:
		# Apply the element's transformations to its bounding box
		if box.defined:
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
			if self.transform and self.transform._transformed:
				box = self.transform._transform_box(box)
		return box


class _StructureElement(_Element):
	attribs = _attrib['Core'] + _attrib['Conditional'] + _attrib['Style'] + _attrib['External'] + _attrib['Presentation'] + _attrib['GraphicalEvents']
	content = _content['Description'] + _content['Animation'] + _content['Structure'] + _content['Shape'] + _content['Text'] + _content['Image'] + _content['View'] + _content['Conditional'] + _content['Hyperlink'] + _content['Script'] + _content['Style'] + _content['Marker'] + _content['Clip'] + _content['Mask'] + _content['Gradient'] + _content['Pattern'] + _content['Filter'] + _content['Cursor'] + _content['Font'] + _content['ColorProfile']
	_open_tag = True

	def draw(self, surface:ht.Surface, *, paint:bool = True,
	         viewport:ty.Optional[ht.Viewport] = None):
		for child in self.child_elements():
			child.draw(surface, paint=paint, viewport=viewport)

	def bounding_box(self, *, with_transform:bool = True) -> ht.Box:
		# https://svgwg.org/svg2-draft/coords.html#bounding-box
		box = ht.Box()
		for child in self.child_elements():
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
			'fill', self.__class__._defaults['fill'], cascade=True)
		fill = helpers.colors.color(fill, fill_opacity*opacity)
		fill_rule = helpers.attribs.get_enum(
			self, 'fill-rule', helpers.attribs.FILL_RULES, cascade=True)

		stroke = self.get_attribute(
			'stroke', self.__class__._defaults['stroke'], cascade=True)
		stroke = helpers.colors.color(stroke, stroke_opacity*opacity)
		stroke_width = self.get_attribute(
			'stroke-width', self.__class__._defaults['stroke-width'], cascade=True)
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
