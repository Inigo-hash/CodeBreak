"""
practice_templates.py

Randomized Code Practice problems for all Stage 1 topics.

There are five authored templates per topic. Each template generates
fresh values/text whenever it is selected, while keeping the challenge
dictionary compatible with the existing CodeBreak validators.

Used with PracticeManager's shuffle-bag system.
"""

import random


# =========================================================
# Template IDs
# =========================================================

PRACTICE_TEMPLATE_IDS = {
    "python_syntax_basics": [
        "python_syntax_a",
        "python_syntax_b",
        "python_syntax_c",
        "python_syntax_d",
        "python_syntax_e",
    ],
    "variables": [
        "variables_a",
        "variables_b",
        "variables_c",
        "variables_d",
        "variables_e",
    ],
    "data_types": [
        "data_types_a",
        "data_types_b",
        "data_types_c",
        "data_types_d",
        "data_types_e",
    ],
    "type_casting": [
        "type_casting_a",
        "type_casting_b",
        "type_casting_c",
        "type_casting_d",
        "type_casting_e",
    ],
    "input_lesson": [
        "input_a",
        "input_b",
        "input_c",
        "input_d",
        "input_e",
    ],
    "formatted_output": [
        "formatted_output_a",
        "formatted_output_b",
        "formatted_output_c",
        "formatted_output_d",
        "formatted_output_e",
    ],
    "operators_lesson": [
        "operators_a",
        "operators_b",
        "operators_c",
        "operators_d",
        "operators_e",
    ],
    "strings_lesson": [
        "strings_a",
        "strings_b",
        "strings_c",
        "strings_d",
        "strings_e",
    ],
    "control_flow_lesson": [
        "control_flow_a",
        "control_flow_b",
        "control_flow_c",
        "control_flow_d",
        "control_flow_e",
    ],
}


# =========================================================
# Shared helpers
# =========================================================

def get_topic_template_ids(topic_id):
    """Return the five template IDs for one topic."""
    return list(PRACTICE_TEMPLATE_IDS.get(topic_id, []))


def _challenge(
    template_id,
    title,
    challenge_type,
    problem,
    objective,
    expected,
    *,
    hints=None,
    runtime_expected=None,
    test_inputs=None,
    hidden_tests=None,
):
    """Build one challenge dictionary in the game's existing format."""

    data = {
        "id": f"practice_{template_id}",
        "practice_template_id": template_id,
        "title": title,
        "difficulty": "Practice",
        "type": challenge_type,
        "problem": problem,
        "objective": objective,
        "requirements": [],
        "expected": expected,
    }

    if hints is not None:
        data["hints"] = hints

    if runtime_expected is not None:
        data["runtime_expected"] = runtime_expected

    if test_inputs is not None:
        data["test_inputs"] = test_inputs

    if hidden_tests is not None:
        data["hidden_tests"] = hidden_tests

    return data


def generate_practice_challenge(template_id):
    """
    Generate a fresh randomized challenge for a template ID.

    Returns None when the template ID does not exist.
    """

    builder = _TEMPLATE_BUILDERS.get(template_id)

    if builder is None:
        return None

    return builder()


# =========================================================
# Python Syntax Basics - print()
# =========================================================

def _python_syntax_a():
    place = random.choice(["Island", "Stonebrook", "Driftwood", "Clearing"])
    message = f"Entering {place}!"

    return _challenge(
        "python_syntax_a",
        "Python Syntax Practice",
        "print",
        f'Use print() to display exactly:\n\n{message}',
        f'Display "{message}" using print().',
        {"value": message},
        hints=[
            "Use Python's print() function.",
            "Put the message inside quotation marks.",
            f'The text must be exactly: {message}',
            f'Use this shape: print("{message}")',
        ],
    )


def _python_syntax_b():
    number = random.randint(2, 9)
    message = f"Stage {number} ready"

    return _challenge(
        "python_syntax_b",
        "Python Syntax Practice",
        "print",
        f'Print this exact message:\n\n{message}',
        "Use one print() call with the exact required text.",
        {"value": message},
        hints=[
            "You only need one line of Python.",
            "Use print() with a string.",
            f'Keep the number {number} inside the quotation marks too.',
            f'Use: print("{message}")',
        ],
    )


