"""Small, labelled reference answers; never executes or solves player code.

Only whole, recognized questions match. Everything else stays on the AI path.
Keep game facts tied to authored controls rather than an independent key list.
"""
import re

GUIDE_LABEL = 'Built-in guide: '


def built_in_answer(question):
    text = re.sub(r'\s+', ' ', question.strip().lower()).strip(' ?!.')
    definitions = {
        'python': 'Python is a programming language used to write instructions for a computer. CodeBreak teaches it through coding challenges. For example, print("Hello") displays Hello.',
        'a variable': 'A variable is a name that refers to a value. For example, score = 10 stores the value 10 under the name score.',
        'a list': 'A list is an ordered collection you can change. For example, items = ["key", "torch"]. Index 0 selects the first item; index -1 selects the last.',
        'a for loop': 'A for loop repeats code for each item in a collection. For example, for item in items: visits each item. Indent the code you want repeated.',
        'a while loop': 'A while loop repeats while its condition is true. Make sure something changes so the condition can eventually become false.',
        'a function': 'A function is a reusable block defined with def. Parameters receive inputs, and return sends a result back to the caller.',
        'a dictionary': 'A dictionary stores key-value pairs. For example, supplies = {"torches": 3}; supplies["torches"] reads the value 3.',
        'a tuple': 'A tuple is an ordered collection whose entries cannot be changed after creation. For example, position = (2, 4). You can read its entries with indexing.',
    }
    if text in ('who is python', 'ano ang python', 'ano yung python'):
        return GUIDE_LABEL + definitions['python']
    for subject, answer in definitions.items():
        if text in (f'what is {subject}', f"what's {subject}"):
            return GUIDE_LABEL + answer
    if text in ('what is codebreak', "what's codebreak"):
        return GUIDE_LABEL + 'CodeBreak is a desktop game for learning Python through exploration, coding challenges and combat with Filipino folklore creatures. Read lessons, solve challenges and follow your stage objectives.'
    if text in ('how to play the game', 'how do i play the game', 'how to play codebreak', 'how do i play codebreak'):
        return GUIDE_LABEL + ('Explore, search objects, read lessons and solve coding challenges. Open I for the stage manual and O for objectives. Open B, drag the sword to a hotbar slot and select it before fighting. Save from the pause menu.')
    if text in ('what are the controls', 'what are the game controls', 'how do i move', 'how to move'):
        from src.data.controls import CONTROL_SECTIONS
        movement = next(rows for title, rows in CONTROL_SECTIONS if title == 'MOVING AND FIGHTING')
        return GUIDE_LABEL + '; '.join(f'{key}: {action}' for key, action in movement) + '. Open I for the stage manual and full controls.'
    if text in ('how do i equip the sword', 'how to equip the sword', 'how do i attack'):
        from src.data.controls import CONTROL_NOTES
        return GUIDE_LABEL + ' '.join(CONTROL_NOTES[:2])
    if text in ('how do i save', 'how to save the game'):
        return GUIDE_LABEL + 'Press Escape to pause, then choose Save Game. Use the same save slot when you continue your adventure.'
    if text in ('how to cheat', 'how do i cheat', 'are there cheats', 'cheat codes'):
        # This module also runs on the relay, which has no Pygame display.
        # A server cannot know whether a downloaded game's debug keys are on.
        return GUIDE_LABEL + ('For normal progress, solve the required challenges to earn keys. '
                              'I can give hints if you tell me which lesson is difficult. '
                              'In testing builds with developer controls enabled, F4 toggles '
                              'developer exploration. It does not count as completing lessons or the stage.')
    return None


def _normalize(question):
    return re.sub(r'[^a-z0-9_+]+', ' ', question.lower()).strip()


def _has_phrase(text, phrase):
    return f' {_normalize(phrase)} ' in f' {text} '


