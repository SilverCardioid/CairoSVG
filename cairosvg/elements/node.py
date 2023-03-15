from __future__ import annotations
import typing as ty

from .. import helpers
from ..helpers import types as ht

class _Node:
	is_element = False

	def __init__(self, *, parent:ty.Optional[_Node] = None,
	             child_index:ty.Optional[int] = None,
	             namespaces:ty.Optional[ty.Dict[str,str]] = None):
		self._parent = parent
		self._children = []
		if parent is not None:
			# child
			if parent._can_have_child(self):
				if child_index is not None:
					parent._children.insert(child_index, self)
				else:
					parent._children.append(self)
			else:
				raise ValueError(f"{parent} node doesn't take {self} child node")
			self._root = parent._root
		else:
			# root
			self._root = helpers.root.Root(self, namespaces=namespaces)

	def _can_have_child(self, child:_Node):
		return True

	@property
	def id(self) -> ty.Optional[str]:
		return None
	@id.setter
	def id(self, value:str):
		raise NotImplementedError("non-element node can't have an ID")
	@id.deleter
	def id(self):
		raise NotImplementedError("non-element node can't have an ID")

	@property
	def parent(self) -> ty.Optional[_Node]:
		return self._parent
	@parent.setter
	def parent(self, elem:ty.Optional[_Node]):
		if elem:
			elem.add_child(self)
		else:
			self.detach()

	@property
	def children(self) -> ty.Tuple[_Node, ...]:
		return tuple(self._children)

	@property
	def depth(self) -> int:
		return 0 if self.is_root() else self.parent.depth + 1

	@property
	def root(self) -> _Node:
		return self._root.element

	def is_root(self) -> bool:
		"""Check whether this node is the root of an element tree."""
		return self.root is self

	def _set_id(self, value:str):
		if value in self._root._ids:
			print('warning: duplicate ID ignored: ' + value)
		else:
			self._root._ids[value] = self

	def _get_auto_id(self, prefix:str,
	                 id_list:ty.Optional[ty.List[str]] = None) -> str:
		# Find the first free ID of the form prefix+number
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

	def change_id(self, *args, **kwargs):
		raise NotImplementedError("non-element node can't have an ID")

	def child_elements(self) -> ty.List[_Node]:
		"""Get a list of element child nodes."""
		return [e for e in self._children if e.is_element]

	def delete(self, recursive:bool = True):
		"""Delete this node from the tree.
		Remove the node from its parent and children, without creating a
		new element tree. Further method calls on the node may fail.
		If `recursive` is True, the method will be called recursively on the
		node's descendants. Otherwise, its direct children will be detached
		into their own element trees.
		"""
		if self.parent:
			self.parent._children.remove(self)

		if recursive:
			while len(self._children) > 0:
				self._children[-1].delete(True)
		else:
			while len(self._children) > 0:
				self._children[-1].detach()

		# ID cleanup
		if self.id:
			del self._root._ids[self.id]
		if not recursive:
			self._root._update_ids()

		self._parent = None
		self._root = None

	def detach(self):
		"""Disconnect this element from the tree.
		Remove the element from its parent, and make it the root of a new
		element tree including its descendants.
		"""
		old_root = self._root
		parent = self.parent
		if parent:
			self._parent = None
			parent._children.remove(self)
			self._root = ht.Root(self)
			for e in self.descendants(False, elements_only=False):
				e._root = self._root

			self._root._update_ids()
			for eid in self._root._ids:
				del old_root._ids[eid]

	def add_child(self, node:_Node, child_index:ty.Optional[int] = None):
		if node in self.ancestors(True):
			raise ValueError('can\'t add a node\'s ancestor to itself')
		if not self._can_have_child(node):
			raise ValueError(f"{parent} node doesn't take {self} child node")

		different_tree = True
		if node.parent:
			# Remove from parent if node stays within the same tree;
			# else, detach entirely
			if self._root is node._root:
				different_tree = False
				node.parent._children.remove(node)
			else:
				node.detach()

		if child_index is not None:
			self._children.insert(child_index, node)
		else:
			self._children.append(node)
		node._parent = self

		if different_tree:
			assert node.is_root()
			id_conflicts = node._root._ids.keys() & self._root._ids.keys()
			if id_conflicts:
				print('warning: duplicate ids changed: ' + ', '.join(id_conflicts))
				id_list = node._root._ids.keys() | self._root._ids.keys()
				for eid in id_conflicts:
					elem = node._root._ids[eid]
					new_id = elem._get_auto_id(eid, id_list)
					elem.change_id(new_id)
			self._root._ids.update(node._root._ids)
			for e in node.descendants(True, elements_only=False):
				e._root = self._root

	def add_text_node(self, text:str, *, child_index:ty.Optional[int] = None):
		"""Add a text node as a child of this node."""
		return TextNode(text, parent=self, child_index=child_index)

	def add_comment(self, text:str, *, child_index:ty.Optional[int] = None):
		"""Add an XML comment as a child of this node."""
		return Comment(text, parent=self, child_index=child_index)

	def descendants(self, include_self:bool = True, *,
	                elements_only:bool = True
	                ) -> ty.Generator[_Node, None, None]:
		"""A generator of the node's descendants.
		Traverses the node's subtree (children, grandchildren etc.), and
		yields nodes depth-first. If `include_self` is True, start with the
		node itself. By default, only consider element nodes; if `elements_only`
		is False, include text nodes and comments.
		"""
		if include_self and (not elements_only or self.is_element):
			yield self
		for child in self._children:
			yield from child.descendants(True, elements_only=elements_only)

	def ancestors(self, include_self:bool = True, *,
	              elements_only:bool = True
	              ) -> ty.Generator[_Node, None, None]:
		"""A generator of the node's ancestors.
		Yields the node's parent, grandparent, etc., up to the root node. If
		`include_self` is True, start with the node itself. By default, only
		consider element nodes; if `elements_only` is False, include text nodes
		and comments.
		"""
		if include_self and (not elements_only or self.is_element):
			yield self
		anc = self.parent
		while anc:
			if not elements_only or anc.is_element:
				yield anc
				anc = anc.parent

	def code(self, **kwargs):
		raise NotImplementedError()

	def write_code(self, file:ty.Optional[ty.TextIO] = None,
	               indent:ty.Optional[str] = '', indent_depth:int = 0,
	               newline:ty.Optional[str] = '\n', **kwargs):
		indent = indent or ''
		newline = newline or ''
		indentation = indent_depth*indent
		tag = self.code(**kwargs)
		file.write(f'{indentation}{tag}{newline}')

	def draw(self, surface:ht.Surface, **kwargs):
		raise NotImplementedError()


class TextNode(_Node):
	def __init__(self, text, *, parent:ty.Optional[_Node] = None,
	             child_index:ty.Optional[int] = None):
		super().__init__(parent=parent, child_index=child_index)
		self.text = text

	def __repr__(self) -> str:
		return f'TextNode({self.text!r})'

	def _can_have_child(self, child:_Node):
		return False

	def code(self):
		return self.text


class Comment(_Node):
	def __init__(self, text, *, parent:ty.Optional[_Node] = None,
	             child_index:ty.Optional[int] = None):
		super().__init__(parent=parent, child_index=child_index)
		self.text = text

	def __repr__(self) -> str:
		return self.code()

	def _can_have_child(self, child:_Node):
		return False

	def code(self):
		return '<!-- ' + self.text + ' -->'
