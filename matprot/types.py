from numpy import ndarray
from typing import Union, List, Dict, Any, Tuple
from pathlib import Path

TraceData = ndarray  #: A trace, i.e. an array of samples for one or more channels stored in a cachefile

FileName = Union[str, Path]  #: The name of a file in the operating system

MatFileContent = Dict[str, ndarray]  # the content of a converted mat-file

TargetCoords = Dict[
    int, Tuple[float, float, float]
]  # a dictionary of coordinates per target
