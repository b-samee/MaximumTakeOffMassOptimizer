import typing
import pathlib
import numpy

RunConfiguration: typing.TypeAlias = dict[str, numpy.float64 | dict[str, numpy.float64] | list[dict[str, pathlib.Path]]]
