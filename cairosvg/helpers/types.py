import typing as ty

from .coordinates import Viewport, Length, PointError
from .geometry import Arc, Box
from .namespaces import Namespaces
from .root import Root
from .surface import Surface
from .transform import Transform

Point = ty.Union[str, ty.Sequence[Length]]
VertexList = ty.List[ty.Tuple[float, float]]
