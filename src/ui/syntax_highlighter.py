"""
syntax_highlighter.py

Turns lines of Python source code into (text, color) segments so
the editor can render each part of a line in a different color.

This is a lightweight, character-by-character scanner - not a full
Python parser. That's intentional: code typed live in the editor is
very often incomplete or momentarily invalid (mid-statement, a
missing closing quote, etc.), and a real parser would choke on that.

It DOES track one piece of state across lines: whether a triple-
quoted string ('''...''' or \"\"\"...\"\"\") opened on an earlier line
and hasn't been closed yet. Without that, every line after an open
multi-line string would be colored as if nothing were happening,
since each line would be analyzed with no memory of what came before.
"""

from src.ui.editor_theme import (
    TEXT_COLOR,
    SYNTAX_KEYWORD_COLOR,
    SYNTAX_BUILTIN_COLOR,
    SYNTAX_STRING_COLOR,
    SYNTAX_NUMBER_COLOR,
    SYNTAX_COMMENT_COLOR,
    SYNTAX_FUNCTION_COLOR,
    SYNTAX_SELF_COLOR,
    SYNTAX_DECORATOR_COLOR,
)

KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else",
    "except", "finally", "for", "from", "global", "if", "import",
    "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
    "return", "try", "while", "with", "yield",
}

BUILTINS = {
    "print", "len", "range", "str", "int", "float", "bool", "list",
    "dict", "set", "tuple", "input", "type", "isinstance", "enumerate",
    "zip", "map", "filter", "sorted", "reversed", "sum", "min", "max",
    "abs", "round", "open", "super", "object", "any", "all", "id",
    "getattr", "setattr", "hasattr", "issubclass", "iter", "next",
}

SELF_NAMES = {"self", "cls"}

TRIPLE_QUOTES = ("'''", '"""')


def _find_string_end(text, delimiter):
    """
    Searches `text` for the end of a string opened by `delimiter`
    (one of "'", '"', "'''", '\"\"\"'), honoring backslash escapes.

    Returns the index in `text` immediately AFTER the closing
    delimiter, or None if the string never closes within `text`.
    """

    i = 0
    n = len(text)
    delimiter_length = len(delimiter)

    while i < n:

        if text[i] == "\\":
            # Skip the escaped character too, so an escaped quote
            # (e.g. \" inside a "..." string) is never mistaken
            # for the closing delimiter.
            i += 2
            continue

        if text[i:i + delimiter_length] == delimiter:
            return i + delimiter_length

        i += 1

    return None


