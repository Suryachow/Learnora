"""The catalogue Learnora ships with.

Two courses only, each taught end to end: C from the toolchain to a finished CLI,
and Python from the interpreter to a packaged command-line tool. Every lesson
carries a video to work through and a quiz that checks the idea.
"""

from .c_course import C_COURSE
from .python_course import PYTHON_COURSE

CATALOGUE = [C_COURSE, PYTHON_COURSE]

__all__ = ["CATALOGUE", "C_COURSE", "PYTHON_COURSE"]
