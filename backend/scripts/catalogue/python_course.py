"""The Python course: twenty lessons from the interpreter to a finished CLI."""

from .helpers import Q, lesson, quiz

PYTHON_COURSE = {
    "title": "Python Programming",
    "category": "Python",
    #: ₹349 to unlock the whole course. Paise, as everywhere in the codebase.
    "price_paise": 34900,
    "description": (
        "Python from first principles to production habits: syntax and collections, "
        "functions and errors, classes, generators, typing, the standard library, tests "
        "and concurrency. Each lesson carries a quiz so the idea is checked before you "
        "move on."
    ),
    "topics": [
        lesson(
            "Running Python: interpreter, script, REPL",
            "TqPzwenhMj0",
            r"""## Three ways in

Python is read and executed line by line, so you can try an idea without writing
a file:

```bash
python                 # the REPL: type, press enter, see the result
python app.py          # run a file as a script
python -m http.server  # run a module from the standard library
```

In the REPL, `exit()` leaves. In a script, the interpreter reads the file top to
bottom and stops at the first unhandled error.

## Blocks are indentation

Curly braces do not exist. A colon opens a block and the indentation decides
where it ends:

```python
def reward(percent):
    if percent >= 70:
        return 2000
    return 0
```

Four spaces per level, never tabs mixed with spaces. The blank line between
functions is a convention, not a rule.

## Comments and names

`#` starts a comment. Names use lowercase words joined by underscores, classes
use `CapitalisedWords`, and constants are `UPPER_CASE`. A name that needs a
comment to explain it usually needs a better name.

## Check your interpreter

```python
import sys
print(sys.version)
```

Every modern tutorial assumes Python 3.7 or newer; anything older is missing
f-strings and dataclasses.""",
            quiz(
                "Running Python check",
                2000,
                [
                    Q(
                        "Which command runs a file called app.py?",
                        ["python app.py", "run app.py", "python -m app.py", "py.run app"],
                        0,
                    ),
                    Q("What do colons and indentation define in Python?", ["Comments", "Blocks", "Types", "Modules"], 1),
                    Q("What does REPL stand for?", ["Read-eval-print loop", "Rapid execution", "Runtime environment", "Reference"], 0),
                    Q("Which symbol starts a comment?", ["//", "#", "--", "/*"], 1),
                    Q(
                        "Which naming style is conventional for a class?",
                        ["snake_case", "CapitalisedWords", "UPPER_CASE", "kebab-case"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Variables, numbers and strings",
            "Eaz5e6M8tL4",
            r"""## Names point at values

A variable is a name bound to an object. No type declaration is needed:

```python
price = 149          # int
ratio = 0.75         # float
name = "Learnora"    # str
paid = True          # bool
```

`type(value)` tells you what you have. `int`, `float`, `str` and `bool` cover most
day-to-day work.

## Arithmetic

`+ - * /` behave as expected, with `/` always returning a float. `//` is floor
division and `%` is the remainder:

```python
7 / 2    # 3.5
7 // 2   # 3
7 % 2    # 1
2 ** 10  # 1024
```

Division by zero raises `ZeroDivisionError` rather than returning infinity.

## Strings do the work

```python
greeting = "hello"
greeting.upper()             # 'HELLO'
greeting.replace("h", "j")   # 'jello'
f"Total: {price * 2} INR"    # 'Total: 298 INR'
```

Strings are immutable: every method returns a new string. `len(text)` counts
characters, `text[0]` is the first one, and `text.split(",")` turns text into a
list. f-strings are the readable way to build a message.""",
            quiz(
                "Numbers and strings check",
                2000,
                [
                    Q("What is `7 // 2`?", ["3.5", "3", "4", "1"], 1),
                    Q("What type does `7 / 2` return?", ["int", "float", "str", "bool"], 1),
                    Q(
                        "Which expression formats a value into a string?",
                        ['f"Total: {price}"', '"Total: {price}"', 'f"Total: (price)"', 'format"Total"'],
                        0,
                    ),
                    Q("Strings in Python are:", ["Mutable", "Immutable", "Numbers", "Lists"], 1),
                    Q("What does `len('Learnora')` return?", ["7", "8", "9", "0"], 1),
                ],
            ),
        ),
        lesson(
            "Lists, tuples and dictionaries",
            "6SPDvPK38tw",
            r"""## Ordered collections

A list is mutable and keeps order; a tuple is immutable and can be used as a
dictionary key.

```python
skills = ["python", "sql"]
skills.append("c")
skills[0] = "python3"

point = (3, 4)
x, y = point            # unpacking
```

Negative indexes count from the end: `skills[-1]` is the last item. Slicing
takes a copy: `skills[1:3]`.

## Dictionaries

A dict maps keys to values and keeps insertion order:

```python
scores = {"python": 90, "sql": 75}
scores["c"] = 82
for name, score in scores.items():
    print(name, score)

scores.get("rust", 0)   # 0 instead of KeyError
```

Use `get` when a missing key is normal, and square brackets when a missing key is
a bug you want to hear about.

## Choosing a container

A list is right when order matters and you iterate. A tuple is right for a fixed
record. A dict is right when you look things up by name. Reaching for the wrong
one usually shows up as a slow loop or a search by index.""",
            quiz(
                "Collections check",
                2200,
                [
                    Q("Which bracket creates a list?", ["()", "[]", "{}", "<>"], 1),
                    Q("Which collection is immutable?", ["list", "dict", "tuple", "set"], 2),
                    Q("What does `skills[-1]` return?", ["The first item", "The last item", "An error", "The length"], 1),
                    Q(
                        "Which call avoids a KeyError for a missing key?",
                        ["scores['rust']", "scores.get('rust')", "scores.pop()", "scores.items()"],
                        1,
                    ),
                    Q("`dict.items()` gives you:", ["Keys only", "Values only", "Key/value pairs", "A copy of the dict"], 2),
                ],
            ),
        ),
        lesson(
            "Sets and comprehensions",
            "aequTxAvQq4",
            r"""## Sets answer 'have I seen this?'

A set stores unique values with no order, which makes membership fast and
duplicates impossible:

```python
seen = {"python", "sql"}
seen.add("c")
seen.add("python")     # no effect
"sql" in seen          # True
seen & {"sql", "go"}   # {'sql'} - intersection
seen | {"go"}          # union
```

Use a set to deduplicate a list (`set(items)`) or to compare two lists of names.

## Comprehensions build a collection in one line

```python
scores = [55, 72, 90, 68]
passed = [s for s in scores if s >= 70]
doubled = [s * 2 for s in scores]
labels = {s: ("pass" if s >= 70 else "retry") for s in scores}
```

The shape is always `[expression for item in iterable if condition]`. Prefer it
over building a list with `append` in a loop - it states the intent once.

## Keep them shallow

One `for` and one `if` stay readable. Two nested comprehensions usually mean a
named function would be clearer. A comprehension that needs a comment should be
a loop.""",
            quiz(
                "Sets and comprehensions check",
                2300,
                [
                    Q("A set stores:", ["Unique values, unordered", "Duplicates", "Key/value pairs", "Only numbers"], 0),
                    Q("What does `{1, 2} | {2, 3}` produce?", ["{1, 2, 3}", "{2}", "{1, 3}", "An error"], 0),
                    Q(
                        "What does `[s for s in scores if s > 70]` build?",
                        ["All scores", "Only scores above 70", "A dict", "A tuple"],
                        1,
                    ),
                    Q("How do you deduplicate a list quickly?", ["list(items)", "set(items)", "sorted(items)", "items.copy()"], 1),
                    Q("A set membership test costs roughly:", ["O(n)", "O(log n)", "O(1)", "O(n^2)"], 2),
                ],
            ),
        ),
        lesson(
            "Control flow: if, while and for",
            "Y21OR1OPC9A",
            r"""## Branching

```python
if score >= 70:
    status = "passed"
elif score >= 50:
    status = "close"
else:
    status = "retry"
```

Any non-empty value is truthy: `0`, `""`, `[]`, `{}` and `None` are falsy.
Comparisons can be chained: `50 <= score < 70` means exactly what it says.

## Looping

`for` walks over anything iterable. `enumerate` adds the index, `zip` walks two
sequences in step:

```python
for index, name in enumerate(names, start=1):
    print(index, name)

for name, score in zip(names, scores):
    print(name, score)
```

`while` repeats while a condition holds. `break` leaves the loop; `continue`
skips to the next item. Python's `for` also has an `else` block that runs only
when no `break` happened - useful for search loops.

## range

`range(3)` produces `0, 1, 2`. `range(1, 10, 2)` produces `1, 3, 5, 7, 9`. It is
lazy, so a huge range costs nothing until you iterate it.""",
            quiz(
                "Control flow check",
                2300,
                [
                    Q("What does `range(3)` produce when looped over?", ["1, 2, 3", "0, 1, 2", "0, 1, 2, 3", "3"], 1),
                    Q("Which values are falsy?", ["0, '', [], None", "1 and 'a'", "Only False", "Only 0"], 0),
                    Q("What does `enumerate` add?", ["A copy", "The index", "A key", "A type"], 1),
                    Q("What does `break` do?", ["Skips one item", "Exits the loop", "Restarts the loop", "Raises an error"], 1),
                    Q("Is `50 <= score < 70` valid Python?", ["Yes", "No", "Only in Python 2", "Only with parentheses"], 0),
                ],
            ),
        ),
        lesson(
            "Functions, arguments and scope",
            "eRWOdpludPM",
            r"""## Name the work

```python
def reward_for(percent, reward=2000, *, minimum=70):
    '''Return the reward earned for a quiz percentage.'''
    return reward if percent >= minimum else 0
```

Arguments can have defaults, and everything after `*` must be passed by name,
which keeps call sites readable: `reward_for(83, minimum=80)`.

Return a value instead of printing when the caller needs the result. A function
that returns `None` on every path is really a procedure - fine, but name it like
one (`print_report`) rather than `get_report`.

## Scope

Names created inside a function are local. Reading a global works; rebinding one
needs `global`, which is usually a sign the state belongs in an argument or a
class instead.

```python
total = 0

def add(amount):
    global total      # avoid when you can
    total += amount
```

## Small and honest

A function should do one thing and say so in its name. Type hints and a docstring
are not decoration: they are the contract the next caller relies on. Avoid mutable
default arguments (`def f(items=[])`) - the list is created once and shared.""",
            quiz(
                "Functions check",
                2400,
                [
                    Q("Which keyword defines a function?", ["func", "def", "function", "lambda"], 1),
                    Q(
                        "What does a parameter after `*` require?",
                        ["A default", "Being passed by name", "Being an int", "Being optional"],
                        1,
                    ),
                    Q(
                        "Why avoid `def f(items=[])`?",
                        ["It is slow", "The default list is shared between calls", "It fails to compile", "It needs a type hint"],
                        1,
                    ),
                    Q("Variables created inside a function are:", ["Global", "Local", "Constant", "Shared"], 1),
                    Q("What is the cleanest way to return a result?", ["print it", "return it", "Store it globally", "Write it to a file"], 1),
                ],
            ),
        ),
        lesson(
            "Errors and exceptions",
            "Yh4CrPHVBdE",
            r"""## Failures are values too

An exception stops the current block and travels up until something handles it:

```python
try:
    score = int(raw)
except ValueError:
    score = 0
```

Catch the specific error you expect. A bare `except:` hides programming mistakes
along with the data problems.

## else and finally

```python
try:
    handle = open(path)
except OSError as error:
    print("cannot open:", error)
else:
    with handle:
        data = handle.read()
finally:
    print("done")
```

`else` runs only when no exception happened; `finally` always runs, which is where
cleanup belongs. In practice `with` handles most cleanup for you.

## Raise your own

```python
def withdraw(balance, amount):
    if amount > balance:
        raise ValueError("amount exceeds balance")
    return balance - amount
```

Raise early with a clear message. Callers can then decide whether to retry, ask
again or stop. `error.args` and `str(error)` carry what you put in.""",
            quiz(
                "Exceptions check",
                2400,
                [
                    Q("Which block runs when no error occurs?", ["except", "finally", "else", "raise"], 2),
                    Q("Which block always runs?", ["else", "finally", "except", "try"], 1),
                    Q("What is wrong with a bare `except:`?", ["It is slow", "It hides programming mistakes", "It is invalid syntax", "It only catches OSError"], 1),
                    Q("How do you signal a bad argument?", ["return None", "raise ValueError", "print a warning", "exit(0)"], 1),
                    Q("What is raised by `int('abc')`?", ["TypeError", "ValueError", "KeyError", "OSError"], 1),
                ],
            ),
        ),
        lesson(
            "Reading and writing files",
            "YuRO9-rOgv4",
            r"""## Use with

`with` closes the file even if the block raises:

```python
with open("rewards.csv", encoding="utf-8") as handle:
    for line in handle:
        print(line.strip())
```

Modes: `"r"` read, `"w"` write and truncate, `"a"` append, `"x"` create and fail
if it exists. Add `"b"` for binary. Always pass `encoding="utf-8"` unless you
have a reason not to - the default varies by platform.

## Writing

```python
with open("report.txt", "w", encoding="utf-8") as out:
    out.write("reward,2000\n")
```

Iterating a file yields one line at a time, so memory stays flat on large files.
`read()` on a 2 GB log will not.

## Paths

`pathlib` beats string concatenation:

```python
from pathlib import Path

folder = Path("data")
folder.mkdir(exist_ok=True)
report = folder / "report.txt"
print(report.exists(), report.suffix)
```

It handles separators, joins and suffixes the same way on every platform.""",
            quiz(
                "Files check",
                2500,
                [
                    Q("Which mode appends instead of replacing?", ["'r'", "'w'", "'a'", "'x'"], 2),
                    Q("Why use `with open(...)`?", ["It is faster", "It closes the file for you", "It compresses it", "It is required"], 1),
                    Q("Which call reads one line at a time?", ["handle.read()", "iterating over the handle", "handle.seek()", "handle.flush()"], 1),
                    Q("Which mode fails when the file already exists?", ["'r'", "'w'", "'a'", "'x'"], 3),
                    Q("What is the modern way to build a path?", ["String concatenation", "pathlib.Path", "os.sep only", "A tuple"], 1),
                ],
            ),
        ),
        lesson(
            "Modules, packages and virtual environments",
            "LJC8277LONg",
            r"""## A module is a file

Any `.py` file can be imported. Split work into modules instead of growing one
long script:

```python
from rewards import calculate_reward
import statistics
```

The import path matters: `rewards.py` must be next to the importing file or on
`sys.path`. A folder with an `__init__.py` is a package, so `from app.services
import ledger` works.

## The main guard

```python
if __name__ == "__main__":
    main()
```

This lets a file be both importable and runnable without firing the CLI on
import.

## One environment per project

```bash
python -m venv .venv
.venv\\Scripts\\activate      # Windows
pip install requests
pip freeze > requirements.txt
```

A virtual environment is a private `site-packages` folder. Two projects can pin
different versions of the same package without arguing. Commit
`requirements.txt`; never commit `.venv`.""",
            quiz(
                "Modules check",
                2500,
                [
                    Q(
                        "What does a virtual environment isolate?",
                        ["Your source files", "Installed packages per project", "Your database", "Your editor"],
                        1,
                    ),
                    Q("Which command records exact versions?", ["pip list --all", "pip freeze", "pip show", "pip search"], 1),
                    Q("What is a Python module?", ["A compiled binary", "A file you can import", "A virtual machine", "A built-in function"], 1),
                    Q("What makes a folder a package?", ["Only a name", "An `__init__.py` file", "A README", "A requirements file"], 1),
                    Q(
                        "What does `if __name__ == '__main__'` guard?",
                        ["Imports", "Code that should run only as a script", "Type checks", "Exceptions"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Classes and objects",
            "wHUOeXbZCYA",
            r"""## A class groups state and behaviour

```python
class Wallet:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def credit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount
        return self.balance

wallet = Wallet("Asha")
wallet.credit(500)
```

`self` is the object being worked on; it is passed automatically. `__init__`
runs when the object is created and is where invariants get established.

## Attributes

Instance attributes belong to one object. Class attributes are shared, which is
why a mutable one is dangerous:

```python
class Course:
    kind = "language"          # shared, fine because it is a string
    def __init__(self):
        self.topics = []       # per object, correct
```

Reach for a class when data and the rules that protect it travel together. A
plain function over a dict is better for anything simpler.""",
            quiz(
                "Classes check",
                2600,
                [
                    Q("Which method runs when an object is created?", ["__new__ only", "__init__", "__call__", "__main__"], 1),
                    Q("What does `self` refer to?", ["The class", "The instance being used", "The module", "A global"], 1),
                    Q(
                        "Why is a mutable class attribute risky?",
                        ["It is slow", "It is shared by every instance", "It cannot be typed", "It is private"],
                        1,
                    ),
                    Q("How do you read an instance attribute?", ["self.attr", "self->attr", "this.attr", "class.attr"], 0),
                    Q(
                        "When is a class the right choice?",
                        [
                            "For every helper function",
                            "When state and the rules around it belong together",
                            "Only for inheritance",
                            "Never",
                        ],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Inheritance, dunder methods and dataclasses",
            "IUqKuGNasdM",
            r"""## Inheritance is for shared behaviour

```python
class Member:
    def __init__(self, name):
        self.name = name

    def plan(self):
        return "free"

class Subscriber(Member):
    def plan(self):
        return "member"

class Trial(Subscriber):
    def plan(self):
        return super().plan() + " (trial)"
```

Override only what differs and call `super()` to reuse the rest. Inheritance is
for an is-a relationship; composing small objects is usually simpler.

## Dunder methods make objects behave

```python
class Money:
    def __init__(self, paise):
        self.paise = paise

    def __repr__(self):
        return f"Money({self.paise})"

    def __add__(self, other):
        return Money(self.paise + other.paise)
```

`__repr__` for developers, `__str__` for users, `__eq__` for comparison,
`__len__` and `__iter__` for containers.

## dataclasses

When a class is mostly fields, let the decorator write the boilerplate:

```python
from dataclasses import dataclass

@dataclass
class Topic:
    title: str
    reward: int = 0
```""",
            quiz(
                "Inheritance check",
                2600,
                [
                    Q("How do you call a parent implementation?", ["parent()", "super()", "base()", "self.parent"], 1),
                    Q("Which method gives a developer-facing string?", ["__str__", "__repr__", "__init__", "__eq__"], 1),
                    Q("Which decorator generates `__init__` and `__repr__`?", ["@dataclass", "@staticmethod", "@property", "@classmethod"], 0),
                    Q(
                        "Inheritance models which relationship?",
                        ["has-a", "is-a", "uses-a", "owns-a"],
                        1,
                    ),
                    Q("Which method supports `a + b`?", ["__add__", "__sum__", "__plus__", "__iadd__"], 0),
                ],
            ),
        ),
        lesson(
            "Iterators and generators",
            "viTHc_4XfCA",
            r"""## Iteration is a protocol

`for` calls `iter()` once and then `next()` until `StopIteration`. Anything that
supports those two calls is iterable.

```python
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1
```

## Generators write that for you

A function with `yield` returns a generator: values are produced on demand, one
at a time.

```python
def rewards(percents):
    for percent in percents:
        if percent >= 70:
            yield 2000

total = sum(rewards([55, 80, 92]))   # 4000
```

Because it is lazy, a generator can stream a file or an API page-by-page without
holding everything in memory. Generators are single-use: iterating again after
they finish gives nothing.

## Practice

Write a generator that yields the running total of a list of amounts, and check
it against a manual sum.""",
            quiz(
                "Iterators check",
                2700,
                [
                    Q("Which keyword turns a function into a generator?", ["return", "yield", "async", "emit"], 1),
                    Q("What ends iteration?", ["return value", "StopIteration", "break", "None"], 1),
                    Q("Generators are:", ["Eager", "Lazy", "Immutable", "Always lists"], 1),
                    Q("How many times can a generator be iterated?", ["Once", "Twice", "Forever", "As often as memory allows"], 0),
                    Q("Which method gets an iterator from an iterable?", ["next()", "iter()", "len()", "list()"], 1),
                ],
            ),
        ),
        lesson(
            "Decorators and closures",
            "dFuVh_Bzy9c",
            r"""## Functions are values

A function can take another function and return one:

```python
def timed(work):
    def wrapper(*args, **kwargs):
        print("starting", work.__name__)
        result = work(*args, **kwargs)
        print("finished", work.__name__)
        return result
    return wrapper

@timed
def load_courses():
    return ["c", "python"]
```

`@timed` is exactly `load_courses = timed(load_courses)`. The decorator wraps the
behaviour without touching the body, which is why logging, timing and caching
are usually decorators.

## Closures remember their environment

`wrapper` keeps `work` alive after `timed` has returned. That captured variable
is a closure. `functools.wraps` copies the name and docstring onto the wrapper so
tracebacks and help still make sense.

```python
from functools import wraps
```

## When not to

A decorator that changes what the function returns, or hides arguments, becomes
a puzzle. Keep them to cross-cutting concerns and pass configuration through
arguments.""",
            quiz(
                "Decorators check",
                2700,
                [
                    Q("Which syntax applies a decorator?", ["@name", "#name", "name!", "decorate(name)"], 0),
                    Q(
                        "`@timed` above `def f()` is equivalent to:",
                        ["f = timed(f)", "timed = f()", "f(timed)", "timed(f())"],
                        0,
                    ),
                    Q("What does a closure capture?", ["Nothing", "Variables from its enclosing scope", "Only globals", "The call stack"], 1),
                    Q("What does `functools.wraps` preserve?", ["Speed", "Name and docstring", "Type hints", "Exceptions"], 1),
                    Q(
                        "Which task suits a decorator?",
                        ["Renaming a variable", "Timing or logging a call", "Declaring a class", "Catching every error"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Type hints and static checking",
            "lYnMyi81hrs",
            r"""## Hints document, tools check

```python
def total_reward(percents: list[int], reward: int = 2000) -> int:
    return sum(reward for percent in percents if percent >= 70)
```

Python does not enforce hints at run time. A type checker such as mypy or pyright
reads them and reports calls that cannot work before the code runs. That is the
point: catch the mistake in the editor, not after a payout.

## Useful pieces

```python
from typing import Optional

def find(name: str) -> Optional[int]:   # int | None
    ...

Pair = tuple[str, int]
```

`list[int]`, `dict[str, int]`, `str | None` and `Callable[[int], str]` cover most
signatures. Hints on public functions pay for themselves; hints on every local
variable usually do not.

## Dataclasses and models

Hints are what `@dataclass` reads to build `__init__`, and what FastAPI and
Pydantic use to validate request bodies. Well-hinted code gets validation and
editor completion for free.""",
            quiz(
                "Type hints check",
                2800,
                [
                    Q("Type hints are enforced:", ["At run time, always", "By a static checker, not the interpreter", "Never", "Only in classes"], 1),
                    Q("What does `-> int` annotate?", ["A parameter", "The return type", "A variable", "A decorator"], 1),
                    Q("Which type means 'int or None'?", ["int | None", "int", "object", "Any"], 0),
                    Q("Which tool checks hints without running code?", ["pytest", "mypy", "pip", "black"], 1),
                    Q("Which library uses hints to validate request bodies?", ["Pydantic", "NumPy", "Rich", "Click"], 0),
                ],
            ),
        ),
        lesson(
            "The standard library tour",
            "fhoDRB53DwY",
            r"""## Batteries included

Most Python is a thin layer over modules that already exist. Learn these and you
skip a dependency.

| Module | Use it for |
| --- | --- |
| `collections` | `Counter`, `defaultdict`, `deque` |
| `itertools` | `chain`, `groupby`, `islice` |
| `datetime` | dates, durations, time zones |
| `pathlib` | file system paths |
| `json` / `csv` | data files |
| `math` / `statistics` | calculations |
| `re` | pattern matching |

```python
from collections import Counter

counts = Counter(["c", "python", "python"])
print(counts.most_common(1))     # [('python', 2)]
```

## Dates without pain

```python
from datetime import date, timedelta

today = date.today()
renew = today + timedelta(days=30)
print(renew.isoformat())
```

Use timezone-aware datetimes for anything a user sees across regions, and store
ISO 8601 strings or UTC timestamps rather than local time.

## Practice

Count the most common extension in a folder with `pathlib` and `Counter`.""",
            quiz(
                "Standard library check",
                2800,
                [
                    Q("Which module counts items quickly?", ["collections.Counter", "itertools.count", "math", "re"], 0),
                    Q("Which class adds a default for missing keys?", ["Counter", "defaultdict", "deque", "namedtuple"], 1),
                    Q("Which module handles paths cleanly?", ["os.path only", "pathlib", "glob", "shutil"], 1),
                    Q("Which class adds 30 days to a date?", ["date + 30", "timedelta(days=30)", "relativedelta(30)", "date.add(30)"], 1),
                    Q("Which module matches text patterns?", ["re", "csv", "json", "math"], 0),
                ],
            ),
        ),
        lesson(
            "JSON, CSV and HTTP",
            "TqPzwenhMj0",
            r"""## Data on disk

JSON maps directly onto dicts and lists:

```python
import json

payload = {"name": "Learnora", "topics": 38}
text = json.dumps(payload, indent=2)
back = json.loads(text)
```

For files use `json.dump(obj, handle)` and `json.load(handle)`. JSON has no
comments and no tuples - a tuple comes back as a list.

CSV is a table, so read it as rows of strings:

```python
import csv

with open("rewards.csv", newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        print(row["amount"])
```

Always pass `newline=""` when writing CSV, or Windows adds blank lines.

## Talking to an API

```python
import urllib.request

with urllib.request.urlopen("https://example.com/api", timeout=10) as response:
    data = json.load(response)
```

Check the status before trusting the body, set a timeout so a stalled server
cannot hang your program, and catch `URLError` / `HTTPError` rather than letting
a network blip crash the run.""",
            quiz(
                "JSON, CSV and HTTP check",
                2800,
                [
                    Q("Which call turns text into Python data?", ["json.dumps", "json.loads", "json.dump", "str"], 1),
                    Q("What does a JSON object become in Python?", ["A list", "A dict", "A tuple", "A string"], 1),
                    Q("Which class reads CSV rows as dictionaries?", ["csv.reader", "csv.DictReader", "csv.writer", "csv.table"], 1),
                    Q("Why pass `newline=''` to `open` for CSV?", ["It is faster", "It stops blank lines on writing", "It encodes UTF-8", "It is required for reading"], 1),
                    Q("Why set a timeout on an HTTP call?", ["It is required", "So a stalled server cannot hang the program", "It makes it secure", "It compresses the body"], 1),
                ],
            ),
        ),
        lesson(
            "Testing with pytest",
            "Eaz5e6M8tL4",
            r"""## Tests are just functions

```python
# tests/test_rewards.py
from rewards import reward_for

def test_full_reward():
    assert reward_for(80) == 2000

def test_below_threshold():
    assert reward_for(60) == 0
```

Run them with `pytest`. A test passes when no assertion fails. Name the file
`test_*.py` so the runner finds it.

## Fixtures build the world

```python
import pytest

@pytest.fixture
def wallet():
    from wallet import Wallet
    return Wallet("Asha", balance=100)

def test_credit(wallet):
    assert wallet.credit(50) == 150
```

Fixtures are reusable setup, created fresh for each test. `tmp_path` gives a
throwaway directory, `monkeypatch` swaps out a dependency for the duration of a
run.

## Cases and expected errors

```python
@pytest.mark.parametrize("percent,expected", [(0, 0), (70, 2000), (100, 2000)])
def test_thresholds(percent, expected):
    assert reward_for(percent) == expected

with pytest.raises(ValueError):
    withdraw(100, 500)
```

Test the behaviour you promise, not the internals. One assertion with a clear
name beats ten mysterious ones.""",
            quiz(
                "pytest check",
                2900,
                [
                    Q("What marks a test as failed?", ["print", "A failed assert", "return False", "A warning"], 1),
                    Q("Which decorator shares setup across tests?", ["@pytest.fixture", "@pytest.mark.skip", "@pytest.setup", "@fixture"], 0),
                    Q("Which decorator runs one test with many inputs?", ["@pytest.mark.parametrize", "@pytest.fixture", "@pytest.mark.slow", "@pytest.case"], 0),
                    Q("How do you assert that code raises?", ["try/except only", "pytest.raises", "assert raises", "pytest.fail"], 1),
                    Q("What does the `tmp_path` fixture give you?", ["A URL", "A temporary directory", "A database", "A mock"], 1),
                ],
            ),
        ),
        lesson(
            "Concurrency: threads, processes and asyncio",
            "6SPDvPK38tw",
            r"""## Three tools, three problems

| Tool | Good for | Cost |
| --- | --- | --- |
| `threading` | waiting on I/O | the GIL limits pure Python CPU work |
| `multiprocessing` | CPU-bound work | processes are expensive and do not share memory |
| `asyncio` | many network calls | everything below it must be async |

```python
import asyncio

async def fetch(name):
    await asyncio.sleep(0.5)          # stands in for a network call
    return name.upper()

async def main():
    results = await asyncio.gather(fetch("c"), fetch("python"))
    print(results)

asyncio.run(main())
```

## The rule that saves you

The event loop runs one coroutine at a time. One blocking call - `time.sleep`,
a synchronous HTTP request, a heavy loop - freezes everything else. Use async
libraries inside async code, and push CPU work to a process pool.

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as pool:
    totals = list(pool.map(download, urls))
```

Classes such as `ThreadPoolExecutor` are the least surprising way to start: the
pool owns the threads and closes them for you.""",
            quiz(
                "Concurrency check",
                2900,
                [
                    Q("Which tool suits waiting on many network calls?", ["threads", "asyncio", "multiprocessing", "A for loop"], 1),
                    Q("Which tool suits CPU-bound work in pure Python?", ["threads", "asyncio", "multiprocessing", "Futures only"], 2),
                    Q("What limits threads doing pure Python CPU work?", ["The OS", "The GIL", "The heap", "The event loop"], 1),
                    Q("What happens if you block inside a coroutine?", ["Nothing", "The whole event loop stalls", "It runs in another thread", "It raises an error"], 1),
                    Q("What does `asyncio.gather` do?", ["Runs one coroutine", "Runs several concurrently and collects results", "Creates threads", "Starts processes"], 1),
                ],
            ),
        ),
        lesson(
            "Packaging and project layout",
            "aequTxAvQq4",
            r"""## A layout that scales

```
project/
  pyproject.toml
  README.md
  src/learnora/__init__.py
  src/learnora/cli.py
  tests/test_cli.py
```

The `src` layout stops you importing the local folder by accident instead of
the installed package. Tests live outside the package.

## pyproject.toml

```toml
[project]
name = "learnora"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27"]

[project.scripts]
learnora = "learnora.cli:main"
```

`pip install -e .` installs the package in editable mode and creates the
`learnora` command from `[project.scripts]`. One tool, one file: dependencies,
metadata and tool settings all live here.

## Habits

Pin application dependencies in `requirements.txt` or in `pyproject.toml`, and
let a lock file capture exact versions for deployment. Keep `.venv`, `__pycache__`
and build output out of git. Tag releases rather than editing the version in
five places.""",
            quiz(
                "Packaging check",
                2900,
                [
                    Q("Which file declares project metadata and dependencies?", ["setup.cfg", "pyproject.toml", "requirements.txt only", "Makefile"], 1),
                    Q("What does `pip install -e .` do?", ["Builds a wheel", "Installs the project in editable mode", "Upgrades pip", "Freezes versions"], 1),
                    Q("Which table creates a console command?", ["[project.scripts]", "[tool.pytest]", "[project.urls]", "[build-system]"], 0),
                    Q("Why use a `src` layout?", ["It is faster", "It prevents importing the wrong copy", "It is required by pip", "It hides tests"], 1),
                    Q("What should never be committed?", ["pyproject.toml", "The test suite", "The virtual environment", "The README"], 2),
                ],
            ),
        ),
        lesson(
            "Capstone: a reporting CLI",
            "Y21OR1OPC9A",
            r"""## Put it together

A finished Python tool reads input, does one job, prints a result and exits with
a meaningful code:

```python
import argparse
import csv
from collections import Counter

def main(argv=None):
    parser = argparse.ArgumentParser(prog="learnora")
    parser.add_argument("path")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args(argv)

    with open(args.path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    counts = Counter(row["topic"] for row in rows)
    for name, count in counts.most_common(args.top):
        print(f"{name}: {count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

`argparse` gives you `--help`, validation and sane defaults. `SystemExit` carries
the exit code to the shell.

## The last 10%

Write one test per behaviour with `tmp_path`; run `pytest`. Keep the parsing,
the calculation and the printing in separate functions so each can be tested
without a real file. That is the difference between a script and a tool.""",
            quiz(
                "Capstone check",
                3200,
                [
                    Q("Which module parses command-line arguments?", ["sys", "argparse", "os", "click"], 1),
                    Q("What does `SystemExit` do?", ["Prints an error", "Ends the process with a code", "Raises a warning", "Restarts the script"], 1),
                    Q("Which exit code signals success?", ["1", "0", "255", "-1"], 1),
                    Q(
                        "Why separate parsing, calculation and printing?",
                        ["It is slower", "Each part can be tested on its own", "It looks better", "It avoids imports"],
                        1,
                    ),
                    Q("Which fixture creates files for a test?", ["monkeypatch", "tmp_path", "capsys", "request"], 1),
                ],
            ),
        ),
    ],
}
