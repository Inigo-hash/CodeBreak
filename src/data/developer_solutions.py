"""Reference snippets for the password-gated developer lesson helper.

These are convenience fixtures for local game testing, not learner hints or
part of the challenge validators. Press F7 in a challenge editor to load one.
"""

DEVELOPER_SOLUTIONS = {
    # Stage 1
    "print_001": 'print("Hello, World!")',
    "python_syntax_basics_001": 'print("Hello, Explorer!")',
    "variables_001": "age = 18",
    "data_types_001": 'age = 18\nheight = 1.75\nname = "Alex"\nis_ready = True',
    "type_casting_001": 'age_text = "18"\nage = int(age_text)',
    "input_lesson_001": 'name = input("Enter your name: ")',
    "formatted_output_001": 'name = "Alex"\nprint(f"Welcome, {name}!")',
    "operators_lesson_001": "score = 5\nscore += 3\npassed = score >= 8",
    "strings_lesson_001": 'game_name = "CodeBreak"\nmessage = "Welcome to\\n" + game_name\nresult = message.upper()',
    "control_flow_lesson_001": "score = 85\nhas_key = True\nif score >= 90:\n    rank = 'Gold'\nelif score >= 75:\n    rank = 'Silver'\nelse:\n    rank = 'Bronze'\ncan_enter = has_key and score >= 75",
    "stage1_final_001": 'name = input("Enter explorer name: ")\nscore_text = input("Enter score: ")\nscore = int(score_text)\nscore += 10\nif score >= 90:\n    rank = "Gold"\nelif score >= 75:\n    rank = "Silver"\nelse:\n    rank = "Bronze"\nmessage = f"{name} - {rank}"\nfinal_message = message.upper()\nprint(final_message)',
    "stage1_supply_final": 'name = input("Enter explorer name: ")\namount_text = input("Enter amount: ")\namount = int(amount_text)\ntotal = amount * 4 + 6\nif total >= 46:\n    status = "Stocked"\nelif total >= 26:\n    status = "Ready"\nelse:\n    status = "Low"\nready = total >= 26\nmessage = f"{name} - Supplies: {total} - {status}"\nfinal_message = message.upper()\nprint(final_message)',
    "stage1_energy_final": 'name = input("Enter explorer name: ")\namount_text = input("Enter amount: ")\namount = int(amount_text)\ntotal = (amount - 15) * 2\nif total >= 100:\n    status = "Stable"\nelif total >= 50:\n    status = "Charging"\nelse:\n    status = "Weak"\nready = total >= 50\nmessage = f"{name} - Energy: {total} - {status}"\nfinal_message = message.upper()\nprint(final_message)',
    "stage1_bridge_final": 'name = input("Enter explorer name: ")\namount_text = input("Enter amount: ")\namount = int(amount_text)\ntotal = amount * 5 - 20\nif total >= 100:\n    status = "Complete"\nelif total >= 50:\n    status = "Partial"\nelse:\n    status = "Insufficient"\nready = total >= 50\nmessage = f"{name} - Budget: {total} - {status}"\nfinal_message = message.upper()\nprint(final_message)',
    # Stage 2
    "iterative_structure_lesson_for_001": "def sum_training_points(limit):\n    total = 0\n    for number in range(1, limit + 1):\n        total += number\n    return total",
    "iterative_structure_lesson_nested_001": "def count_training_tiles(rows, columns):\n    count = 0\n    for row in range(rows):\n        for column in range(columns):\n            count += 1\n    return count",
    "iterative_structure_lesson_control_001": "def count_launch_numbers(start):\n    count = 0\n    number = start\n    while number > 0:\n        count += 1\n        number -= 1\n    return count",
    "lists_lesson_report_001": "def list_report(items):\n    if not items:\n        return (None, 0)\n    return (items[0], len(items))",
    "lists_lesson_update_001": "def add_inventory_item(items, new_item):\n    result = list(items)\n    result.append(new_item)\n    return result",
    "functions_lesson_greet_001": 'def greet_explorer(name):\n    return "Hello, " + name',
    "functions_lesson_total_001": "def add_supplies(first, second):\n    return first + second",
    "tuples_lesson_coordinates_001": "def make_coordinates(x, y):\n    return (x, y)",
    "tuples_lesson_distance_001": "def get_x_coordinate(point):\n    return point[0]",
    "error_handling_lesson_safe_int_001": "def safe_number(text):\n    try:\n        return int(text)\n    except ValueError:\n        return None",
    "error_handling_lesson_safe_divide_001": "def safe_divide(first, second):\n    try:\n        return first / second\n    except ZeroDivisionError:\n        return None",
    # Castle curriculum
    "castle_tuples_inspect_001": "def inspect_record(record):\n    if not record:\n        return (None, None, 0)\n    return (record[0], record[-1], len(record))",
    "castle_tuples_replace_001": "def replace_quantity(record, quantity):\n    return (record[0], quantity)",
    "castle_dictionaries_lookup_001": "def lookup_stock(stock, item):\n    if item in stock:\n        return stock[item]\n    return 0",
    "castle_dictionaries_count_001": "def count_items(items):\n    counts = {}\n    for item in items:\n        counts[item] = counts.get(item, 0) + 1\n    return counts",
    "castle_for_loops_total_001": "def total_supplies(quantities):\n    total = 0\n    for quantity in quantities:\n        total += quantity\n    return total",
    "castle_for_loops_labels_001": "def cell_labels(count):\n    result = []\n    for number in range(1, count + 1):\n        result.append(number)\n    return result",
    "castle_while_loops_charge_001": "def charge_steps(current, target, step):\n    count = 0\n    while current < target:\n        current += step\n        count += 1\n    return count",
    "castle_while_loops_countdown_001": "def countdown(start):\n    result = []\n    while start > 0:\n        result.append(start)\n        start -= 1\n    return result",
    "castle_nested_loops_flatten_001": "def flatten_cells(rows):\n    result = []\n    for row in rows:\n        for item in row:\n            result.append(item)\n    return result",
    "castle_nested_loops_coordinates_001": "def cell_coordinates(rows, columns):\n    result = []\n    for row in range(rows):\n        for column in range(columns):\n            result.append((row, column))\n    return result",
    "castle_loop_control_stop_001": "def before_stop(items, stop):\n    result = []\n    for item in items:\n        if item == stop:\n            break\n        result.append(item)\n    return result",
    "castle_loop_control_skip_001": "def positive_before_stop(numbers):\n    result = []\n    for number in numbers:\n        if number == 0:\n            break\n        if number < 0:\n            continue\n        result.append(number)\n    return result",
    "castle_functions_price_001": "def supply_cost(quantity, price):\n    return quantity * price",
    "castle_functions_invoice_001": "def line_cost(quantity, price):\n    return quantity * price\n\ndef invoice_total(quantities, price):\n    result = 0\n    for quantity in quantities:\n        result += line_cost(quantity, price)\n    return result",
    "castle_exceptions_parse_001": "def parse_quantity(raw):\n    try:\n        return int(raw)\n    except (ValueError, TypeError):\n        return 0",
    "castle_exceptions_total_001": "def valid_quantity_total(values):\n    total = 0\n    for raw in values:\n        try:\n            total += int(raw)\n        except (ValueError, TypeError):\n            continue\n    return total",
    "castle_supply_final": "def build_supply_report(records, minimum):\n    total = 0\n    count = 0\n    for item, raw in records:\n        try:\n            quantity = int(raw)\n        except ValueError:\n            continue\n        if quantity >= minimum:\n            total += quantity\n            count += 1\n    return (total, count)",
    "castle_rooms_final": "def audit_rooms(rooms):\n    result = []\n    for room in rooms:\n        total = 0\n        for item, raw in room:\n            try:\n                quantity = int(raw)\n            except ValueError:\n                continue\n            if quantity >= 0:\n                total += quantity\n        result.append(total)\n    return result",
    "castle_manifest_final": "def read_manifest(records, stop):\n    result = []\n    for item, raw in records:\n        if item == stop:\n            break\n        try:\n            quantity = int(raw)\n        except ValueError:\n            continue\n        if quantity >= 0:\n            result.append((item, quantity))\n    return result",
}