def _python_syntax_c():
    creature = random.choice(["Kapre", "Duwende", "Tikbalang", "Aswang"])
    message = f"{creature} spotted!"

    return _challenge(
        "python_syntax_c",
        "Python Syntax Practice",
        "print",
        f'Use print() to show:\n\n{message}',
        "Practice correct print() syntax.",
        {"value": message},
        hints=[
            "Start with print(",
            "The message should be a string.",
            "Remember the closing quote and parenthesis.",
            f'Correct shape: print("{message}")',
        ],
    )


def _python_syntax_d():
    item = random.choice(["Key", "Potion", "Map", "Sword"])
    message = f"{item} collected"

    return _challenge(
        "python_syntax_d",
        "Python Syntax Practice",
        "print",
        f'Display exactly:\n\n{message}',
        "Use print() correctly with a text value.",
        {"value": message},
        hints=[
            "Use print() rather than creating a variable.",
            "Place the text between quotes.",
            "Capitalization matters.",
            f'Use: print("{message}")',
        ],
    )


def _python_syntax_e():
    action = random.choice(["Explore", "Search", "Continue", "Escape"])
    message = f"{action} the area."

    return _challenge(
        "python_syntax_e",
        "Python Syntax Practice",
        "print",
        f'Write one print() statement that displays:\n\n{message}',
        "Practice a complete Python function call.",
        {"value": message},
        hints=[
            "The function name is print.",
            "Give print() one string argument.",
            "Do not remove the period from the message.",
            f'Use: print("{message}")',
        ],
    )


# =========================================================
# Variables
# =========================================================

def _variable_problem(template_id, variable_name, value, description):
    return _challenge(
        template_id,
        "Variables Practice",
        "variable",
        (
            f"Create a variable named {variable_name}\n"
            f"and assign it the value {repr(value)}.\n\n"
            f"{description}"
        ),
        f"Create {variable_name} with the correct value.",
        {
            "name": variable_name,
            "value": value,
        },
        hints=[
            f"The variable name must be {variable_name}.",
            "Use the = assignment operator.",
            f"The required value is {repr(value)}.",
            f"Use this shape: {variable_name} = {repr(value)}",
        ],
    )


def _variables_a():
    return _variable_problem(
        "variables_a",
        "health",
        random.randint(50, 100),
        "This represents the explorer's current health.",
    )


def _variables_b():
    return _variable_problem(
        "variables_b",
        "coins",
        random.randint(3, 25),
        "Store the number of coins collected.",
    )


def _variables_c():
    return _variable_problem(
        "variables_c",
        "player_name",
        random.choice(["Alex", "Mika", "Luna", "Kai", "Rin"]),
        "Store the explorer's name as text.",
    )


def _variables_d():
    return _variable_problem(
        "variables_d",
        "speed",
        random.randint(2, 8),
        "Store the player's movement speed.",
    )


def _variables_e():
    return _variable_problem(
        "variables_e",
        "has_map",
        random.choice([True, False]),
        "Store whether the player currently has a map.",
    )


# =========================================================
# Data Types
# =========================================================

def _data_types_challenge(
    template_id,
    int_name,
    int_value,
    float_name,
    float_value,
    str_name,
    str_value,
    bool_name,
    bool_value,
):
    return _challenge(
        template_id,
        "Data Types Practice",
        "data_type",
        (
            "Create these four variables using the correct data types:\n\n"
            f"{int_name} = {repr(int_value)}\n"
            f"{float_name} = {repr(float_value)}\n"
            f"{str_name} = {repr(str_value)}\n"
            f"{bool_name} = {repr(bool_value)}"
        ),
        "Create one int, float, string, and boolean with the required values.",
        {
            int_name: {"type": "int", "value": int_value},
            float_name: {"type": "float", "value": float_value},
            str_name: {"type": "str", "value": str_value},
            bool_name: {"type": "bool", "value": bool_value},
        },
        hints=[
            "An int is a whole number.",
            "A float contains a decimal point.",
            "Strings use quotation marks.",
            "Boolean values are written as True or False.",
        ],
    )


