"""Stage 1 post-boss assessment flow, reused by the reminder and exit gate."""
from src.data.final_assessments import FINAL_COMPLETION_ID
from src.systems.final_assessment import peek_assessment, start_attempt, finish_attempt, settle_interrupted
from src.systems.stage_gate import evaluate_stage_gate
from src.screens.assessment_briefing import assessment_dialog
from src.ui.code_editor import CodeEditor


def open_final_assessment(screen, stage, state, sessions, persist, mark_passed):
    if stage.get('id') != 'island':
        return False
    gate = evaluate_stage_gate(stage, state.get('keys', 0), state.get('challenges_passed', []),
                               state.get('stage_progress', {}).get('defeated_enemies', []))
    if FINAL_COMPLETION_ID in state.get('challenges_passed', []):
        return True
    if not gate.boss_defeated or gate.missing_topic_ids:
        assessment_dialog(screen, 'ASSESSMENT LOCKED',
                          ['Complete the Stage 1 topics and defeat its boss first.'], 'BACK', False)
        return False
    session = sessions.setdefault('island', {})
    if settle_interrupted(session):
        persist()
    challenge = peek_assessment(session)
    minutes, seconds = divmod(challenge['time_limit'], 60)
    ready = assessment_dialog(screen, 'STAGE 1 FINAL ASSESSMENT', [
        challenge['title'],
        f'Time limit: {minutes}:{seconds:02d}. The timer starts when you press START.',
        'You can RUN, correct errors, and SUBMIT again while time remains.',
        'Timing out, exiting the editor, or closing the game ends this attempt. '
        'Your next attempt uses a different problem. Boss victory is kept.',
        'ESC here returns to the game without starting an attempt.',
    ])
    if not ready:
        return False
    active = start_attempt(session, challenge)
    persist()  # Save before entering the editor, including the consumed problem.

    def commit_pass():
        finish_attempt(session, 'passed')
        mark_passed()
        persist()

    editor = CodeEditor(screen, challenge, screen.copy(), mode='assessment',
                        time_limit=challenge['time_limit'], assessment_deadline=active['deadline'],
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
            'Your next retake will use a different problem.',
            'Your topics, keys, and boss victory are kept. Use the assessment reminder '
            'or stage gate whenever you are ready to try again.',
        ], 'BACK TO GAME', False)
    return editor.solved
