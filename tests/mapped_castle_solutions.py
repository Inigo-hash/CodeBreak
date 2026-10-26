"""Reference solutions for the current mapped Castle lessons; tests only."""
MAPPED_CASTLE_SOLUTIONS = {
    "iterative_structure_lesson_for_001": "def sum_training_points(limit):\n    total = 0\n    for number in range(1, limit + 1):\n        total += number\n    return total",
    "iterative_structure_lesson_nested_001": "def count_training_tiles(rows, columns):\n    count = 0\n    for row in range(rows):\n        for column in range(columns):\n            count += 1\n    return count",
    "iterative_structure_lesson_control_001": "def count_launch_numbers(start):\n    count = 0\n    number = start\n    while number > 0:\n        count += 1\n        number -= 1\n    return count",
    "lists_lesson_report_001": "def list_report(items):\n    if not items:\n        return (None, 0)\n    return (items[0], len(items))",
    "lists_lesson_update_001": "def add_inventory_item(items, new_item):\n    result = list(items)\n    result.append(new_item)\n    return result",
    "functions_lesson_greet_001": "def greet_explorer(name):\n    return \"Hello, \" + name",
    "functions_lesson_total_001": "def add_supplies(first, second):\n    return first + second",
    "tuples_lesson_coordinates_001": "def make_coordinates(x, y):\n    return (x, y)",
    "tuples_lesson_distance_001": "def get_x_coordinate(point):\n    return point[0]",
    "error_handling_lesson_safe_int_001": "def safe_number(text):\n    try:\n        return int(text)\n    except ValueError:\n        return None",
    "error_handling_lesson_safe_divide_001": "def safe_divide(first, second):\n    try:\n        return first / second\n    except ZeroDivisionError:\n        return None"
}
