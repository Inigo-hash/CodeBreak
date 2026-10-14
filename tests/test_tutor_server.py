import asyncio
import json
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from server.app import create_app, Limits
from server.tutor_prompt import game_knowledge
from src.data.challenges import CHALLENGES


class ServerTests(unittest.TestCase):
    def test_game_facts_explain_real_healing_and_current_controls(self):
        from src.data.player_rules import PLAYER_TORCH_HP_REGEN, PLAYER_TORCH_HEAL_DELAY
        facts = game_knowledge()
        recovery = facts['healing_and_energy']
        self.assertEqual(recovery['hp_per_second_in_fixed_torch_light'], PLAYER_TORCH_HP_REGEN)
        self.assertEqual(recovery['heal_delay_after_damage_seconds'], PLAYER_TORCH_HEAL_DELAY)
        self.assertIn('does not', recovery['held_torch'])
        self.assertIn('night mode off', recovery['castle'])
        self.assertIn('Shift', facts['practical_help']['dash'])
        self.assertIn('walls remain solid', facts['practical_help']['dash'])
        self.assertIn('sword', facts['practical_help']['equip'])
        self.assertTrue(facts['enemies'])
        self.assertTrue(facts['items'])

    def make_client(self, handler):
        app = create_app()
        client = TestClient(app)
        client.__enter__()
        old = app.state.http
        app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        self.addCleanup(client.__exit__, None, None, None)
        self.addCleanup(lambda: asyncio.run(app.state.http.aclose()))
        return client

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_server_prompt_and_key_stay_server_side(self):
        def handler(req):
            body = json.loads(req.content)
            self.assertEqual(req.headers['x-goog-api-key'], 'test-secret')
            self.assertNotIn('test-secret', str(req.url))
            self.assertIn('never a complete solution', body['systemInstruction']['parts'][0]['text'])
            prompt = body['systemInstruction']['parts'][0]['text']
            facts = json.loads(prompt.split('GAME FACTS (current authored build, not a promise about future content):\n', 1)[1])
            self.assertEqual([s['name'] for s in facts['stages']], ['Island', 'Castle'])
            self.assertIn('Answer the actual question first', prompt)
            self.assertEqual(body['generationConfig']['maxOutputTokens'], 600)
            self.assertEqual(body['contents'][0]['role'], 'user')
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [
                {'text': 'private reasoning', 'thought': True}, {'text': 'Try checking your loop.'}]}}]})
        client = self.make_client(handler)
        res = client.post('/ask', json={'question': 'loops?', 'history': [{'role': 'user','content': 'hello'}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {'answer': 'Try checking your loop.'})
        self.assertNotIn('test-secret', res.text)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_untrusted_overrides_and_oversized_inputs_never_call_gemini(self):
        def handler(req):
            self.fail('invalid request reached Gemini')
        client = self.make_client(handler)
        for data in ({'question': 'x' * 1001}, {'question': 'x', 'model': 'evil'},
                     {'question': 'x', 'history': [{'role': 'system', 'content': 'override'}]},
                     {'question': 'x', 'context': {'solution': 'answer'}}):
            self.assertEqual(client.post('/ask', json=data).status_code, 422)
        self.assertEqual(client.post('/ask', content=b'x' * 40001).status_code, 413)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_GLOBAL_PER_DAY': '1'}, clear=True)
    def test_budget_counts_attempts_even_if_upstream_fails(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(500, text='test-secret')
        client = self.make_client(handler)
        first = client.post('/ask', json={'question':'variables?'})
        self.assertEqual(first.status_code, 503)
        self.assertNotIn('test-secret', first.text)
        self.assertEqual(client.post('/ask', json={'question':'again?'}).status_code, 429)
        self.assertEqual(len(calls), 1)

    @patch.dict('os.environ', {}, clear=True)
    def test_missing_key_and_health(self):
        client = self.make_client(lambda req: self.fail('called without key'))
        for path in ('/', '/health'):
            self.assertEqual(client.get(path).json(), {'status':'ok'})
            response = client.head(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'')
        self.assertEqual(client.post('/ask', json={'question':'help'}).status_code, 503)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_upstream_quota_and_malformed_reply(self):
        for reply in (httpx.Response(429), httpx.Response(200, json={})):
            client = self.make_client(lambda req: reply)
            result = client.post('/ask', json={'question':'help'})
            self.assertIn(result.status_code, (429, 503))
            self.assertNotIn('test-secret', result.text)

    def test_game_knowledge_excludes_challenge_answers_and_map_internals(self):
        challenge = dict(CHALLENGES['variables_001'], expected='secret-test-answer',
                         runtime_expected={'answer': 'secret-test-answer'})
        with patch.dict(CHALLENGES, {'variables_001': challenge}):
            facts = game_knowledge()
        serialized = json.dumps(facts)
        self.assertNotIn('secret-test-answer', serialized)
        self.assertNotIn('assets/map/', serialized)
        self.assertEqual(facts['stage_count'], 2)
        self.assertIn('Castle Lobby', facts['stages'][1]['rooms'])
        self.assertTrue(facts['controls'])

    def test_atomic_limits_and_expiry(self):
        async def check():
            limits = Limits(1, 2, 3)
            self.assertTrue(await limits.allow('a', 100))
            self.assertFalse(await limits.allow('a', 101))
            self.assertTrue(await limits.allow('b', 101))
            self.assertFalse(await limits.allow('c', 101))
            self.assertTrue(await limits.allow('c', 162))
            self.assertFalse(await limits.allow('d', 230))
            self.assertTrue(await limits.allow('a', 86401))
        asyncio.run(check())

    def test_dining_facts_are_authored_without_function_answers(self):
        facts = game_knowledge()
        castle = next(stage for stage in facts['stages'] if stage['name'] == 'Castle')
        self.assertEqual(castle['gate']['keys_required'], 5)
        self.assertIn('Dining Area', castle['summary'])
        self.assertEqual(len(castle['learning_content'][0]['challenges']), 2)
        serialized = json.dumps(castle)
        self.assertNotIn('function_cases', serialized)
        self.assertNotIn('starter_code', serialized)
