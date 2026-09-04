"""
sandbox.py

Safely executes player-submitted Python code for the CodeBreak
coding challenges.

This is NOT a general-purpose Python sandbox - it does not attempt
to defend against a maliciously creative attacker escaping to full
system access. It exists to give code challenges written for a game
a reasonably safe execution environment: no filesystem access, no
imports, no network, and no infinite loops locking up the game.

Responsibilities
----------------
- Reject dangerous code before running it (imports, exec/eval,
  file access, dunder attribute tricks).
- Run the remaining code with a restricted set of builtins.
- Capture everything printed to stdout.
- Stop code that runs too long (e.g. an infinite loop).
- Report back what happened in a single, simple result object.

This module does NOT decide whether a challenge was solved
correctly - that's ChallengeManager's job. This only answers
"did the code run, and what did it print/error?"
"""

import ast
import io
import sys
import time
import contextlib


class SandboxError(Exception):
    """Raised when submitted code fails the safety check before running."""


class SandboxTimeout(Exception):
    """Raised internally when user code runs past the allowed time limit."""


# ==============================================================
# Static Safety Check
# ==============================================================

# Names that must never be reachable, even indirectly, because they
# can be used to break out of the sandbox or touch the real system.
FORBIDDEN_NAMES = {
    "__import__", "eval", "exec", "compile", "open",
    "globals", "locals", "vars",
    "exit", "quit", "help", "breakpoint",
    "getattr", "setattr", "delattr",
}


class SafetyVisitor(ast.NodeVisitor):
    """
    Walks the parsed code BEFORE execution and raises SandboxError
    the moment it sees something disallowed. Nothing here runs the
    user's code - it only inspects the syntax tree.
    """

    def visit_Import(self, node):
        raise SandboxError(
            "Import statements aren't allowed in the code editor."
        )

    def visit_ImportFrom(self, node):
        raise SandboxError(
            "Import statements aren't allowed in the code editor."
        )

    def visit_Name(self, node):
        if node.id in FORBIDDEN_NAMES:
            raise SandboxError(
                f"'{node.id}' isn't allowed in the code editor."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Blocks dunder attribute access (e.g. "().__class__" or
        # "x.__globals__"), which is the classic way to climb out
        # of a restricted-builtins sandbox back to real Python.
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise SandboxError(
                "Double-underscore attributes aren't allowed."
            )
        self.generic_visit(node)


def check_code_is_safe(code):
    """
    Parses `code` and raises SandboxError if it contains anything
    disallowed. A plain SyntaxError from a bad parse is allowed to
    propagate uncaught - the caller treats that as a normal "your
    code has a syntax error" result, not a safety issue.
    """

    tree = ast.parse(code)
    SafetyVisitor().visit(tree)


# ==============================================================
# Restricted Execution Environment
# ==============================================================

# Only these builtins are reachable from inside user code. Anything
# not listed here (open, __import__, eval, exec, etc.) simply does
# not exist as far as the executed code is concerned.
SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "isinstance": isinstance,
    "type": type,
    "any": any,
    "all": all,
    "True": True,
    "False": False,
    "None": None,
    # Common exception types, so user code can raise/catch them
    # normally (e.g. "except ValueError:") without needing imports.
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "IndexError": IndexError,
    "KeyError": KeyError,
    "ZeroDivisionError": ZeroDivisionError,
    "StopIteration": StopIteration,
    "RuntimeError": RuntimeError,
    "ArithmeticError": ArithmeticError,
    "AttributeError": AttributeError,
    "NameError": NameError,
    "EOFError": EOFError,
}


def _make_timeout_tracer(deadline):
    """
    Returns a trace function that raises SandboxTimeout once the
    deadline has passed. Passed to sys.settrace() so it gets called
    on every line the user's code executes - including every
    iteration of a loop - which is what lets this catch something
    like "while True: pass" without needing a separate thread or
    process to forcibly kill.
    """

    def tracer(frame, event, arg):
        if time.time() > deadline:
            raise SandboxTimeout("Code took too long to run.")
        return tracer

    return tracer


def run_user_code(
    code,
    timeout=3.0,
    input_values=None
):
    """
    Runs `code` in a restricted environment and returns a result
    dict. Never raises - all failure modes (syntax errors, unsafe
    code, runtime errors, timeouts) are reported back in the dict
    instead, so the caller can always safely display the result.

    Returns
    -------
    dict with keys:
        success : bool
            True only if the code ran start-to-finish with no error.
        output : str
            Everything the code printed via print().
        error : str or None
            A human-readable error message, or None on success.
        globals : dict or None
            The variables the code ended up with (only present on
            success). Useful later for ChallengeManager to check,
            e.g., "does 'age' equal 18?".
    """

    # ---- Empty code: nothing to run ----
    stripped = code.strip()
    if not stripped:
        return {
            "success": False,
            "output": "",
            "error": "There's no code to run yet.",
        }

    # ---- Syntax check ----
    try:
        ast.parse(code)
    except SyntaxError as error:
        return {
            "success": False,
            "output": "",
            "error": f"Syntax error on line {error.lineno}: {error.msg}",
        }

    # ---- Safety check (imports, dunders, dangerous builtins) ----
    try:
        check_code_is_safe(code)
    except SandboxError as error:
        return {
            "success": False,
            "output": "",
            "error": str(error),
        }

    # --------------------------------------------------------------
    # Controlled input()
    # --------------------------------------------------------------

    # Every execution gets its own fresh set of test inputs.
    input_queue = iter(
        str(value)
        for value in (input_values or [])
    )


    def safe_input(prompt=""):
        """
        Replacement for Python's real input().

        Instead of reading from the computer terminal, values are
        supplied by the current coding challenge.
        """

        try:
            value = next(input_queue)

        except StopIteration:
            raise EOFError(
                "The program requested more input values "
                "than the challenge provided."
            )

        # Show what the player would normally see in a terminal.
        print(
            f"{prompt}{value}"
        )

        return value


    # Make a copy because safe_input belongs only to this execution.
    sandbox_builtins = dict(
        SAFE_BUILTINS
    )

    sandbox_builtins[
        "input"
    ] = safe_input


    sandbox_globals = {
        "__builtins__": sandbox_builtins
    }

    output_buffer = io.StringIO()

    deadline = time.time() + timeout
    tracer = _make_timeout_tracer(deadline)

    try:
        sys.settrace(tracer)

        with contextlib.redirect_stdout(output_buffer):
            exec(compile(code, "<user_code>", "exec"), sandbox_globals)

    except SandboxTimeout as error:
        return {
            "success": False,
            "output": output_buffer.getvalue(),
            "error": str(error),
        }

    except Exception as error:
        # Any runtime error from the user's own code (ValueError,
        # ZeroDivisionError, a typo causing NameError, etc.) lands
        # here and is reported back instead of crashing the game.
        return {
            "success": False,
            "output": output_buffer.getvalue(),
            "error": f"{type(error).__name__}: {error}",
        }

    finally:
        sys.settrace(None)

    user_variables = {
        name: value
        for name, value in sandbox_globals.items()
        if not name.startswith("__")
    }

    return {
        "success": True,
        "output": output_buffer.getvalue(),
        "error": None,
        "globals": sandbox_globals,
        "variables": user_variables,
    }