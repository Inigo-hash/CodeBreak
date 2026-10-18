"""Independent learner-style examples used only by verification, never the tutor."""
CASTLE_SOLUTIONS = {
'castle_tuples_inspect_001': '''def inspect_record(record):
    if not record:
        return (None, None, 0)
    return (record[0], record[-1], len(record))''',
'castle_tuples_replace_001': '''def replace_quantity(record, quantity):
    return (record[0], quantity)''',
'castle_dictionaries_lookup_001': '''def lookup_stock(stock, item):
    if item in stock:
        return stock[item]
    return 0''',
'castle_dictionaries_count_001': '''def count_items(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts''',
'castle_for_loops_total_001': '''def total_supplies(quantities):
    total = 0
    for quantity in quantities:
        total += quantity
    return total''',
'castle_for_loops_labels_001': '''def cell_labels(count):
    result = []
    for number in range(1, count + 1):
        result.append(number)
    return result''',
'castle_while_loops_charge_001': '''def charge_steps(current, target, step):
    count = 0
    while current < target:
        current += step
        count += 1
    return count''',
'castle_while_loops_countdown_001': '''def countdown(start):
    result = []
    while start > 0:
        result.append(start)
        start -= 1
    return result''',
'castle_nested_loops_flatten_001': '''def flatten_cells(rows):
    result = []
    for row in rows:
        for item in row:
            result.append(item)
    return result''',
'castle_nested_loops_coordinates_001': '''def cell_coordinates(rows, columns):
    result = []
    for row in range(rows):
        for column in range(columns):
            result.append((row, column))
    return result''',
'castle_loop_control_stop_001': '''def before_stop(items, stop):
    result = []
    for item in items:
        if item == stop:
            break
        result.append(item)
    return result''',
'castle_loop_control_skip_001': '''def positive_before_stop(numbers):
    result = []
    for number in numbers:
        if number == 0:
            break
        if number < 0:
            continue
        result.append(number)
    return result''',
'castle_functions_price_001': '''def supply_cost(quantity, price):
    return quantity * price''',
'castle_functions_invoice_001': '''def line_cost(quantity, price):
    return quantity * price

def invoice_total(quantities, price):
    result = 0
    for quantity in quantities:
        result += line_cost(quantity, price)
    return result''',
'castle_exceptions_parse_001': '''def parse_quantity(raw):
    try:
        return int(raw)
    except (ValueError, TypeError):
        return 0''',
'castle_exceptions_total_001': '''def valid_quantity_total(values):
    total = 0
    for raw in values:
        try:
            total += int(raw)
        except (ValueError, TypeError):
            continue
    return total''',
'castle_supply_final': '''def build_supply_report(records, minimum):
    result = {}
    for item, raw in records:
        try:
            quantity = int(raw)
        except (ValueError, TypeError):
            continue
        if quantity >= minimum:
            result[item] = result.get(item, 0) + quantity
    return result''',
'castle_rooms_final': '''def audit_rooms(rooms):
    result = {}
    for room in rooms:
        for item, raw in room:
            try:
                quantity = int(raw)
            except (ValueError, TypeError):
                continue
            if quantity >= 0:
                result[item] = result.get(item, 0) + quantity
    return result''',
'castle_manifest_final': '''def read_manifest(records, stop):
    result = {}
    for item, raw in records:
        if item == stop:
            break
        try:
            quantity = int(raw)
        except (ValueError, TypeError):
            continue
        if quantity >= 0:
            result[item] = result.get(item, 0) + quantity
    return result''',
}
