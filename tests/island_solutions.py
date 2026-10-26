"""Restore the original Island fixtures to the all-challenge regression suite."""
ISLAND_SOLUTIONS = {
    'print_001': 'print("Hello, World!")',
    'python_syntax_basics_001': 'print("Hello, Explorer!")',
    'variables_001': 'age = 18',
    'data_types_001': 'age = 18\nheight = 1.75\nname = "Alex"\nis_ready = True',
    'type_casting_001': 'age_text = "18"\nage = int(age_text)',
    'input_lesson_001': 'name = input("Enter your name: ")',
    'formatted_output_001': 'name = "Alex"\nprint(f"Welcome, {name}!")',
    'operators_lesson_001': 'score = 5\nscore += 3\npassed = score >= 8',
    'strings_lesson_001': 'game_name = "CodeBreak"\nmessage = "Welcome to\\n" + game_name\nresult = message.upper()',
    'control_flow_lesson_001': '''score = 85
has_key = True
if score >= 90:
    rank = 'Gold'
elif score >= 75:
    rank = 'Silver'
else:
    rank = 'Bronze'
can_enter = has_key and score >= 75''',
    'stage1_final_001': '''name = input("Enter explorer name: ")
score_text = input("Enter score: ")
score = int(score_text)
score += 10
if score >= 90:
    rank = 'Gold'
elif score >= 75:
    rank = 'Silver'
else:
    rank = 'Bronze'
message = f"{name} - {rank}"
final_message = message.upper()
print(final_message)''',
}