def offline_answer(question, context=None, history=()):
    """Retrieve up to two reference entries, or admit there is no known answer.

    No generated-answer cache, eval, hidden test data, or solution code is used.
    Narrow exact answers are preserved; wider wording is used only as backup.
    """
    direct = built_in_answer(question)
    if direct:
        return direct
    text = _normalize(question)
    if not text:
        return None
    if any(_has_phrase(text, phrase) for phrase in ('saved game', 'save game', 'resume game', 'continue game', 'continue my game')):
        return GUIDE_LABEL + 'To resume, open Start Game, select Continue Game, then choose your existing save slot. Use its password. During play, Escape opens the pause menu; choose Save Game before leaving.'
    if re.search(r'\b(solve|solution|answer|finish|complete)\b', text) and re.search(r'\b(challenge|assessment|castle_\w+|stage1_\w+)\b', text):
        return GUIDE_LABEL + ('I can give hints, not a complete challenge solution. Check the required inputs, operation order and returned value. Try an empty input and one normal input, then use the lesson’s progressive hints for your next step.')
    from src.data.tutor_knowledge import PYTHON_HELP
    matches = []
    for key, aliases, answer in PYTHON_HELP:
        lengths = [len(_normalize(alias).split()) for alias in aliases if _has_phrase(text, alias)]
        if lengths:
            matches.append((max(lengths), key, answer))
    game_answer = _game_reference(text, context or {})
    game_specific = any(_has_phrase(text, term) for term in
                        ('heal', 'healing', 'hp', 'energy', 'sword', 'inventory', 'boss', 'stage', 'stage 1', 'stage 2', 'castle', 'island', 'controls'))
    if game_answer and (not matches or game_specific):
        return GUIDE_LABEL + game_answer
    matches.sort(key=lambda item: -item[0])
    # A follow-up such as "give an example" can reuse the last user question,
    # never the assistant's possibly generated answer or an arbitrary history.
    if not matches and text in ('give an example', 'example please', 'can you explain more', 'explain more', 'paano', 'halimbawa'):
        previous = next((turn.get('content', '') for turn in reversed(list(history)[-8:])
                         if turn.get('role') == 'user'), '')
        if previous and _normalize(previous) != text:
            return offline_answer(previous, context)
    if not matches:
        from src.data.topics import TOPICS
        topic = TOPICS.get(str((context or {}).get('topic', '')))
        if topic:
            reference = offline_answer('explain ' + topic['title'])
            if reference:
                return reference + '\nThis is a topic reference; offline help cannot inspect or execute your code.'
        return None
    # Don't drown a specific issue in general language or collection facts.
    specific = [m for m in matches if m[0] > 1 or m[1].endswith('_error') or m[1] in ('indexing', 'list_methods', 'exceptions')]
    selected = (specific or matches)[:2]
    return GUIDE_LABEL + '\n\n'.join(answer for _, _, answer in selected)


def unavailable_help():
    from src.data.tutor_knowledge import SUGGESTED_QUESTIONS
    return ('Offline guide: I do not have a reliable saved answer for that question. '
            'I can still help with CodeBreak controls, healing, stages and Python lessons. '
            'Try: ' + '; '.join(SUGGESTED_QUESTIONS[:4]) + '.')


def limited_answer(question, context=None, history=(), *, reason=None):
    """Keep answering from references when live capacity is exhausted."""
    answer = offline_answer(question, context, history)
    if answer:
        return answer
    status = ('The live AI has used its daily budget.' if reason == 'tutor_daily_limit'
              else 'The live AI is busy right now.')
    return ('Offline guide: ' + status + ' I can still help with saved Python explanations '
            'and CodeBreak rules. I do not have a reliable saved answer for that question. '
            'Ask about a lesson, controls, healing, or stage objectives.')


