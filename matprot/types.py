from numpy import ndarray
from typing import Union, List, Dict, Any, Tuple
from pathlib import Path

TraceData = ndarray  #: A trace, i.e. an array of samples for one or more channels stored in a cachefile

FileName = Union[str, Path]  #: The name of a file in the operating system

MatFileContent = Dict[str, ndarray]  # the content of a converted mat-file

Coordinate = Tuple[
    float, float, float
]  #: A coordinate tripled, i.e. x, y, z coordinates
