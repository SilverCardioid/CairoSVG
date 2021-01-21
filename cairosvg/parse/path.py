"""
Paths manager.

"""

from math import pi, radians

from ..draw.path import Path
from .bounding_box import calculate_bounding_box
from ..helpers import (
    PATH_LETTERS, clip_marker_box, node_format, normalize, point, point_angle,
    preserve_ratio, quadratic_points, rotate, size)
from .url import parse_url


def draw_markers(surface, node):
    """Draw the markers attached to a path ``node``."""
    if not getattr(node, 'path', None):
        return

    markers = {}
    common_marker = parse_url(node.get('marker', '')).fragment
    for position in ('start', 'mid', 'end'):
        attribute = 'marker-{}'.format(position)
        if attribute in node:
            markers[position] = parse_url(node[attribute]).fragment
        else:
            markers[position] = common_marker

    vertices = node.path.vertices()
    angles = node.path.vertexAngles()

    for i, vertex in enumerate(vertices):
        angle = angles[i]
        if i==0:
          position = 'start'
        elif i < len(vertices) - 1:
          position = 'mid'
        else:
          position = 'end'

        # Draw marker (if a marker exists for 'position')
        marker = markers[position]
        if marker:
            marker_node = surface.markers.get(marker)

            # Calculate scale based on current stroke (if requested)
            if marker_node.get('markerUnits') == 'userSpaceOnUse':
                scale = 1
            else:
                scale = size(
                    surface, surface.parent_node.get('stroke-width', '1'))

            # Calculate position, (additional) scale and clipping based on
            # marker properties
            viewbox = node_format(surface, marker_node)[2]
            if viewbox:
                scale_x, scale_y, translate_x, translate_y = preserve_ratio(
                    surface, marker_node)
                clip_box = clip_marker_box(
                    surface, marker_node, scale_x, scale_y)
            else:
                # Calculate sizes and position
                marker_width = size(surface,
                                    marker_node.get('markerWidth', '3'), 'x')
                marker_height = size(surface,
                                     marker_node.get('markerHeight', '3'), 'y')

                translate_x = -size(surface, marker_node.get('refX', '0'), 'x')
                translate_y = -size(surface, marker_node.get('refY', '0'), 'y')

                # No clipping or scaling since viewbox is not present
                scale_x = scale_y = 1
                clip_box = None

            # Add extra path for marker
            temp_path = surface.context.copy_path()
            surface.context.new_path()

            # Override angle (if requested)
            node_angle = marker_node.get('orient', '0')
            if node_angle not in ('auto', 'auto-start-reverse'):
                angle = radians(float(node_angle))
            elif node_angle == 'auto-start-reverse' and position == 'start':
                angle += radians(180)

            # Draw marker path
            # See http://www.w3.org/TR/SVG/painting.html#MarkerAlgorithm
            for child in marker_node.children:
                surface.context.save()
                surface.context.translate(*vertex)
                surface.context.rotate(angle)
                surface.context.scale(scale)
                surface.context.scale(scale_x, scale_y)
                surface.context.translate(translate_x, translate_y)

                # Add clipping (if present and requested)
                overflow = marker_node.get('overflow', 'hidden')
                if clip_box and overflow in ('hidden', 'scroll'):
                    surface.context.save()
                    surface.context.rectangle(*clip_box)
                    surface.context.restore()
                    surface.context.clip()

                surface.draw(child)
                surface.context.restore()

            surface.context.append_path(temp_path)


def path(surface, node):
    """Draw a path ``node``."""
    string = node.get('d', '')
    node.path = Path(fill='none')

    for letter in PATH_LETTERS:
        string = string.replace(letter, ' {} '.format(letter))

    string = normalize(string)

    while string:
        string = string.strip()
        if string.split(' ', 1)[0] in PATH_LETTERS:
            letter, string = (string + ' ').split(' ', 1)
        elif letter == 'M':
            letter = 'L'
        elif letter == 'm':
            letter = 'l'

        if letter in 'aA':
            # Elliptic curve
            rx, ry, string = point(surface, string)
            rotation, string = string.split(' ', 1)
            rotation = float(rotation)

            # The large and sweep values are not always separated from the
            # following values. These flags can only be 0 or 1, so reading a
            # single digit suffices.
            large, string = string[0], string[1:].strip()
            sweep, string = string[0], string[1:].strip()
            large, sweep = bool(int(large)), bool(int(sweep))

            x3, y3, string = point(surface, string)

            if letter=='A':
                node.path.A(rx, ry, rotation, large, sweep, x3, y3)
            else:
                node.path.a(rx, ry, rotation, large, sweep, x3, y3)

        elif letter == 'c':
            # Relative curve
            x1, y1, string = point(surface, string)
            x2, y2, string = point(surface, string)
            x3, y3, string = point(surface, string)
            node.path.c(x1, y1, x2, y2, x3, y3)

        elif letter == 'C':
            # Curve
            x1, y1, string = point(surface, string)
            x2, y2, string = point(surface, string)
            x3, y3, string = point(surface, string)
            node.path.C(x1, y1, x2, y2, x3, y3)

        elif letter == 'h':
            x, string = (string + ' ').split(' ', 1)
            x = size(surface, x, 'x')
            node.path.h(x)

        elif letter == 'H':
            # Horizontal line
            x, string = (string + ' ').split(' ', 1)
            x = size(surface, x, 'x')
            node.path.H(x)

        elif letter == 'l':
            # Relative straight line
            x, y, string = point(surface, string)
            node.path.l(x, y)

        elif letter == 'L':
            # Straight line
            x, y, string = point(surface, string)
            node.path.L(x, y)

        elif letter == 'm':
            # Current point relative move
            x, y, string = point(surface, string)
            node.path.m(x, y)

        elif letter == 'M':
            # Current point move
            x, y, string = point(surface, string)
            node.path.M(x, y)

        elif letter == 'q':
            # Relative quadratic curve
            x2, y2, string = point(surface, string)
            x3, y3, string = point(surface, string)
            node.path.q(x2, y2, x3, y3)

        elif letter == 'Q':
            # Quadratic curve
            x2, y2, string = point(surface, string)
            x3, y3, string = point(surface, string)
            node.path.Q(x2, y2, x3, y3)

        elif letter == 's':
            # Relative smooth curve
            x2, y2, string = point(surface, string)
            x3, y3, string = point(surface, string)
            node.path.s(x2, y2, x3, y3)

        elif letter == 'S':
            # Smooth curve
            x2, y2, string = point(surface, string)
            x3, y3, string = point(surface, string)
            node.path.S(x2, y2, x3, y3)

        elif letter == 't':
            # Relative quadratic curve end
            x3, y3, string = point(surface, string)
            node.path.t(x3, y3)

        elif letter == 'T':
            # Quadratic curve end
            x3, y3, string = point(surface, string)
            node.path.T(x3, y3)

        elif letter == 'v':
            # Relative vertical line
            y, string = (string + ' ').split(' ', 1)
            y = size(surface, y, 'y')
            node.path.v(y)

        elif letter == 'V':
            # Vertical line
            y, string = (string + ' ').split(' ', 1)
            y = size(surface, y, 'y')
            node.path.V(y)

        elif letter in 'zZ':
            # End of path
            node.path.z()

        string = string.strip()

    node.path._paint = lambda surface: None # hack to bypass painting by .draw
    node.path.draw(surface)