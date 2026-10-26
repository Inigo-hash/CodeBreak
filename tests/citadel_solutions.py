"""Independent correct submissions used by tests, never runtime tutor facts."""
CITADEL_SOLUTIONS = {
    'citadel_comprehensions_squares_001': 'def positive_squares(numbers):\n    return [n*n for n in numbers if n > 0]',
    'citadel_comprehensions_labels_001': 'def clean_labels(labels):\n    return [s.strip().lower() for s in labels if s.strip()]',
    'citadel_sets_unique_001': 'def unique_runes(runes):\n    return sorted(set(runes))',
    'citadel_sets_shared_001': 'def shared_runes(left, right):\n    return sorted(set(left) & set(right))',
    'citadel_sorting_rank_001': 'def rank_seals(records):\n    return sorted(records, key=lambda r: (-r[1], r[0]))',
    'citadel_sorting_stable_001': 'def order_crates(records):\n    return sorted(records, key=lambda r: r[1])',
    'citadel_algorithms_search_001': '''def find_first_seal(records, wanted):
    for record in records:
        if record[0] == wanted:
            return record
    return None''',
    'citadel_algorithms_group_001': '''def total_readings(records):
    result = {}
    for name, raw in records:
        try:
            value = int(raw)
        except (ValueError, TypeError):
            continue
        if value >= 0:
            result[name] = result.get(name, 0) + value
    return result''',
    'citadel_restoration_final': '''def restore_reactor(records, minimum):
    totals = {}
    for name, raw in records:
        name = name.strip().lower()
        if not name:
            continue
        try:
            power = int(raw)
        except (ValueError, TypeError):
            continue
        if power >= minimum:
            totals[name] = totals.get(name, 0) + power
    return sorted(totals.items(), key=lambda pair: (-pair[1], pair[0]))''',
}
