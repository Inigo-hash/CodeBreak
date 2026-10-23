"""Defence reliability: network-down references and the live-first slow path."""
import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from src.systems.ai_tutor import TutorSession, ask_mang_tahimik
from src.systems.tutor_guide import offline_answer, unavailable_help
from src.data.tutor_knowledge import PYTHON_HELP


class OfflineKnowledgeTests(unittest.TestCase):
    def test_every_reference_topic_retrieves_without_a_server(self):
        for _, aliases, _ in PYTHON_HELP:
            with self.subTest(alias=aliases[0]):
                answer = offline_answer('please explain ' + aliases[0])
                self.assertIsNotNone(answer)
                self.assertTrue(answer.startswith('Built-in guide:'))

    def test_reworded_and_taglish_questions(self):
        for question, expected in (
                ('paano gumagana ang while loop?', 'eventually'),
                ('can you explain for loops please?', 'range'),
                ('ano ang dictionary?', 'keys'),
                ('tell me about negative indexing', 'Indexing'),
                ('what happens when pop removes the only item?', 'still returned'),
                ('why does input need conversion?', 'text')):
            with self.subTest(question=question):
                self.assertIn(expected, offline_answer(question))

    def test_python_keys_and_ranges_do_not_turn_into_stage_help(self):
        self.assertIn('dictionary', offline_answer('explain dictionary keys'))
        self.assertNotIn('requires 9 keys', offline_answer('explain dictionary keys'))
        self.assertIn('range', offline_answer('how do I run for loops'))

    def test_live_authored_stage_requirements_not_stale_plan(self):
        from src.data.stages import STAGES
        castle = offline_answer('how many keys unlock the gate?', {'stage': 'castle'})
        self.assertIn(str(STAGES['castle']['completion']['required_keys']) + ' keys', castle)
        self.assertNotIn('Island requires', castle)
        self.assertIn('Castle', offline_answer('what rooms are in stage 2'))

    def test_healing_uses_rules_and_does_not_claim_player_state(self):
        from src.data.player_rules import PLAYER_TORCH_HEAL_DELAY
        answer = offline_answer('where can i heal?', {'stage': 'castle'})
        self.assertIn('night mode off', answer)
        self.assertIn(f'{PLAYER_TORCH_HEAL_DELAY:g} seconds', answer)
        self.assertIn('held hotbar torch', answer)

    def test_hints_never_return_a_complete_challenge_solution(self):
        answer = offline_answer('give the complete solution to the castle_lists challenge')
        self.assertIn('hints, not a complete challenge solution', answer)
        self.assertNotIn('def update_items', answer)
        self.assertNotIn('function_cases', answer)

    def test_unknown_question_is_not_a_fabricated_reference(self):
        self.assertIsNone(offline_answer('what is my exact health and map position?'))
        self.assertIn('do not have a reliable saved answer', unavailable_help())

    def test_followup_uses_last_user_topic_not_untrusted_ai_claim(self):
        history = [{'role':'user','content':'explain while loops'},
                   {'role':'assistant','content':'invent a potion shop'}]
        answer = offline_answer('can you explain more?', history=history)
        self.assertIn('while', answer)
        self.assertNotIn('potion', answer)

    def test_topic_context_gives_reference_without_pretending_to_debug(self):
        answer = offline_answer('check my work please', {'topic':'castle_functions'})
        self.assertIn('function', answer)
        self.assertIn('cannot inspect or execute', answer)