def highlight_line(line, in_triple_string=None):
    """
    Breaks one line into (text, color) segments covering the ENTIRE
    line, so blitting the segments back-to-back reproduces the line
    exactly - just in multiple colors.

    Parameters
    ----------
    line : str
        The single line of code to highlight.

    in_triple_string : str or None
        The triple-quote delimiter ("'''" or '\"\"\"') that was left
        OPEN by a previous line, or None if we're starting fresh.
        Pass the value returned as `new_state` from the call on the
        previous line to carry multi-line strings across lines.

    Returns
    -------
    (segments, new_state)
        segments  : list of (text, color) tuples for this line.
        new_state : the triple-quote delimiter still open at the
                    END of this line, or None if nothing is open.
                    Pass this into the call for the NEXT line.
    """

    segments = []
    i = 0
    n = len(line)
    state = in_triple_string

    # The most recently emitted identifier/keyword, tracked so that
    # "def my_func" or "class MyClass" can color my_func/MyClass as
    # a function/class name. Whitespace between the two doesn't
    # clear this; only hitting a non-name token does.
    previous_name = None

    # Consecutive default-colored characters (whitespace, operators,
    # punctuation) are buffered here and flushed as one segment,
    # instead of emitting a separate segment per character.
    default_start = None

    def flush_default(end):
        nonlocal default_start
        if default_start is not None and end > default_start:
            segments.append((line[default_start:end], TEXT_COLOR))
        default_start = None

    # ------------------------------------------------------------
    # Continuing a multi-line triple-quoted string from above
    # ------------------------------------------------------------

    if state is not None:

        end = _find_string_end(line, state)

        if end is None:
            # Still not closed - the ENTIRE line is inside the
            # string, and the next line inherits the same state.
            segments.append((line, SYNTAX_STRING_COLOR))
            return segments, state

        # The string closes partway through this line; color up to
        # the closing delimiter, then keep scanning normally from
        # there (there may be more code on the same line).
        segments.append((line[:end], SYNTAX_STRING_COLOR))
        i = end
        state = None

    # ------------------------------------------------------------
    # Normal scan
    # ------------------------------------------------------------

    while i < n:

        ch = line[i]

        # ---- Comment: rest of the line, nothing more to scan ----
        if ch == "#":
            flush_default(i)
            segments.append((line[i:], SYNTAX_COMMENT_COLOR))
            i = n
            break

        # ---- Triple-quoted string ----
        if line[i:i + 3] in TRIPLE_QUOTES:
            flush_default(i)

            delimiter = line[i:i + 3]
            end_in_rest = _find_string_end(line[i + 3:], delimiter)

            if end_in_rest is None:
                # Opens here but doesn't close on this line - the
                # rest of the line is string, and this state carries
                # into the next line via the return value.
                segments.append((line[i:], SYNTAX_STRING_COLOR))
                state = delimiter
                i = n
                break

            full_end = i + 3 + end_in_rest
            segments.append((line[i:full_end], SYNTAX_STRING_COLOR))
            i = full_end
            previous_name = None
            continue

        # ---- Single/double-quoted string (not triple) ----
        if ch in ("'", '"'):
            flush_default(i)

            end_in_rest = _find_string_end(line[i + 1:], ch)

            if end_in_rest is None:
                # Unterminated - a regular quote can't validly span
                # lines, so color to end of line but don't carry
                # any state forward.
                segments.append((line[i:], SYNTAX_STRING_COLOR))
                i = n
                break

            full_end = i + 1 + end_in_rest
            segments.append((line[i:full_end], SYNTAX_STRING_COLOR))
            i = full_end
            previous_name = None
            continue

        # ---- Decorator (@staticmethod, @property, etc.) ----
        if ch == "@" and i + 1 < n and (line[i + 1].isalpha() or line[i + 1] == "_"):
            flush_default(i)

            j = i + 1
            while j < n and (line[j].isalnum() or line[j] in "_."):
                j += 1

            segments.append((line[i:j], SYNTAX_DECORATOR_COLOR))
            i = j
            previous_name = None
            continue

        # ---- Number ----
        if ch.isdigit():
            flush_default(i)

            j = i
            while j < n and (line[j].isdigit() or line[j] == "."):
                j += 1

            segments.append((line[i:j], SYNTAX_NUMBER_COLOR))
            i = j
            previous_name = None
            continue

        # ---- Identifier / keyword ----
        if ch.isalpha() or ch == "_":
            flush_default(i)

            j = i
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1

            word = line[i:j]

            if word in KEYWORDS:
                color = SYNTAX_KEYWORD_COLOR
            elif word in SELF_NAMES:
                color = SYNTAX_SELF_COLOR
            elif previous_name in ("def", "class"):
                color = SYNTAX_FUNCTION_COLOR
            elif word in BUILTINS:
                color = SYNTAX_BUILTIN_COLOR
            else:
                color = TEXT_COLOR

            segments.append((word, color))
            previous_name = word
            i = j
            continue

        # ---- Default: whitespace, operators, punctuation ----
        if default_start is None:
            default_start = i
        i += 1

    flush_default(n)

    if not segments:
        segments.append(("", TEXT_COLOR))

    return segments, state


def compute_line_states(lines):
    """
    Walks every line in the buffer from the very start and returns
    a list (same length as `lines`) where entry i is the triple-
    quote state in effect at the START of line i - i.e. whatever a
    line above may have left open.

    This has to scan from line 0 every time because a multi-line
    string can open far above whatever is currently visible on
    screen; there's no way to know a visible line is "inside" a
    string without walking through everything above it first.
    """

    states = []
    state = None

    for line in lines:
        states.append(state)
        _, state = highlight_line(line, state)

    return states