def _data_types_a():
    return _data_types_challenge(
        "data_types_a",
        "lives", random.randint(2, 6),
        "jump_power", round(random.uniform(1.2, 3.8), 1),
        "hero", random.choice(["Alex", "Mika", "Luna"]),
        "is_alive", True,
    )


def _data_types_b():
    return _data_types_challenge(
        "data_types_b",
        "keys", random.randint(1, 8),
        "distance", round(random.uniform(2.5, 9.5), 1),
        "area", random.choice(["Forest", "Ruins", "Beach"]),
        "door_open", random.choice([True, False]),
    )


def _data_types_c():
    return _data_types_challenge(
        "data_types_c",
        "enemies", random.randint(2, 7),
        "damage", round(random.uniform(4.5, 12.5), 1),
        "weapon", random.choice(["Sword", "Spear", "Bow"]),
        "equipped", True,
    )


def _data_types_d():
    return _data_types_challenge(
        "data_types_d",
        "potions", random.randint(1, 5),
        "energy", round(random.uniform(10.5, 40.5), 1),
        "zone", random.choice(["Clearing", "Hollow", "Crossing"]),
        "safe", random.choice([True, False]),
    )


def _data_types_e():
    return _data_types_challenge(
        "data_types_e",
        "score", random.randint(20, 99),
        "time_left", round(random.uniform(15.0, 90.0), 1),
        "rank", random.choice(["Bronze", "Silver", "Gold"]),
        "completed", random.choice([True, False]),
    )


# =========================================================
# Type Casting
# =========================================================

def _casting_challenge(
    template_id,
    source,
    source_value,
    target,
    function_name,
):
    result_value = {
        "int": int,
        "float": float,
        "str": str,
    }[function_name](source_value)

    return _challenge(
        template_id,
        "Type Casting Practice",
        "type_casting",
        (
            f"Create:\n\n{source} = {repr(source_value)}\n\n"
            f"Then convert {source} using {function_name}()\n"
            f"and store the result in {target}."
        ),
        f"Use {function_name}() to convert {source} and store it in {target}.",
        {
            "source": source,
            "source_value": source_value,
            "target": target,
            "function": function_name,
        },
        hints=[
            f"Create {source} first.",
            f"Call {function_name}() with {source}.",
            f"Store the converted value in {target}.",
            f"Use: {target} = {function_name}({source})",
        ],
        runtime_expected={
            source: source_value,
            target: result_value,
        },
    )


def _type_casting_a():
    value = random.randint(10, 99)
    return _casting_challenge(
        "type_casting_a",
        "score_text",
        str(value),
        "score",
        "int",
    )


def _type_casting_b():
    value = round(random.uniform(1.5, 9.5), 1)
    return _casting_challenge(
        "type_casting_b",
        "speed_text",
        str(value),
        "speed",
        "float",
    )


def _type_casting_c():
    value = random.randint(1, 12)
    return _casting_challenge(
        "type_casting_c",
        "level",
        value,
        "level_text",
        "str",
    )


def _type_casting_d():
    value = random.choice([20, 30, 40, 50, 60])
    return _casting_challenge(
        "type_casting_d",
        "energy_text",
        str(value),
        "energy",
        "int",
    )


def _type_casting_e():
    value = round(random.uniform(10.5, 50.5), 1)
    return _casting_challenge(
        "type_casting_e",
        "distance_text",
        str(value),
        "distance",
        "float",
    )


# =========================================================
# Input
# =========================================================

