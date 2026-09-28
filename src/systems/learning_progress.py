"""Read-only Stage 1 progress shared by the HUD and save-slot percentage."""
from src.data.topics import TOPICS
from src.systems.stage_gate import evaluate_stage_gate, required_topic_ids


def progress_snapshot(stage, state):
    passed = set(state.get('challenges_passed', ()))
    discovered = set(state.get('topics_discovered', ()))
    completed = set(state.get('topics_completed', ()))
    gate = evaluate_stage_gate(stage, state.get('keys', 0), passed,
                               state.get('stage_progress', {}).get('defeated_enemies', ()))
    by_challenge = {topic['challenge_id']: (key, topic) for key, topic in TOPICS.items()}
    rows = []
    for challenge_id in required_topic_ids(stage):
        topic_id, topic = by_challenge.get(challenge_id, (challenge_id, {}))
        missing = [key for key in topic.get('requirements', ()) if key not in completed]
        done = challenge_id in passed
        rows.append({
            'id': topic_id, 'title': topic.get('title', challenge_id),
            'status': 'Completed' if done else 'Locked' if missing else 'Available',
            'discovered': done or topic_id in discovered,
            'missing': [TOPICS.get(key, {}).get('title', key) for key in missing],
            'requirements': [TOPICS.get(key, {}).get('title', key)
                             for key in topic.get('requirements', ())],
        })
    units = len(rows) + bool(gate.required_boss_id) + bool(gate.required_final_challenge_id)
    done = gate.completed_topics + (bool(gate.required_boss_id) and gate.boss_defeated) + (
        bool(gate.required_final_challenge_id) and gate.final_challenge_completed)
    percent = round(100 * done / units) if units else 0
    # All learning milestones can be finished before the remaining keys are earned.
    if not gate.unlocked:
        percent = min(99, percent)
    if stage.get('id') in state.get('completed_stages', ()):
        percent = 100
    next_row = next((row for row in rows if row['status'] == 'Available'), None)
    if next_row:
        verb = 'Complete' if next_row['discovered'] else 'Find and complete'
        guidance = f"{verb} {next_row['title']}."
    elif gate.missing_topic_ids:
        guidance = 'Complete the prerequisites shown in Topic Guidance.'
    elif gate.keys < gate.required_keys:
        guidance = 'Clear the remaining enemy areas to collect the required keys.'
    elif not gate.boss_defeated:
        guidance = 'Enter the boss area and defeat the Stage 1 boss.'
    elif not gate.final_challenge_completed:
        guidance = 'Take the final assessment using the reminder or stage gate.'
    else:
        guidance = 'Stage requirements complete. Proceed to the stage gate.'
    return {'percent': percent, 'topics': rows, 'gate': gate, 'next': guidance}
