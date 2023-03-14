import typing as ty
from xml.etree import ElementTree as ET

from ..elements import _creators
from . import namespaces

def parse(source:ty.Union[str, ty.TextIO]
          ) -> ty.Generator[ty.Tuple[str, 'Element'], None, None]:
	events = ET.iterparse(source, events=["start", "end", "comment", "pi", "start-ns", "end-ns"])
	elem_stack = []

	next_ev, next_elem = next(events, (None, None))
	while next_ev:
		new_ns = {}
		while next_ev == 'start-ns':
			new_ns[next_elem[0]] = next_elem[1]
			next_ev, next_elem = next(events, (None, None))
		if new_ns:
			assert next_ev == 'start'

		if next_ev == 'start':
			# Create element
			ns_name, ns_prefix, tag = namespaces._split(next_elem.tag)
			if ns_prefix:
				# Undefined prefix; keep prefix in tag
				print(f'undefined namespace prefix "{ns_prefix}:"')
				tag = ns_prefix + ':' + tag
			parent = elem_stack[-1] if len(elem_stack) > 0 else None
			if ns_name == namespaces.NS_SVG and tag in _creators:
				elem = _creators[tag](parent, **next_elem.attrib)
			else:
				# Custom element
				print(f'<{next_elem.tag}> node not supported; can be saved but not drawn')
				elem = _creators['custom'](parent, tag, ns_name, **next_elem.attrib)
			elem_stack.append(elem)

			if new_ns:
				# Add declared namespaces
				ns = elem._root.namespaces
				if not elem.is_root():
					print('namespace declarations moved to root element')
				for ns_prefix, ns_name in new_ns.items():
					if ns_prefix in ns:
						if ns[ns_prefix] != ns_name:
							# Same prefix for different name
							new_prefix = ns._get_prefix(ns_name, default_prefix=ns_prefix)
							print(f'duplicate prefix "{ns_prefix}:" changed to "{new_prefix}:"')
						# else, already included with same name
						continue
					# Add new prefix
					ns[ns_prefix] = ns_name
			yield ('start', elem)

		elif next_ev == 'end':
			yield ('end', elem_stack.pop())

		# todo: comments (next_ev == 'comment'), text nodes (next_elem.text / next_elem.tail)

		next_ev, next_elem = next(events, (None, None))


def read(source:ty.Union[str, ty.TextIO]) -> 'Element':
	elem_it = parse(source)
	# First element = root
	ev, root = next(elem_it, (None, None))
	# Parse the rest of the tree
	while ev:
		ev, elem = next(elem_it, (None, None))
		if ev == 'start' and elem.is_root():
			print(f'multiple root-level elements')
	return root