def _input_challenge(
    template_id,
    target,
    prompt,
    visible_value,
    hidden_values,
    description,
):
    return _challenge(
        template_id,
        "User Input Practice",
        "input",
        (
            f'Use input() with this exact prompt:\n\n"{prompt}"\n\n'
            f"Store the answer inside {target}.\n\n"
            f"The visible test input will be:\n{visible_value}\n\n"
            f"{description}"
        ),
        f"Use input() and store the result inside {target}.",
        {
            "target": target,
            "prompt": prompt,
        },
        hints=[
            f"The result must be stored in {target}.",
            "Use the input() function.",
            f'The prompt must be exactly: "{prompt}"',
            f'Use: {target} = input("{prompt}")',
        ],
        test_inputs=[visible_value],
        runtime_expected={
            target: visible_value,
        },
        hidden_tests=[
            {
                "input_values": [value],
                "runtime_expected": {
                    target: value,
                },
            }
            for value in hidden_values
        ],
    )


def _input_a():
    visible = random.choice(["Alex", "Mika", "Luna"])
    hidden = ["Kai", "Rin", "CodeBreaker"]

    return _input_challenge(
        "input_a",
        "name",
        "Enter your name: ",
        visible,
        hidden,
        "The program should work for other names too.",
    )


def _input_b():
    visible = random.choice(["Forest", "Beach", "Ruins"])
    hidden = ["Castle", "Village", "Cave"]

    return _input_challenge(
        "input_b",
        "destination",
        "Enter destination: ",
        visible,
        hidden,
        "Store whichever destination the user enters.",
    )


def _input_c():
    visible = random.choice(["Sword", "Map", "Potion"])
    hidden = ["Key", "Shield", "Torch"]

    return _input_challenge(
        "input_c",
        "item",
        "Choose an item: ",
        visible,
        hidden,
        "The input should not be hard-coded.",
    )


def _input_d():
    visible = str(random.randint(1, 9))
    hidden = ["3", "7", "12"]

    return _input_challenge(
        "input_d",
        "level_text",
        "Enter level: ",
        visible,
        hidden,
        "Keep the input as text for this problem.",
    )


def _input_e():
    visible = random.choice(["yes", "no"])
    hidden = ["yes", "no", "maybe"]

    return _input_challenge(
        "input_e",
        "answer",
        "Continue? ",
        visible,
        hidden,
        "Store the user's answer exactly as entered.",
    )


# =========================================================
# Formatted Output
# =========================================================

def _formatted_challenge(
    template_id,
    variable,
    value,
    prefix,
    suffix,
):
    expected_output = f"{prefix}{value}{suffix}"

    return _challenge(
        template_id,
        "Formatted Output Practice",
        "formatted_output",
        (
            f"Create:\n\n{variable} = {repr(value)}\n\n"
            f"Then use an f-string to display exactly:\n\n"
            f"{expected_output}"
        ),
        "Create the required variable and use it inside an f-string.",
        {
            "variable": variable,
            "value": value,
            "prefix": prefix,
            "suffix": suffix,
        },
        hints=[
            f"Create {variable} = {repr(value)} first.",
            "Use an f-string inside print().",
            f"Put {{{variable}}} inside the f-string.",
            f'Use this shape: print(f"{prefix}{{{variable}}}{suffix}")',
        ],
    )


def _formatted_output_a():
    return _formatted_challenge(
        "formatted_output_a",
        "name",
        random.choice(["Alex", "Mika", "Luna", "Kai"]),
        "Welcome, ",
        "!",
    )


def _formatted_output_b():
    return _formatted_challenge(
        "formatted_output_b",
        "score",
        random.randint(10, 99),
        "Score: ",
        " points",
    )


def _formatted_output_c():
    return _formatted_challenge(
        "formatted_output_c",
        "area",
        random.choice(["Forest", "Beach", "Ruins", "Castle"]),
        "Entering ",
        "...",
    )


def _formatted_output_d():
    return _formatted_challenge(
        "formatted_output_d",
        "keys",
        random.randint(1, 9),
        "Keys collected: ",
        "",
    )


def _formatted_output_e():
    return _formatted_challenge(
        "formatted_output_e",
        "enemy",
        random.choice(["Kapre", "Duwende", "Tikbalang"]),
        "Enemy spotted: ",
        "!",
    )


