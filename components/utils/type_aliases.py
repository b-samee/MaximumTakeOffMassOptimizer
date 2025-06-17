import typing
import pathlib
import numpy

Pairing: typing.TypeAlias = dict[str, pathlib.Path]

RunConfiguration: typing.TypeAlias = dict[str, numpy.float64 | dict[str, numpy.float64] | list[Pairing]]