class ClientFailoverTests(unittest.TestCase):
    @patch.dict('os.environ', {'CODEBREAK_TUTOR_URL':'https://tutor.example/ask'})
    def test_legacy_limit_uses_requested_topic_and_keeps_followup_context(self):
        failure = HTTPError('url', 429, 'private', {}, BytesIO(
            b'{"code":"tutor_session_limit","retry_after":18}'))
        with patch('src.systems.ai_tutor.request.urlopen', side_effect=failure) as send:
            answer = ask_mang_tahimik('can you explain more?', history=[
                {'role': 'user', 'content': 'explain while loops'},
                {'role': 'assistant', 'content': 'private invented answer'}])
        self.assertIn('eventually', answer)
        self.assertNotIn('18 seconds', answer)
        self.assertNotIn('private', answer)
        send.assert_called_once()

    def test_finished_reply_accepts_next_question_at_the_same_clock_time(self):
        session = TutorSession(lambda *args: 'live hint')
        with patch('src.systems.ai_tutor.time.monotonic', return_value=100):
            for question in ('first question', 'second question', 'third question', 'fourth question'):
                self.assertTrue(session.submit(question))
                result = session.results.get(timeout=2)
                session._worker.join(2)
                session.results.put(result)
                self.assertEqual(session.poll(), 'live hint')
        self.assertEqual(len(session.history), 8)

    @patch.dict('os.environ', {'CODEBREAK_TUTOR_URL':'https://tutor.example/ask'})
    def test_broad_questions_try_live_ai_first(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'answer':'A live explanation.'}).encode()
        with patch('src.systems.ai_tutor.request.urlopen', return_value=response) as send:
            self.assertEqual(ask_mang_tahimik('please explain while loops'), 'A live explanation.')
            send.assert_called_once()

    @patch.dict('os.environ', {'CODEBREAK_TUTOR_URL':'https://tutor.example/ask'})
    def test_no_internet_uses_knowledge_instead_of_bare_error(self):
        with patch('src.systems.ai_tutor.request.urlopen', side_effect=URLError('private connection detail')):
            answer = ask_mang_tahimik('please explain while loops')
        self.assertTrue(answer.startswith('Built-in guide:'))
        self.assertIn('eventually', answer)
        self.assertNotIn('private', answer)

    @patch.dict('os.environ', {'CODEBREAK_TUTOR_URL':'https://tutor.example/ask'})
    def test_outage_quota_and_bad_reply_use_same_local_backup(self):
        for status in (429,503):
            failure = HTTPError('url',status,'private',{},BytesIO(b'{"code":"gemini_timeout"}'))
            with patch('src.systems.ai_tutor.request.urlopen', side_effect=failure):
                self.assertIn('Built-in guide:', ask_mang_tahimik('tell me about for loops'))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{}'
        with patch('src.systems.ai_tutor.request.urlopen', return_value=response):
            self.assertIn('Built-in guide:', ask_mang_tahimik('tell me about for loops'))

    @patch.dict('os.environ', {'CODEBREAK_TUTOR_MODE':'offline'}, clear=True)
    def test_defence_rehearsal_requires_no_server_or_key(self):
        with patch('src.systems.ai_tutor.request.urlopen') as send:
            self.assertIn('Built-in guide:', ask_mang_tahimik('explain nested loops'))
            self.assertIn('do not have a reliable saved answer', ask_mang_tahimik('predict tomorrow’s weather'))
            send.assert_not_called()

    def test_slow_live_request_shows_reference_then_live_reply(self):
        session = TutorSession(lambda *args: 'unused')
        session.pending = True
        session.last_sent = 100
        session._backup = offline_answer('explain while loops')
        with patch('src.systems.ai_tutor.time.monotonic', return_value=107):
            self.assertIsNone(session.poll())
        with patch('src.systems.ai_tutor.time.monotonic', return_value=108):
            self.assertEqual(session.poll(), session._backup)
            self.assertIsNone(session.poll())
        self.assertTrue(session.pending)
        session.results.put(('explain while loops', 'Here is the live explanation.', True))
        self.assertEqual(session.poll(), 'Live AI: Here is the live explanation.')
        self.assertFalse(session.pending)
        self.assertEqual(session.history[-1]['content'], 'Here is the live explanation.')

    def test_slow_failure_does_not_duplicate_reference(self):
        session = TutorSession()
        session.pending = True
        session._backup = offline_answer('explain while loops')
        session._backup_shown = True
        session.results.put(('explain while loops', session._backup, True))
        self.assertIsNone(session.poll())
        self.assertFalse(session.pending)
        self.assertEqual(len(session.history),2)


class RecoveryTests(unittest.TestCase):
    def test_saved_game_intent_is_not_python_continue(self):
        answer = offline_answer('how do i continue my saved game')
        self.assertIn('save slot', answer)
        self.assertNotIn('enclosing loop', answer)

    def test_detached_result_cannot_overwrite_new_question(self):
        import threading
        started, release, finished = threading.Event(), threading.Event(), threading.Event()
        def slow(*args):
            started.set()
            release.wait(2)
            finished.set()
            return 'late generated answer'
        session = TutorSession(slow)
        try:
            self.assertTrue(session.submit('explain while loops'))
            self.assertTrue(started.wait(1))
            answer = session.use_guide()
            self.assertTrue(answer.startswith('Built-in guide:'))
            self.assertFalse(session.pending)
            session.last_sent = float('-inf')
            self.assertTrue(session.submit('explain dictionaries'))
            self.assertIn('dictionary', session.poll())
            self.assertFalse(session.pending)
        finally:
            release.set()
            session._worker.join(2)
        self.assertTrue(finished.is_set())
        self.assertIsNone(session.poll())
        self.assertNotIn('late generated answer', str(session.history))