def _game_reference(text, context):
    from src.data.stages import STAGES
    from src.data.rooms import ROOM_STAGES
    def mentions(*phrases):
        return any(_has_phrase(text, phrase) for phrase in phrases)
    stage_id = str(context.get('stage', '')).lower()
    stage = next((s for s in STAGES.values() if stage_id in (s['id'].lower(), s['name'].lower())), None)
    if mentions('castle', 'stage 2'):
        stage = STAGES.get('castle')
    elif mentions('island', 'stage 1'):
        stage = STAGES.get('island')
    if mentions('heal', 'healing', 'recover hp', 'restore health', 'low health', 'low hp', 'pagaling', 'mag heal'):
        from src.data.player_rules import PLAYER_TORCH_HP_REGEN, PLAYER_TORCH_HEAL_DELAY
        island_rule = (f'On the Island at night, retreat from enemies and stand in a fixed map torch’s light. '
                       f'Living players recover {PLAYER_TORCH_HP_REGEN:g} HP per second after {PLAYER_TORCH_HEAL_DELAY:g} seconds without damage. '
                       'The held hotbar torch lights your way but does not trigger healing. HP is combat health; hearts are lives, and torch healing does not restore lost hearts.')
        if stage and stage['id'] == 'castle':
            return 'Castle rooms have night mode off by default, so do not expect fixed-torch healing there. ' + island_rule
        return island_rule + (' Castle rooms have night mode off by default.' if not stage else '')
    if mentions('energy', 'stamina', 'dodge', 'dash'):
        from src.data.player_rules import PLAYER_DODGE_ENERGY_COST, PLAYER_ENERGY_REGEN
        return f'Press Shift to dodge. It costs {PLAYER_DODGE_ENERGY_COST:g} energy; normal recovery is {PLAYER_ENERGY_REGEN:g} per second. Dashing passes through enemies, but walls stay solid. Retreat and recover rather than repeatedly dashing with too little energy.'
    if mentions('equip', 'sword', 'attack', 'weapon', 'hotbar', 'inventory', 'bag'):
        from src.data.controls import CONTROL_NOTES
        return ' '.join(CONTROL_NOTES[:2]) + ' Select slots with 1–5 or the mouse wheel. A torch or empty selected slot puts the sword away.'
    if mentions('controls', 'move', 'movement', 'walk', 'lakad'):
        from src.data.controls import CONTROL_SECTIONS
        rows = next(rows for title, rows in CONTROL_SECTIONS if title == 'MOVING AND FIGHTING')
        return '; '.join(f'{key}: {action}' for key, action in rows) + '. I opens the stage manual; M opens the map; O opens objectives.'
    if mentions('search', 'chest', 'crate', 'barrel', 'table'):
        return 'Stand beside a searchable object and hold E. Clear its guards first if combat blocks searching. Opened reward props stay consumed in the saved room; replaying a lesson or practice does not farm another mastery key.'
    if mentions('save', 'saving', 'load game', 'password'):
        return 'Pause with Escape and choose Save Game. Continue using the same slot and password. CodeBreak has three password-protected save slots. Keep your password: it cannot be recovered. Save before ending your demonstration.'
    if mentions('keys', 'key reward', 'mastery', 'unlock', 'progress', 'gate', 'boss', 'finish stage', 'final assessment'):
        stages = [stage] if stage else list(STAGES.values())
        facts = []
        for item in stages:
            rules = item.get('completion', {})
            boss = rules.get('required_boss')
            from src.data.enemies import ENEMIES
            boss_name = ENEMIES.get(boss, {}).get('name', boss) if boss else None
            facts.append(f"{item['name']} requires {rules.get('required_keys', 0)} keys and its required lesson challenges" +
                         (f', plus {boss_name}' if boss_name else '') +
                         (' and a final coding assessment.' if rules.get('required_final_challenge') else '.'))
        return ' '.join(facts) + ' Mastery means completing every required challenge for the topic. Practice gives no repeated key reward. Check O for current objectives; I cannot see your personal completion state.'
    if mentions('stage', 'stages', 'level', 'levels', 'room', 'rooms', 'castle', 'island', 'citadel'):
        parts = []
        for item in ([stage] if stage else STAGES.values()):
            rooms = [room['name'] for room in ROOM_STAGES.get(item['id'], {}).get('rooms', {}).values()]
            parts.append(item['name'] + (': ' + ', '.join(rooms) + '.' if rooms else ': ' + item.get('subtitle', '') + '.'))
        return ' '.join(parts) + ' Castle rooms are parts of Stage 2, not separate stages. Citadel is future Stage 3 content; I cannot promise an unfinished map is playable.'
    if mentions('coding', 'lesson', 'lessons', 'terminal', 'challenge', 'challenges', 'run', 'submit', 'hint', 'hints'):
        return 'Read the terminal’s lesson and worked example, then open its coding challenges. Run tests your code; Submit checks completion. Match required names, inputs and returned values or output. Failed submissions reveal progressive hints. Learning a topic can require more than one challenge; practice is for learning, not extra rewards.'
    if mentions('mang tahimik', 'offline', 'online ai', 'backup', 'artificial intelligence', 'ai not responding'):
        return 'Mang Tahimik uses an online AI for flexible explanations and debugging hints. If it is slow or unavailable, the bundled offline guide retrieves saved reference explanations and game facts. Built-in guide answers are labelled and are not a local generative AI. It never executes your code or supplies complete challenge solutions.'
    if mentions('codebreak', 'play the game', 'play game', 'how to play', 'purpose of the game'):
        return 'CodeBreak is a desktop Python-learning game combining exploration, coding tasks and combat with Filipino folklore creatures. Read lessons, solve challenges and follow objectives. Open I for the stage manual and O for objectives. Knowledge and saved progress matter alongside combat.'
    return None
