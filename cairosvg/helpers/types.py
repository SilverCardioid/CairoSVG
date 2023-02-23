import typing as ty

from .coordinates import Viewport
from .geometry import Arc, Box
from .namespaces import Namespaces
from .root import Root
from .surface import Surface
from .transform import Transform

Length = ty.Union[str, int, float]
VertexList = ty.List[ty.Tuple[float, float]]

# Basic type subclasses to mark arguments that haven't been
# explicitly set, and should be omitted from exported code
class _Default: pass
class _intdef(int, _Default): pass
class _strdef(str, _Default): pass
