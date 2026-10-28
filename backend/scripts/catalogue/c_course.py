"""The C course: eighteen lessons from the toolchain to a finished CLI."""

from .helpers import Q, lesson, quiz

C_COURSE = {
    "title": "C Programming",
    "category": "C",
    #: ₹349 to unlock the whole course. Paise, as everywhere in the codebase.
    "price_paise": 34900,
    "description": (
        "Learn C the way it is actually used: compile real programs, master pointers "
        "and memory, then build data structures, file tools and a finished command-line "
        "project. Every lesson ends with a quiz that checks the idea, not the syntax."
    ),
    "topics": [
        lesson(
            "Getting started: source, compiler, program",
            "RSDzvlXmQi4",
            r"""## From text to a running program

A C file is text until a compiler turns it into machine code. The pipeline has
three steps and it helps to know which one failed:

1. **Preprocess** - pull in headers, expand macros.
2. **Compile** - translate each source file into an object file.
3. **Link** - join objects and libraries into one executable.

```c
#include <stdio.h>

int main(void) {
    printf("Hello, Learnora\n");
    return 0;
}
```

Build and run it:

```bash
gcc -Wall -Wextra -std=c17 hello.c -o hello
./hello
```

`main` returns `0` to tell the shell the program succeeded. Any other value is an
error code - that is how scripts and CI decide whether a build passed.

## Practice

Compile the program with `-Wall` on purpose without `#include <stdio.h>` and read
the warning before you fix it.""",
            quiz(
                "The C toolchain check",
                2200,
                [
                    Q(
                        "Which command builds hello.c into an executable called hello?",
                        ["gcc hello.c -o hello", "gcc hello -o hello.c", "gcc -o hello", "cc hello.c -run"],
                        0,
                    ),
                    Q(
                        "What does the linker do?",
                        [
                            "Turns source into assembly",
                            "Joins object files and libraries into one program",
                            "Runs the program",
                            "Formats the source code",
                        ],
                        1,
                    ),
                    Q(
                        "Which return value from main signals success?",
                        ["0", "1", "-1", "void"],
                        0,
                    ),
                    Q(
                        "What does `#include <stdio.h>` give you?",
                        [
                            "The declarations for printf and friends",
                            "The C runtime itself",
                            "A namespace",
                            "The linker",
                        ],
                        0,
                    ),
                    Q(
                        "Which flag asks the compiler for extra warnings?",
                        ["-O3", "-Wall", "-shared", "-E"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Variables, data types and sizeof",
            "PocJ5jXv8No",
            r"""## Types describe the storage

Every variable has a type, and the type decides how many bytes are reserved and
how the bits are read.

```c
int count = 3;          /* whole numbers */
char grade = 'A';       /* one character, stored as a small integer */
float ratio = 0.75f;    /* single precision */
double price = 149.99;  /* double precision, the default for literals */
unsigned int hits = 0;  /* never negative */
```

`sizeof` reports the size in bytes and is the only portable way to ask:

```c
printf("int is %zu bytes\n", sizeof(int));
```

The sizes of `int` and `long` change between platforms. `char` is always exactly
one byte. `limits.h` and `float.h` give you the minimum and maximum values for
the machine you are actually compiling on.

## Naming

A name may contain letters, digits and underscores, but cannot start with a
digit. Use lowercase words joined by underscores, and make the name say what the
value means: `reward_paise` beats `r`.""",
            quiz(
                "Types and sizes check",
                2400,
                [
                    Q(
                        "How many bytes is a `char` in C?",
                        ["Always exactly 1", "Always 2", "4", "It can be 0"],
                        0,
                    ),
                    Q(
                        "Which format specifier prints an int with printf?",
                        ["%f", "%d", "%c", "%s"],
                        1,
                    ),
                    Q(
                        "Which type should hold a price with decimals?",
                        ["int", "char", "double", "unsigned"],
                        2,
                    ),
                    Q(
                        "What does `sizeof` return?",
                        [
                            "The number of elements",
                            "A size in bytes, as size_t",
                            "A pointer",
                            "The largest value the type can hold",
                        ],
                        1,
                    ),
                    Q(
                        "What does declaring a value `unsigned` give up?",
                        ["Positive values", "Negative values", "Decimals", "Speed"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Operators, precedence and casting",
            "slzcWKWCMBg",
            r"""## Arithmetic has rules

`+ - * /` behave as you expect, with one important exception: dividing two
integers throws the fraction away.

```c
int a = 7 / 2;         /* 3, not 3.5 */
int b = 7 % 2;         /* 1, the remainder */
double c = 7 / 2.0;    /* 3.5, because one side is floating point */
```

`%` is only defined for integers. Use it for even/odd checks, wrapping a counter
into a range, and splitting time into hours and minutes.

## Precedence and casts

Multiplication binds tighter than addition, comparisons bind tighter than `&&`,
and assignment sits near the bottom. Do not memorise the whole table - add
parentheses and the intent becomes obvious to the next reader.

A cast converts a value explicitly:

```c
int total = 7, items = 2;
double average = (double) total / items;   /* convert before dividing */
```

Cast at the point of division, not after it; converting an already-truncated
`3` gives you `3.0`.""",
            quiz(
                "Operators check",
                2400,
                [
                    Q("What is `7 / 2` for two ints?", ["3", "3.5", "4", "3.0"], 0),
                    Q("What does `7 % 2` evaluate to?", ["3", "1", "0", "3.5"], 1),
                    Q(
                        "Which operator binds tighter: `*` or `+`?",
                        ["*", "+", "They are equal", "It depends on the line"],
                        0,
                    ),
                    Q("What does `(double) 7 / 2` produce?", ["3", "3.5", "4", "A compile error"], 1),
                    Q("`x += 3` means the same as:", ["x = 3", "x = x + 3", "x = 3 - x", "x++ 3"], 1),
                ],
            ),
        ),
        lesson(
            "Branching with if and switch",
            "kKJeekDKU30",
            r"""## Conditions are integers

C has no dedicated boolean type in older code: zero is false and every non-zero
value is true.

```c
if (score >= 70) {
    puts("passed");
} else if (score >= 50) {
    puts("close");
} else {
    puts("try again");
}
```

Because assignment is an expression, `if (x = 5)` compiles and is always true. It
is one of the most common typos in C; `-Wall` warns about it, which is why the
flag is worth keeping on.

## switch

`switch` compares one integer value against a list of constants:

```c
switch (command) {
    case 'q':
        quit();
        break;
    case 'h':
        help();
        break;
    default:
        puts("unknown");
}
```

Without `break`, execution falls through into the next case. That is occasionally
useful and almost always a bug. The conditional operator `cond ? a : b` is a
compact `if` for choosing between two values.""",
            quiz(
                "Branching check",
                2500,
                [
                    Q("In C, which value counts as false?", ["0", "1", "-1", "Any non-zero value"], 0),
                    Q(
                        "What happens when a case has no `break`?",
                        [
                            "A compile error",
                            "Execution falls through to the next case",
                            "The switch exits",
                            "The default case runs first",
                        ],
                        1,
                    ),
                    Q("Which operator chooses between two values?", ["?:", "&&", "||", "!!"], 0),
                    Q(
                        "`switch` can compare which types?",
                        ["Strings", "Floats", "Integer types", "Arrays"],
                        2,
                    ),
                    Q(
                        "What does `if (x = 5)` actually do?",
                        ["Compares x with 5", "Assigns 5 and is always true", "Fails to compile", "Skips the branch"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Loops: for, while and do-while",
            "RSDzvlXmQi4",
            r"""## Three loops, three shapes

Use `for` when you know how many times to repeat, `while` when a condition
decides, and `do-while` when the body must run at least once.

```c
for (int i = 0; i < 5; i++) {
    printf("%d\n", i);        /* 0 1 2 3 4 */
}

int n = 0;
while (n < 5) {
    n++;
}

int choice;
do {
    choice = read_command();
} while (choice != 'q');
```

## break and continue

`break` leaves the loop entirely; `continue` skips to the next iteration. Both
are the clean way out of a loop whose exit condition is easier to express
inside the body.

```c
for (int i = 0; i < len; i++) {
    if (items[i] == target) {
        found = 1;
        break;
    }
}
```

Off-by-one is the classic loop bug: `i <= len` reads one element past the end,
which C will happily attempt.""",
            quiz(
                "Loop check",
                2500,
                [
                    Q("Which loop always runs at least once?", ["for", "while", "do-while", "None"], 2),
                    Q(
                        "How many times does `for (int i = 0; i < 5; i++)` run?",
                        ["4", "5", "6", "0"],
                        1,
                    ),
                    Q("What does `break` do?", ["Skips one iteration", "Exits the loop", "Restarts the loop", "Exits the program"], 1),
                    Q("What does `continue` do?", ["Exits the loop", "Jumps to the next iteration", "Does nothing", "Exits the function"], 1),
                    Q(
                        "Which loop fits a repeat count you cannot predict?",
                        ["while", "for", "do-while only", "None of them"],
                        0,
                    ),
                ],
            ),
        ),
        lesson(
            "Functions, prototypes and scope",
            "PocJ5jXv8No",
            r"""## Name the work

A function is a block with a type, a name and parameters:

```c
int add(int a, int b);          /* declaration: this exists somewhere */

int add(int a, int b) {         /* definition: here is the body */
    return a + b;
}
```

The declaration is the function's promise. Put promises in a header so every
file that calls the function agrees about its shape.

C passes arguments **by value**: the function gets a copy. To let a function
change the caller's variable you pass its address, which is why `scanf` needs
`&value`.

## Scope and lifetime

A variable declared inside a block exists only in that block. A local does not
survive the return; the memory is reused by the next call. `static` inside a
function keeps one copy for the life of the program, which is useful for
counters and dangerous as a place to hide state.

Recursion needs a base case - otherwise you get a stack overflow rather than a
wrong answer, which at least fails loudly.""",
            quiz(
                "Functions and scope check",
                2600,
                [
                    Q(
                        "Which line is a function prototype?",
                        [
                            "int add(int a, int b);",
                            "int add(int a, int b) { return a + b; }",
                            "add(a, b);",
                            "#define add(a, b)",
                        ],
                        0,
                    ),
                    Q("C passes arguments by:", ["Reference", "Value", "Name", "Pointer only"], 1),
                    Q(
                        "What must a non-void function do?",
                        [
                            "Print something",
                            "Return a value on every reachable path",
                            "Be recursive",
                            "Be static",
                        ],
                        1,
                    ),
                    Q("What does every recursive function need?", ["A loop", "A base case", "A global variable", "A pointer"], 1),
                    Q(
                        "A variable declared inside a block:",
                        [
                            "Lives for the whole program",
                            "Lives until the block ends",
                            "Is allocated on the heap",
                            "Is always static",
                        ],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Arrays and C strings",
            "slzcWKWCMBg",
            r"""## Arrays are fixed-size blocks

An array is a run of values of one type, indexed from `0`, and it does not know
its own length.

```c
int scores[5] = {90, 75, 61, 88, 100};
scores[0] = 95;               /* the first element */
int sum = 0;
for (int i = 0; i < 5; i++) {
    sum += scores[i];
}
```

C does not check the index. Writing `scores[5]` touches memory that belongs to
something else, and the result is undefined behaviour - it may work, it may crash,
or it may silently corrupt a variable two lines away.

## Strings are arrays with a terminator

A C string ends with the NUL byte `'\0'`. That terminator is how every function
knows where the text stops:

```c
char name[16] = "Learnora";   /* 9 bytes used: 8 letters + '\0' */
printf("%zu\n", strlen(name)); /* 8 */
```

Reserve room for the terminator when you size a buffer, and prefer `snprintf`
and `strncpy`-style bounded copies over the unbounded versions when the input
comes from outside the program.""",
            quiz(
                "Arrays and strings check",
                2600,
                [
                    Q("What is the first index of an array?", ["0", "1", "-1", "It depends"], 0),
                    Q("What marks the end of a C string?", ["A space", "The NUL byte", "A newline", "The length prefix"], 1),
                    Q(
                        "What happens when you write past the end of an array?",
                        ["A compile error", "Undefined behaviour", "The array grows", "An exception is thrown"],
                        1,
                    ),
                    Q("Which function copies a string?", ["strlen", "strcpy", "strcmp", "strcat"], 1),
                    Q(
                        "How many bytes does `char name[10] = \"C\";` use?",
                        ["1", "2", "10", "0"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Pointers: addresses and dereferencing",
            "kKJeekDKU30",
            r"""## A pointer holds an address

`&` asks where a variable lives; `*` reads or writes through an address.

```c
int score = 10;
int *p = &score;   /* p holds the address of score */

printf("%d\n", *p);  /* 10 */
*p = 20;             /* writes 20 into score */
```

The type matters: `int *` says "the bytes at this address should be read as an
int". Get the type wrong and you reinterpret memory.

## NULL means "no object"

A pointer that does not point anywhere should be `NULL`. Dereferencing it is
undefined behaviour, usually a crash, so check before you follow it:

```c
int *p = find_score("python");
if (p != NULL) {
    printf("%d\n", *p);
}
```

Passing a pointer is how C shares data without copying it, and it is also how C
gets use-after-free bugs. Every pointer is either valid or a promise you have to
keep.""",
            quiz(
                "Pointer check",
                2700,
                [
                    Q("What does `&score` give you?", ["The value of score", "The address of score", "The size of score", "A copy of score"], 1),
                    Q("What does `*p` do?", ["Multiplies", "Reads or writes the value at p", "Gives p's address", "Allocates memory"], 1),
                    Q("Which value marks 'points at nothing'?", ["0.0", "NULL", "The empty string", "-1"], 1),
                    Q("A pointer stores:", ["A value", "An address", "A type", "A size"], 1),
                    Q("Dereferencing NULL is:", ["Zero", "Undefined behaviour", "A compile error", "A NULL result"], 1),
                ],
            ),
        ),
        lesson(
            "Pointers, arrays and function arguments",
            "RSDzvlXmQi4",
            r"""## An array is passed as a pointer

When you pass an array to a function you pass the address of its first element,
so the function edits the caller's data. The length does not travel with it -
pass it explicitly.

```c
int total(const int *values, int count) {
    int sum = 0;
    for (int i = 0; i < count; i++) {
        sum += values[i];
    }
    return sum;
}
```

`values[i]` is defined as `*(values + i)`: pointer arithmetic moves in whole
elements, not bytes. `values + 1` advances by `sizeof(int)`.

## Pointers let a function return two things

C returns one value, so results travel back through pointers:

```c
int divide(int a, int b, int *out) {
    if (b == 0) return 0;     /* failure */
    *out = a / b;
    return 1;                 /* success */
}
```

Callers check the status and read the result only when it succeeded. `const`
before the pointee says "I will read this but not change it", which is the most
useful comment in a C signature.""",
            quiz(
                "Pointers and arrays check",
                2700,
                [
                    Q(
                        "Passing an array to a function passes:",
                        ["A copy of the array", "A pointer to its first element", "Its length", "Nothing"],
                        1,
                    ),
                    Q("`values + 1` advances by:", ["1 byte", "One element", "Two bytes", "Nothing"], 1),
                    Q(
                        "Which signature can swap two ints for the caller?",
                        [
                            "void swap(int a, int b)",
                            "void swap(int *a, int *b)",
                            "void swap(int a, int *b)",
                            "void swap(*int a)",
                        ],
                        1,
                    ),
                    Q("How does `strlen` find the length?", ["It stores it", "It scans to the NUL byte", "It calls sizeof", "It reads a header"], 1),
                    Q(
                        "`const char *s` means:",
                        [
                            "The pointer cannot change",
                            "The characters cannot be changed through s",
                            "s is NULL",
                            "s is global",
                        ],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Structs, enums and typedef",
            "PocJ5jXv8No",
            r"""## Group values that belong together

A struct is a named bundle of fields. It is the closest C gets to a record:

```c
struct point {
    int x;
    int y;
};

struct point start = {0, 0};
start.x = 12;

struct point *cursor = &start;
cursor->y = 5;        /* the same as (*cursor).y */
```

`.` reads a member from a struct value, `->` reads it through a pointer. Use the
pointer form for anything large - passing a struct by value copies every field.

## Names for numbers

`enum` gives names to a set of integers, so code reads as intent:

```c
typedef enum { NEW, LEARNING, PASSED } status;
status lesson = PASSED;
```

`typedef` makes an alias: `typedef struct point point;` lets you write `point`
without repeating `struct`. It does not create a new type, it only renames one.

## Practice

Model a course with a title, a reward and a level enum, then print it with a
function that takes a `const struct course *`.""",
            quiz(
                "Structs and enums check",
                2700,
                [
                    Q(
                        "Which operator reads a member through a pointer?",
                        [".", "->", "::", "&"],
                        1,
                    ),
                    Q(
                        "Which keyword names a set of integer constants?",
                        ["struct", "enum", "union", "typedef"],
                        1,
                    ),
                    Q(
                        "What does `typedef` do?",
                        ["Creates a variable", "Makes an alias for a type", "Allocates memory", "Includes a header"],
                        1,
                    ),
                    Q(
                        "Is `struct point p; p.x = 3;` valid C?",
                        ["Yes", "No", "Only for pointers", "Only in C++"],
                        0,
                    ),
                    Q(
                        "A union stores its members:",
                        ["One after another", "At the same address", "On the heap", "Only as ints"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Dynamic memory: malloc, calloc, realloc, free",
            "slzcWKWCMBg",
            r"""## The heap, on demand

Locals live on the stack and disappear on return. When the size is only known
at run time, ask the heap:

```c
int count = 10;
int *scores = malloc(count * sizeof *scores);
if (scores == NULL) {
    return 1;                 /* out of memory */
}
scores[0] = 90;
free(scores);                 /* give it back once */
```

`malloc` returns uninitialised bytes. `calloc` returns zeroed bytes. `realloc`
grows or shrinks a block, and may move it - always assign the result to a new
pointer before overwriting the old one:

```c
int *bigger = realloc(scores, 20 * sizeof *scores);
if (bigger == NULL) { /* the old block is still yours to free */ }
scores = bigger;
```

## Rules that keep you out of trouble

Every successful allocation gets exactly one `free`. Never use memory after
freeing it, never free twice, and never free something you did not allocate.
`sizeof *ptr` is the safest way to write the size: it stays correct when the
type changes.""",
            quiz(
                "Dynamic memory check",
                2800,
                [
                    Q("Which call returns zeroed memory?", ["malloc", "calloc", "realloc", "free"], 1),
                    Q(
                        "What must every successful allocation eventually meet?",
                        ["free", "delete", "memset", "Nothing"],
                        0,
                    ),
                    Q("`realloc` can:", ["Resize a block", "Only free", "Copy strings", "Change a type"], 0),
                    Q("Forgetting to free memory causes:", ["A leak", "A compile error", "A type error", "A syntax error"], 0),
                    Q(
                        "What should you check every time malloc returns?",
                        ["The size", "Whether it is NULL", "The alignment", "The type"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Files: reading and writing",
            "kKJeekDKU30",
            r"""## A FILE handle

`fopen` opens a stream and returns a `FILE *`, or `NULL` when it fails:

```c
FILE *out = fopen("report.txt", "w");
if (out == NULL) {
    perror("report.txt");   /* explains the failure */
    return 1;
}
fprintf(out, "reward,%d\n", 2000);
fclose(out);
```

Modes you will use: `"r"` read, `"w"` write and truncate, `"a"` append, plus a
`b` suffix for binary. Add `+` if you need both directions on one handle.

## Reading line by line

`fgets` reads at most the size you give it, which makes it safe on untrusted
input:

```c
char line[256];
while (fgets(line, sizeof line, in) != NULL) {
    printf("%s", line);
}
fclose(in);
```

Check `fclose`: buffered writes can fail on the final flush. A program that
ignores the result can silently lose the last block of output.""",
            quiz(
                "File handling check",
                2800,
                [
                    Q("Which mode truncates an existing file?", ["\"r\"", "\"w\"", "\"a\"", "\"rb\""], 1),
                    Q(
                        "Which reads a line with a size limit?",
                        ["fgets", "gets", "getc", "fscanf"],
                        0,
                    ),
                    Q("What must you do with an open FILE*?", ["Close it", "Free it", "Delete it", "Lock it"], 0),
                    Q(
                        "Which call writes a formatted line to a file?",
                        ["printf", "fprintf", "sprintf", "puts"],
                        1,
                    ),
                    Q("What does fopen return on failure?", ["0", "NULL", "-1", "An empty string"], 1),
                ],
            ),
        ),
        lesson(
            "Preprocessor, headers and the build",
            "RSDzvlXmQi4",
            r"""## Before the compiler

The preprocessor runs first. `#include` pastes a file in, `#define` substitutes
text, and `#if` can leave whole blocks out.

```c
#include "course.h"

#define MAX_TOPICS 64                 /* a constant */
#define SQUARE(x) ((x) * (x))         /* a macro: parenthesise every part */
```

A macro is text substitution, not a function: it has no type checking, and
`SQUARE(i++)` increments twice. For constants prefer `static const int`; for
small helpers prefer a real function and let the compiler inline it.

## Headers and guards

Put declarations in a header and definitions in a `.c` file:

```c
#ifndef COURSE_H
#define COURSE_H

int total_reward(const struct course *c);

#endif
```

The guard stops the same declarations being pasted twice. `#pragma once` does
the same job on every compiler you are likely to meet.

## One build command

```bash
gcc -std=c17 -Wall -Wextra -g -c course.c -o course.o
gcc -std=c17 -Wall -Wextra -g main.c course.o -o learnora
```

Compile with warnings on from the first day; cleaning them up later is far more
work than never creating them.""",
            quiz(
                "Preprocessor and build check",
                2800,
                [
                    Q("Which directive includes a header?", ["#define", "#include", "#ifdef", "#pragma"], 1),
                    Q(
                        "Why do headers carry include guards?",
                        [
                            "They make the build faster",
                            "They stop duplicate declarations in one translation unit",
                            "They reserve memory",
                            "They link libraries",
                        ],
                        1,
                    ),
                    Q("What does `-Wall` do?", ["Links libraries", "Enables common warnings", "Builds a release", "Starts a debugger"], 1),
                    Q("A macro is:", ["Type checked", "Textual substitution", "A function", "A file"], 1),
                    Q(
                        "To call a function defined in another .c file you need:",
                        ["A copy of it", "Its declaration in a header", "A macro", "An enum"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "The standard library tour",
            "PocJ5jXv8No",
            r"""## Know what already exists

Most C is written against a handful of headers. Learn these and you stop
re-implementing them badly.

| Header | What it gives you |
| --- | --- |
| `string.h` | `strlen`, `strcmp`, `strchr`, `memcpy`, `memset` |
| `stdlib.h` | `malloc`, `free`, `atoi`, `abs`, `qsort`, `exit` |
| `stdio.h` | `printf`, `fopen`, `fgets`, `sscanf` |
| `ctype.h` | `isdigit`, `isalpha`, `isspace`, `toupper` |
| `math.h` | `sqrt`, `pow`, `floor` (link with `-lm`) |
| `assert.h` | `assert`, which aborts when a promise breaks |

## Sorting without writing a sort

```c
int by_reward(const void *a, const void *b) {
    const struct course *left = a;
    const struct course *right = b;
    return (left->reward > right->reward) - (left->reward < right->reward);
}

qsort(courses, count, sizeof courses[0], by_reward);
```

The comparator returns a negative, zero or positive number - never the raw
difference, which overflows for large values.

## Checked assumptions

`assert(count > 0)` documents an invariant and crashes early in a debug build.
Compiled with `-DNDEBUG` the call disappears, so never put work with side
effects inside it.""",
            quiz(
                "Standard library check",
                2900,
                [
                    Q("Which header declares malloc?", ["stdio.h", "stdlib.h", "string.h", "math.h"], 1),
                    Q("Which function sorts with a comparator?", ["sort", "qsort", "bsearch", "sortby"], 1),
                    Q(
                        "Which call tests a character for digits?",
                        ["isalpha", "isdigit", "isspace", "toupper"],
                        1,
                    ),
                    Q("`memcpy` copies:", ["Strings only", "A block of bytes", "Files", "Ints only"], 1),
                    Q("Which flag links the maths library?", ["-lm", "-lpthread", "-lc", "-lmath"], 0),
                ],
            ),
        ),
        lesson(
            "Bitwise operators and flags",
            "slzcWKWCMBg",
            r"""## Bits are yours to address

C exposes the bits of an integer through six operators:

| Operator | Meaning |
| --- | --- |
| `&` | and |
| `\|` | or |
| `^` | exclusive or |
| `~` | not |
| `<<` | shift left |
| `>>` | shift right |

They are how a program packs several on/off facts into one integer, which is
what file permissions, network headers and hardware registers all do.

## Set, clear, toggle, test

```c
#define READ  (1 << 0)   /* 0b0001 */
#define WRITE (1 << 1)   /* 0b0010 */
#define ADMIN (1 << 2)   /* 0b0100 */

unsigned flags = 0;
flags |= READ;              /* set */
flags &= ~WRITE;            /* clear */
flags ^= ADMIN;             /* toggle */
if (flags & READ) { /* test */ }
```

Note the parentheses in `(flags & READ) != 0`: `==` binds tighter than `&`, so
without them you compare the mask with zero and the branch is wrong.

## Shifting carefully

`x << 1` doubles an unsigned value. Shifting by the width of the type, or left
into the sign bit, is undefined; shifting a negative value right is
implementation-defined. Use `unsigned` for bit work and the rules stay boring.""",
            quiz(
                "Bitwise check",
                2900,
                [
                    Q("Which expression sets a bit?", ["x | mask", "x & mask", "x ^ ~mask", "x >> mask"], 0),
                    Q("Which expression tests a bit correctly?", ["x & mask", "(x & mask) != 0", "x | mask", "x ^ mask"], 1),
                    Q("What does `x ^ mask` do to a set bit?", ["Clears it", "Toggles it", "Doubles it", "Leaves it"], 1),
                    Q("`1 << 3` equals:", ["3", "8", "6", "9"], 1),
                    Q(
                        "Shifting a negative signed value right is:",
                        ["Well defined", "Implementation-defined", "A compile error", "Identical everywhere"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Data structures: lists, stacks and queues",
            "kKJeekDKU30",
            r"""## A linked list

When the count is unknown and insertion is frequent, a chain of nodes beats an
array:

```c
struct node {
    int value;
    struct node *next;
};

struct node *push(struct node *head, int value) {
    struct node *fresh = malloc(sizeof *fresh);
    if (fresh == NULL) return head;
    fresh->value = value;
    fresh->next = head;
    return fresh;
}
```

Traversal walks the chain; the walk ends at `NULL`:

```c
for (struct node *it = head; it != NULL; it = it->next) {
    printf("%d\n", it->value);
}
```

Freeing must also walk, and must save `next` before freeing the node you are
standing on.

## Stacks and queues

A stack is last-in-first-out: push and pop from the same end. A queue is
first-in-first-out: add at the back, remove from the front. Both can be an array
plus an index, which is faster and uses less memory than a list - the ring
buffer that wraps the index back to zero is the standard version.

Inserting at the head of a list is O(1); finding the nth element is O(n). An
array indexes in O(1) but inserting in the middle costs a copy.""",
            quiz(
                "Data structures check",
                3000,
                [
                    Q("A linked list node needs:", ["Only data", "Data plus a pointer to the next node", "An index", "A hash"], 1),
                    Q("Inserting at the head of a singly linked list is:", ["O(n)", "O(1)", "O(log n)", "O(n^2)"], 1),
                    Q("A stack is:", ["FIFO", "LIFO", "Sorted", "Random access"], 1),
                    Q("A queue is:", ["LIFO", "FIFO", "Sorted", "Always an array"], 1),
                    Q("Why free every list node?", ["To keep the order", "To avoid a leak", "To sort it", "To resize it"], 1),
                ],
            ),
        ),
        lesson(
            "Debugging, sanitisers and undefined behaviour",
            "RSDzvlXmQi4",
            r"""## Build something you can inspect

Two flags turn a cryptic crash into a useful report:

```bash
gcc -std=c17 -Wall -Wextra -g \\
    -fsanitize=address,undefined \\
    main.c course.c -o learnora
./learnora
```

`-g` keeps the names and line numbers. AddressSanitizer catches out-of-bounds
access, use-after-free and leaks; UndefinedBehaviorSanitizer catches signed
overflow, misaligned loads and invalid shifts.

## gdb in five commands

```bash
gdb ./learnora
(gdb) run
(gdb) break total_reward
(gdb) print count
(gdb) backtrace
```

Run, set a breakpoint, inspect a variable, read the call stack. That is enough
to find most problems, and `valgrind --leak-check=full ./learnora` covers the
memory leaks sanitisers report less clearly.

## Undefined behaviour is not "it works"

Reading an uninitialised variable, indexing out of bounds, using freed memory,
and overflowing a signed int are all undefined. The program may print the right
answer today and something else after a compiler upgrade. Treat every warning as
a bug report from the future.""",
            quiz(
                "Debugging check",
                3000,
                [
                    Q("Which flag keeps debug symbols?", ["-g", "-O2", "-s", "-DNDEBUG"], 0),
                    Q(
                        "What does AddressSanitizer find?",
                        ["Slow loops", "Out-of-bounds access and use-after-free", "Syntax errors", "Missing headers"],
                        1,
                    ),
                    Q("Which gdb command prints a variable?", ["show", "print", "cat", "display"], 1),
                    Q(
                        "A buffer overflow is caught by:",
                        ["The compiler, always", "Sanitisers and careful code", "The operating system, always", "Nothing, ever"],
                        1,
                    ),
                    Q(
                        "Undefined behaviour means:",
                        ["A compile error", "Anything may happen", "An exception is thrown", "The program exits cleanly"],
                        1,
                    ),
                ],
            ),
        ),
        lesson(
            "Capstone: a small command-line project",
            "PocJ5jXv8No",
            r"""## Put it together

A finished C program is more than a `main`. Give it a shape:

```
learnora/
  include/report.h
  src/main.c
  src/report.c
  Makefile
```

The header declares what the rest of the program may call; each `.c` file owns
one job; the Makefile rebuilds only what changed.

## Arguments and exit codes

```c
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: learnora <file>\n");
        return 2;              /* usage error */
    }
    FILE *in = fopen(argv[1], "r");
    if (in == NULL) {
        perror(argv[1]);
        return 1;              /* runtime failure */
    }
    /* ... read, compute, free, fclose ... */
    return 0;
}
```

`argv[0]` is the program name, so the first real argument is `argv[1]`. Exit `0`
for success, a non-zero code for each distinct failure: scripts and CI read them.

## The habit that matters

For every allocation write its `free` on the same day; check every pointer before
following it; keep `-Wall -Wextra -g` and the sanitisers in your build. The
language will not stop you, so the build has to.""",
            quiz(
                "Capstone check",
                3200,
                [
                    Q("What is `argv[0]`?", ["The first argument", "The program name", "The argument count", "NULL"], 1),
                    Q("`argc` counts:", ["Arguments only", "The program name plus arguments", "Characters", "Files"], 1),
                    Q("Which exit code signals failure?", ["0", "A non-zero value", "Only -1", "Only 255"], 1),
                    Q("Every allocation should be paired with:", ["Another allocation", "free", "malloc", "memset"], 1),
                    Q(
                        "Why split code into headers and source files?",
                        [
                            "Only for speed",
                            "To declare interfaces once and share them",
                            "To hide memory",
                            "To avoid linking",
                        ],
                        1,
                    ),
                ],
            ),
        ),
    ],
}
