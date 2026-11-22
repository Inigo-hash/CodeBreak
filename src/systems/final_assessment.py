"""Persistent shuffle bag and attempt records for stage final assessments."""
import random
import time
from src.data.final_assessments import ASSESSMENT_IDS, get_final_assessment


def settle_interrupted(session, now=None):
    """A process closed during an attempt must not grant that attempt a new clock."""
    active = session.get('active')
    if not active:
        return False
    now = time.time() if now is None else now
    finish_attempt(session, 'timed_out' if now >= active['deadline'] else 'interrupted', now)
    return True


def peek_assessment(session, rng=None, assessment_ids=None):
    rng = rng or random
    pool = tuple(ASSESSMENT_IDS if assessment_ids is None else assessment_ids)
    if not pool:
        return None
    bag = [key for key in session.get('remaining', []) if key in pool]
    session['remaining'] = bag
    if not bag:
        bag = list(pool)
        rng.shuffle(bag)
        if bag[-1] == session.get('last'):
            bag[0], bag[-1] = bag[-1], bag[0]
        session['remaining'] = bag
    return get_final_assessment(bag[-1])


def pick_practice_assessment(session, upcoming_id, assessment_ids, rng=None):
    """Choose an untimed practice problem that differs from the next real attempt.

    The practice report must never be the same problem the player is about to
    be timed on, and it avoids repeating the previous practice problem when
    other choices exist.
    """
    rng = rng or random
    pool = [key for key in dict.fromkeys(assessment_ids) if key != upcoming_id]
    if not pool:
        return upcoming_id
    fresh = [key for key in pool if key != session.get('last_practice')]
    choice = rng.choice(fresh or pool)
    session['last_practice'] = choice
    return choice


def start_attempt(session, challenge, now=None, bonus_time=0):
    if session.get('active'):
        raise ValueError('An assessment attempt is already active.')
    now = time.time() if now is None else now
    if not session.get('remaining') or session['remaining'][-1] != challenge['id']:
        raise ValueError('Start the selected assessment from the rotation.')
    session['remaining'].pop()
    session['last'] = challenge['id']
    bonus = max(0, min(300, int(bonus_time or 0)))
    limit = challenge['time_limit'] + bonus
    session['active'] = {'challenge_id': challenge['id'], 'started_at': now,
                         'deadline': now + limit, 'time_limit': limit, 'bonus_time': bonus}
    return session['active']


def finish_attempt(session, result, now=None):
    active = session.pop('active', None)
    if not active:
        return
    record = dict(active)
    record.update(result=result, finished_at=time.time() if now is None else now)
    session.setdefault('history', []).append(record)
    if result != 'passed':
        session['practice_required'] = True