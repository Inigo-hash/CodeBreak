"""Rehearse offline coverage or verify a genuinely generated live tutor reply."""
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.systems.ai_tutor import ask_mang_tahimik, TutorError
from src.data.tutor_knowledge import PYTHON_HELP


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--offline', action='store_true')
    mode.add_argument('--live', action='store_true')
    args = parser.parse_args()
    old_mode = os.environ.get('CODEBREAK_TUTOR_MODE')
    try:
        os.environ['CODEBREAK_TUTOR_MODE'] = 'offline' if args.offline else 'auto'
        if args.offline:
            questions = ['please explain ' + aliases[0] for _, aliases, _ in PYTHON_HELP]
            questions += ['where can i heal', 'how do i equip the sword', 'how many keys unlock the castle gate']
            for question in questions:
                answer = ask_mang_tahimik(question)
                if not answer.startswith('Built-in guide:'):
                    print('FAIL: no reference for ' + question)
                    return 1
            print(f'PASS: {len(questions)} offline reference checks; no server or API key required.')
        else:
            answer = ask_mang_tahimik('Explain the difference between append() and pop() with one unrelated Python example.')
            if answer.startswith(('Built-in guide:', 'Offline guide:')):
                print('LIVE AI NOT VERIFIED: a local reference was used instead. The offline backup is working.')
                return 1
            print('LIVE REPLY RECEIVED:\n' + answer)
        return 0
    except TutorError as exc:
        print('LIVE AI NOT VERIFIED: ' + str(exc))
        return 1
    finally:
        if old_mode is None:
            os.environ.pop('CODEBREAK_TUTOR_MODE', None)
        else:
            os.environ['CODEBREAK_TUTOR_MODE'] = old_mode


if __name__ == '__main__':
    raise SystemExit(main())
