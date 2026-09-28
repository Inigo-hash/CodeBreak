"""Persistent shuffle bag and attempt records for the Stage 1 final assessment."""
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


def peek_assessment(session, rng=None):
    rng = rng or random
    bag = session.get('remaining', [])
    if not bag:
        bag = list(ASSESSMENT_IDS)
        rng.shuffle(bag)
        if bag[-1] == session.get('last'):
            bag[0], bag[-1] = bag[-1], bag[0]
        session['remaining'] = bag
    return get_final_assessment(bag[-1])


def start_attempt(session, challenge, now=None):
    if session.get('active'):
        raise ValueError('An assessment attempt is already active.')
    now = time.time() if now is None else now
    if not session.get('remaining') or session['remaining'][-1] != challenge['id']:
        raise ValueError('Start the selected assessment from the rotation.')
    session['remaining'].pop()
    session['last'] = challenge['id']
    session['active'] = {'challenge_id': challenge['id'], 'started_at': now,
                         'deadline': now + challenge['time_limit'], 'time_limit': challenge['time_limit']}
    return session['active']


def finish_attempt(session, result, now=None):
    active = session.pop('active', None)
    if not active:
        return
    record = dict(active)
    record.update(result=result, finished_at=time.time() if now is None else now)
    session.setdefault('history', []).append(record)
