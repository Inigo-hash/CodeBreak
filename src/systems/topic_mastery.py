"""Build a complete reward snapshot before the existing atomic slot write."""
from copy import deepcopy
from src.data.topics import TOPICS, topic_challenge_ids


def reconcile_mastery(state, stage):
    result = deepcopy(state)
    bundles = stage.get('completion', {}).get('mastery_bundles', {})
    if not bundles:
        return result
    passed = set(result.get('challenges_passed', []))
    completed = list(result.get('topics_completed', []))
    claims = set(result.get('mastery_reward_claims') or [])
    for bundle_id, bundle in bundles.items():
        mastered = set(bundle['challenges']).issubset(passed)
        for topic_id in bundle['topics']:
            if mastered and topic_id not in completed:
                completed.append(topic_id)
            elif not mastered and topic_id in completed:
                completed.remove(topic_id)
        if mastered:
            claims.add(bundle_id)
    earned = sum(bundle['keys'] for key, bundle in bundles.items() if key in claims)
    result['topics_completed'] = completed
    result['mastery_reward_claims'] = sorted(claims)
    result['keys'] = min(stage['completion']['required_keys'], max(int(result.get('keys', 0)), earned))
    return result


def complete_topic_challenge(state, stage, topic_id, challenge_id, practice=False):
    result = deepcopy(state)
    if practice or challenge_id not in topic_challenge_ids(TOPICS[topic_id]):
        return result
    passed = result.setdefault('challenges_passed', [])
    if challenge_id not in passed:
        passed.append(challenge_id)
    if set(topic_challenge_ids(TOPICS[topic_id])).issubset(passed):
        completed = result.setdefault('topics_completed', [])
        if topic_id not in completed:
            completed.append(topic_id)
    return reconcile_mastery(result, stage)
