"""Stage-authored post-boss assessment flow, reused by the reminder and exit gate."""
from src.data.final_assessments import assessment_ids_for_stage
from src.systems.rooms import stage_defeated_enemies
from src.systems.final_assessment import peek_assessment, start_attempt, finish_attempt, settle_interrupted
from src.systems.stage_gate import evaluate_stage_gate
from src.screens.assessment_briefing import assessment_dialog
from src.ui.code_editor import CodeEditor


def open_final_assessment(screen, stage, state, sessions, persist, mark_passed, consume_bonus=None):
    completion_id = stage.get('completion', {}).get('required_final_challenge')
    if not completion_id:
        return False
    gate = evaluate_stage_gate(stage, state.get('keys', 0), state.get('challenges_passed', []),
                               stage_defeated_enemies(state))
    if completion_id in state.get('challenges_passed', []):
        return True
    if not gate.boss_defeated or gate.missing_topic_ids or gate.keys < gate.required_keys:
        assessment_dialog(screen, 'ASSESSMENT LOCKED',
                          ['Complete this stage’s topics, collect its keys, and defeat its boss first.'], 'BACK', False)
        return False
    session = sessions.setdefault(stage['id'], {})
    if settle_interrupted(session):
        persist()
    challenge = peek_assessment(session, assessment_ids=assessment_ids_for_stage(stage))
    if challenge is None:
        assessment_dialog(screen, 'ASSESSMENT UNAVAILABLE',
                          ['This stage’s assessment content has not been authored yet.'], 'BACK', False)
        return False
    if stage.get('completion', {}).get('practice_after_failure') and session.get('practice_required'):
        if not assessment_dialog(screen, 'PRACTICE BEFORE RETAKING', [
                'Complete one untimed practice report before the next timed attempt.',
                'Practice keeps your keys, boss victory and bonus time. It grants no completion rewards.',
        ], 'OPEN PRACTICE'):
            return False
        practice = dict(challenge, id='practice_' + challenge['id'], practice_only=True)
        practice_editor = CodeEditor(screen, practice, screen.copy(), mode='practice')
        practice_editor.run()
        if not practice_editor.solved:
            return False
        session['practice_required'] = False
        session['practice_completed'] = session.get('practice_completed', 0) + 1
        persist()
    bonus = max(0, min(300, int(state.get('bonus_time', 0)))) if consume_bonus else 0
    minutes, seconds = divmod(challenge['time_limit'] + bonus, 60)
    ready = assessment_dialog(screen, f"{stage.get('name', stage['id']).upper()} FINAL ASSESSMENT", [
        challenge['title'],
        f'Time limit: {minutes}:{seconds:02d}. The timer starts when you press START.',
        f'Includes {bonus} earned bonus seconds (up to 300 per attempt), spent only when you START.',
        'You can RUN, correct errors, and SUBMIT again while time remains.',
        'Timing out, exiting the editor, or closing the game ends this attempt. '
        'Your next attempt uses the stage’s assessment rotation. Boss victory is kept.',
        'ESC here returns to the game without starting an attempt.',
    ])
    if not ready:
        return False
    active = start_attempt(session, challenge, bonus_time=bonus)
    if consume_bonus:
        consume_bonus(bonus)
    persist()  # Save before entering the editor, including the consumed problem.

    def commit_pass():
        finish_attempt(session, 'passed')
        mark_passed()
        persist()

    editor = CodeEditor(screen, challenge, screen.copy(), mode='assessment',
                        time_limit=active['time_limit'], assessment_deadline=active['deadline'],
                        on_assessment_pass=commit_pass)
    try:
        editor.run()
    finally:
        if session.get('active'):
            finish_attempt(session, 'timed_out' if editor.timed_out else 'abandoned')
            persist()
    if not editor.solved:
        assessment_dialog(screen, 'TIME IS UP' if editor.timed_out else 'ATTEMPT ENDED', [
            'This assessment was not completed.',
            'Your next retake uses the stage’s assessment rotation.',
            'Your topics, keys, and boss victory are kept.',
            'Complete an untimed practice report before retaking.'
            if stage.get('completion', {}).get('practice_after_failure') else
            'Use the reminder or stage gate whenever you are ready to try again.',
        ], 'BACK TO GAME', False)
    return editor.solved