# =========================================================
# Operators
# =========================================================

def _operator_challenge(
    template_id,
    target,
    start,
    operator_name,
    operator_symbol,
    update,
    comparison_target,
    comparison_operator,
    comparison_symbol,
    comparison_value,
):
    if operator_name == "add_assign":
        final = start + update
    elif operator_name == "subtract_assign":
        final = start - update
    elif operator_name == "multiply_assign":
        final = start * update
    elif operator_name == "divide_assign":
        final = start / update
    else:
        raise ValueError(f"Unsupported assignment operator: {operator_name}")

    comparison_functions = {
        "eq": lambda a, b: a == b,
        "neq": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "gte": lambda a, b: a >= b,
        "lte": lambda a, b: a <= b,
    }

    result = comparison_functions[comparison_operator](
        final,
        comparison_value,
    )

    return _challenge(
        template_id,
        "Operators Practice",
        "operator",
        (
            f"Create {target} = {repr(start)}.\n"
            f"Then use {operator_symbol} with {repr(update)}.\n"
            f"Finally create {comparison_target} using:\n\n"
            f"{target} {comparison_symbol} {repr(comparison_value)}"
        ),
        "Use an assignment operator followed by a comparison operator.",
        {
            "target": target,
            "start_value": start,
            "operator": operator_name,
            "update_value": update,
            "final_value": final,
            "comparison_target": comparison_target,
            "comparison_operator": comparison_operator,
            "comparison_value": comparison_value,
            "comparison_result": result,
        },
        hints=[
            f"Start with {target} = {repr(start)}.",
            f"Update it using {target} {operator_symbol} {repr(update)}.",
            f"Create {comparison_target} with a comparison.",
            (
                f"Use: {comparison_target} = "
                f"{target} {comparison_symbol} {repr(comparison_value)}"
            ),
        ],
        runtime_expected={
            target: final,
            comparison_target: result,
        },
    )


def _operators_a():
    start = random.randint(2, 10)
    update = random.randint(2, 8)
    final = start + update

    return _operator_challenge(
        "operators_a",
        "score",
        start,
        "add_assign",
        "+=",
        update,
        "passed",
        "gte",
        ">=",
        final,
    )


def _operators_b():
    start = random.randint(12, 30)
    update = random.randint(2, 8)
    final = start - update

    return _operator_challenge(
        "operators_b",
        "health",
        start,
        "subtract_assign",
        "-=",
        update,
        "alive",
        "gt",
        ">",
        0 if final > 0 else final - 1,
    )


def _operators_c():
    start = random.randint(2, 6)
    update = random.randint(2, 4)
    final = start * update

    return _operator_challenge(
        "operators_c",
        "damage",
        start,
        "multiply_assign",
        "*=",
        update,
        "strong",
        "gte",
        ">=",
        final,
    )


def _operators_d():
    divisor = random.choice([2, 4, 5])
    final = random.randint(2, 8)
    start = final * divisor

    return _operator_challenge(
        "operators_d",
        "supplies",
        start,
        "divide_assign",
        "/=",
        divisor,
        "low_supply",
        "lte",
        "<=",
        float(final),
    )


def _operators_e():
    start = random.randint(5, 15)
    update = random.randint(1, 5)
    final = start + update
    comparison = final + random.randint(1, 4)

    return _operator_challenge(
        "operators_e",
        "energy",
        start,
        "add_assign",
        "+=",
        update,
        "needs_rest",
        "lt",
        "<",
        comparison,
    )


# =========================================================
# Strings
# =========================================================

