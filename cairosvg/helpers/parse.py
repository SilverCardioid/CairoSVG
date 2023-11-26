import re
import typing as ty
from xml.etree import ElementTree as ET

from ..elements import _creators
from . import namespaces

if ty.TYPE_CHECKING:
	from ..elements.node import _Node

def parse(source:ty.Union[str, ty.TextIO]
          ) -> ty.Generator[ty.Tuple[str, '_Node'], None, None]:
	events = ET.iterparse(source, events=["start", "end", "comment", "pi", "start-ns", "end-ns"])
	# Each item is the parent of the next;
	# retrieve None for root's parent
	elem_stack = [None] # csvg Element objects
	xml_stack = [None]  # etree Element objects

	next_ev, next_xml = next(events, (None, None))
	while next_ev:
		# Collect namespace declarations by the next element
		new_ns = {}
		while next_ev == 'start-ns':
			new_ns[next_xml[0]] = next_xml[1]
			next_ev, next_xml = next(events, (None, None))
		if new_ns:
			assert next_ev == 'start'

		if next_ev == 'start':
			# Preceding text in parent element
			parent = elem_stack[-1]
			xml_parent = xml_stack[-1]
			if xml_parent:
				text = xml_parent.text and xml_parent.text.strip()
				if text:
					text_node = parent.add_text_node(text)
					yield ('text', text_node)

			# Create element
			ns_name, ns_prefix, tag = namespaces._split(next_xml.tag)
			if ns_prefix:
				# Undefined prefix; keep prefix in tag
				print(f'undefined namespace prefix "{ns_prefix}:"')
				tag = ns_prefix + ':' + tag
			if ns_name == namespaces.NS_SVG and tag in _creators:
				elem = _creators[tag](parent, **next_xml.attrib)
			else:
				# Custom element
				print_tag = tag if ns_name == namespaces.NS_SVG else next_xml.tag
				print(f'<{print_tag}> node not supported; can be saved but not drawn')
				elem = _creators['custom'](parent, tag, ns_name, **next_xml.attrib)
			elem_stack.append(elem)
			xml_stack.append(next_xml)

			if new_ns:
				# Add declared namespaces
				ns = elem._root.namespaces
				if not elem.is_root():
					print('namespace declarations moved to root element')
				for ns_prefix, ns_name in new_ns.items():
					if not ns_prefix:
						# new default namespace; assign prefix if there isn't one
						if ns_name in ns._names:
							continue
						else:
							# try using the final part of the namespace name
							tail = re.search('\w+$', ns_name)
							ns_prefix = ns._get_prefix(
								ns_name, default_prefix=tail and tail[0])
					if ns_prefix in ns:
						if ns[ns_prefix] != ns_name:
							# Same prefix for different name
							new_prefix = ns._get_prefix(
								ns_name, default_prefix=ns_prefix)
							print(f'duplicate prefix "{ns_prefix}:" changed to "{new_prefix}:"')
						# else, already included with same name
						continue
					# Add new prefix
					ns[ns_prefix] = ns_name
			yield ('start', elem)

		elif next_ev == 'end':
			# Element closing tag
			elem = elem_stack.pop()
			xml_stack.pop()

			# Text content (if not already yielded before child element)
			if len(elem._children) == 0:
				text = next_xml.text and next_xml.text.strip()
				if text:
					text_node = elem.add_text_node(text)
					yield ('text', text_node)

			yield ('end', elem)

			# Following text in parent element
			tail = next_xml.tail and next_xml.tail.strip()
			if tail:
				text_node = elem_stack[-1].add_text_node(tail)
				yield ('text', text_node)

		elif next_ev == 'comment':
			# <!-- comment -->
			text = next_xml.text.strip() if next_xml.text else ''
			comment = elem_stack[-1].add_comment(text)
			yield ('comment', comment)

		next_ev, next_xml = next(events, (None, None))


def read(source:ty.Union[str, ty.TextIO]) -> '_Node':
	elem_it = parse(source)
	# First element = root
	ev, root = next(elem_it, (None, None))
	# Parse the rest of the tree
	while ev:
		ev, elem = next(elem_it, (None, None))
		if ev == 'start' and elem.is_root():
			print(f'multiple root-level elements')
	return root