def _string_challenge(
    template_id,
    name_target,
    name_value,
    message_target,
    prefix,
    result_target,
    method,
):
    combined = prefix + name_value

    if method == "upper":
        result = combined.upper()
    elif method == "lower":
        result = combined.lower()
    elif method == "strip":
        result = combined.strip()
    else:
        raise ValueError(f"Unsupported string method: {method}")

    return _challenge(
        template_id,
        "Strings Practice",
        "string",
        (
            f"Create {name_target} = {repr(name_value)}.\n"
            f"Create {message_target} by joining {repr(prefix)} "
            f"+ {name_target}.\n"
            f"Then create {result_target} using "
            f"{message_target}.{method}()."
        ),
        "Join strings with + and use the required string method.",
        {
            "name_target": name_target,
            "name_value": name_value,
            "message_target": message_target,
            "prefix": prefix,
            "result_target": result_target,
            "method": method,
            "result": result,
        },
        hints=[
            f"Create {name_target} first.",
            (
                f"Build {message_target} using "
                f"{repr(prefix)} + {name_target}."
            ),
            f"Call .{method}() on {message_target}.",
            (
                f"Use: {result_target} = "
                f"{message_target}.{method}()"
            ),
        ],
        runtime_expected={
            name_target: name_value,
            message_target: combined,
            result_target: result,
        },
    )


def _strings_a():
    return _string_challenge(
        "strings_a",
        "game_name",
        random.choice(["CodeBreak", "IslandRun", "Quest"]),
        "message",
        "Welcome to\n",
        "result",
        "upper",
    )


def _strings_b():
    return _string_challenge(
        "strings_b",
        "hero",
        random.choice(["ALEX", "MIKA", "LUNA"]),
        "message",
        "PLAYER: ",
        "result",
        "lower",
    )


def _strings_c():
    return _string_challenge(
        "strings_c",
        "area",
        random.choice(["Forest", "Castle", "Ruins"]),
        "message",
        "Entering\n",
        "result",
        "upper",
    )


def _strings_d():
    name_value = random.choice(["island   ", "castle   ", "village   "])

    return _string_challenge(
        "strings_d",
        "location",
        name_value,
        "message",
        "   ",
        "result",
        "strip",
    )


def _strings_e():
    return _string_challenge(
        "strings_e",
        "enemy",
        random.choice(["KAPRE", "DUWENDE", "TIKBALANG"]),
        "warning",
        "WARNING: ",
        "result",
        "lower",
    )


# =========================================================
# Control Flow
# =========================================================

def _control_flow_challenge(
    template_id,
    score_target,
    score_value,
    key_target,
    key_value,
    rank_target,
    high_threshold,
    mid_threshold,
    high_result,
    mid_result,
    low_result,
    boolean_target,
):
    if score_value >= high_threshold:
        rank_value = high_result
    elif score_value >= mid_threshold:
        rank_value = mid_result
    else:
        rank_value = low_result

    boolean_value = key_value and score_value >= mid_threshold

    return _challenge(
        template_id,
        "Control Flow Practice",
        "control_flow",
        (
            f"Set {score_target} = {score_value} and "
            f"{key_target} = {key_value}.\n\n"
            f"Use if/elif/else to create {rank_target}:\n"
            f'- "{high_result}" when {score_target} >= {high_threshold}\n'
            f'- "{mid_result}" when {score_target} >= {mid_threshold}\n'
            f'- "{low_result}" otherwise\n\n'
            f"Then create {boolean_target} using:\n"
            f"{key_target} and {score_target} >= {mid_threshold}"
        ),
        "Use if/elif/else and boolean logic with and.",
        {
            "score_target": score_target,
            "score_value": score_value,
            "key_target": key_target,
            "key_value": key_value,
            "rank_target": rank_target,
            "branches": [
                {
                    "operator": "gte",
                    "value": high_threshold,
                    "result": high_result,
                },
                {
                    "operator": "gte",
                    "value": mid_threshold,
                    "result": mid_result,
                },
            ],
            "else_result": low_result,
            "boolean_target": boolean_target,
            "boolean_variable": key_target,
            "boolean_operator": "and",
            "comparison_operator": "gte",
            "comparison_value": mid_threshold,
            "boolean_result": boolean_value,
        },
        hints=[
            (
                f"Create {score_target} = {score_value} and "
                f"{key_target} = {key_value} first."
            ),
            (
                f"Use if {score_target} >= {high_threshold}, "
                f"then elif {score_target} >= {mid_threshold}."
            ),
            f"Finish the decision with an else branch.",
            (
                f"Use: {boolean_target} = "
                f"{key_target} and {score_target} >= {mid_threshold}"
            ),
        ],
        runtime_expected={
            score_target: score_value,
            key_target: key_value,
            rank_target: rank_value,
            boolean_target: boolean_value,
        },
    )


def _control_flow_a():
    score = random.randint(75, 89)

    return _control_flow_challenge(
        "control_flow_a",
        "score",
        score,
        "has_key",
        True,
        "rank",
        90,
        75,
        "Gold",
        "Silver",
        "Bronze",
        "can_enter",
    )


def _control_flow_b():
    score = random.randint(90, 100)

    return _control_flow_challenge(
        "control_flow_b",
        "points",
        score,
        "mission_active",
        True,
        "reward",
        90,
        70,
        "Large",
        "Medium",
        "Small",
        "can_claim",
    )


def _control_flow_c():
    score = random.randint(40, 69)

    return _control_flow_challenge(
        "control_flow_c",
        "energy",
        score,
        "has_food",
        True,
        "status",
        80,
        60,
        "Strong",
        "Ready",
        "Tired",
        "can_travel",
    )


def _control_flow_d():
    score = random.randint(60, 79)

    return _control_flow_challenge(
        "control_flow_d",
        "health",
        score,
        "has_potion",
        random.choice([True, False]),
        "condition",
        80,
        60,
        "Healthy",
        "Hurt",
        "Critical",
        "can_continue",
    )


def _control_flow_e():
    score = random.randint(20, 59)

    return _control_flow_challenge(
        "control_flow_e",
        "progress",
        score,
        "gate_open",
        random.choice([True, False]),
        "stage",
        80,
        60,
        "Complete",
        "Almost",
        "Beginning",
        "can_finish",
    )


# =========================================================
# Template registry
# =========================================================

_TEMPLATE_BUILDERS = {
    # Python Syntax Basics
    "python_syntax_a": _python_syntax_a,
    "python_syntax_b": _python_syntax_b,
    "python_syntax_c": _python_syntax_c,
    "python_syntax_d": _python_syntax_d,
    "python_syntax_e": _python_syntax_e,

    # Variables
    "variables_a": _variables_a,
    "variables_b": _variables_b,
    "variables_c": _variables_c,
    "variables_d": _variables_d,
    "variables_e": _variables_e,

    # Data Types
    "data_types_a": _data_types_a,
    "data_types_b": _data_types_b,
    "data_types_c": _data_types_c,
    "data_types_d": _data_types_d,
    "data_types_e": _data_types_e,

    # Type Casting
    "type_casting_a": _type_casting_a,
    "type_casting_b": _type_casting_b,
    "type_casting_c": _type_casting_c,
    "type_casting_d": _type_casting_d,
    "type_casting_e": _type_casting_e,

    # Input
    "input_a": _input_a,
    "input_b": _input_b,
    "input_c": _input_c,
    "input_d": _input_d,
    "input_e": _input_e,

    # Formatted Output
    "formatted_output_a": _formatted_output_a,
    "formatted_output_b": _formatted_output_b,
    "formatted_output_c": _formatted_output_c,
    "formatted_output_d": _formatted_output_d,
    "formatted_output_e": _formatted_output_e,

    # Operators
    "operators_a": _operators_a,
    "operators_b": _operators_b,
    "operators_c": _operators_c,
    "operators_d": _operators_d,
    "operators_e": _operators_e,

    # Strings
    "strings_a": _strings_a,
    "strings_b": _strings_b,
    "strings_c": _strings_c,
    "strings_d": _strings_d,
    "strings_e": _strings_e,

    # Control Flow
    "control_flow_a": _control_flow_a,
    "control_flow_b": _control_flow_b,
    "control_flow_c": _control_flow_c,
    "control_flow_d": _control_flow_d,
    "control_flow_e": _control_flow_e,
}
