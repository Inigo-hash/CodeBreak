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
            self.assertEqual(client.get(path).headers['x-tutor-revision'], 'session-limits-20261019')
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

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_GLOBAL_PER_DAY': '2'}, clear=True)
    def test_temporary_failure_retries_once_and_consumes_attempt_budget(self):
        calls = []
        def handler(req):
            calls.append(req)
            if len(calls) == 1:
                return httpx.Response(503, text='test-secret')
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': 'Use WASD to move.'}]}}]})
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock) as wait:
            response = client.post('/ask', json={'question': 'how to play?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['answer'], 'Use WASD to move.')
        self.assertEqual(len(calls), 2)
        self.assertIn('/gemini-2.5-flash-lite:generateContent', str(calls[0].url))
        self.assertIn('/gemini-3.1-flash-lite:generateContent', str(calls[1].url))
        wait.assert_awaited_once_with(1)
        self.assertEqual(client.post('/ask', json={'question': 'again?'}).status_code, 429)
        self.assertEqual(len(calls), 2)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_persistent_provider_outage_is_bounded_and_safe(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(503, text='test-secret provider internals')
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = client.post('/ask', json={'question': 'how to play?'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'gemini_http_503')
        self.assertEqual(len(calls), 2)
        self.assertNotIn('test-secret', response.text)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'GEMINI_FALLBACK_MODEL': ''}, clear=True)
    def test_quota_auth_and_model_errors_are_not_retried(self):
        for status in (400, 401, 403, 404, 429):
            with self.subTest(status=status):
                calls = []
                def handler(req):
                    calls.append(req)
                    return httpx.Response(status, text='test-secret')
                client = self.make_client(handler)
                response = client.post('/ask', json={'question': 'help'})
                self.assertEqual(len(calls), 1)
                self.assertEqual(response.status_code, 429 if status == 429 else 503)
                self.assertNotIn('test-secret', response.text)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_GLOBAL_PER_DAY': '1'}, clear=True)
    def test_retry_does_not_bypass_one_attempt_budget(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(503)
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = client.post('/ask', json={'question': 'help'})
        self.assertEqual(response.json()['code'], 'gemini_http_503')
        self.assertEqual(len(calls), 1)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_provider_operation_has_total_deadline(self):
        async def handler(req):
            await asyncio.sleep(1)
            self.fail('request should have been cancelled')
        client = self.make_client(handler)
        with patch('server.app.PROVIDER_DEADLINE', 0.01):
            response = client.post('/ask', json={'question': 'help'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'gemini_timeout')

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'GEMINI_FALLBACK_MODEL': ''}, clear=True)
    def test_backup_can_be_disabled_without_removing_retry(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(503)
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = client.post('/ask', json={'question': 'help'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].url, calls[1].url)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'GEMINI_FALLBACK_MODEL': 'bad/model'}, clear=True)
    def test_invalid_backup_never_sends_credentials(self):
        client = self.make_client(lambda req: self.fail('invalid backup reached provider'))
        response = client.post('/ask', json={'question': 'help'})
        self.assertEqual(response.json()['code'], 'tutor_not_configured')

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret',
                            'GEMINI_MODEL': 'gemini-2.5-flash-lite',
                            'GEMINI_FALLBACK_MODEL': 'gemini-2.5-flash'}, clear=True)
    def test_missing_model_recovers_with_current_backup_even_with_legacy_env(self):
        calls = []
        def handler(req):
            calls.append(req)
            if len(calls) == 1:
                return httpx.Response(404)
            self.assertIn('/gemini-3.1-flash-lite:generateContent', str(req.url))
            return httpx.Response(200, json={'candidates':[{'content':{'parts':[{'text':'Use WASD.'}]}}]})
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = client.post('/ask',json={'question':'how do I move?'})
        self.assertEqual(response.json(),{'answer':'Use WASD.'})
        self.assertEqual(len(calls),2)

    @patch.dict('os.environ', {'GEMINI_API_KEY':'test-secret', 'TUTOR_IP_PER_MINUTE':'1'}, clear=True)
    def test_sessions_on_same_network_have_separate_question_allowances(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'hint'}]}}]})
        client = self.make_client(handler)
        def ask(identity):
            return client.post('/ask',json={'question':'help','client_id':identity * 32})
        self.assertEqual(ask('a').status_code,200)
        limited = ask('a')
        self.assertEqual(limited.status_code,429)
        self.assertEqual(limited.json()['code'],'tutor_session_limit')
        self.assertTrue(1 <= int(limited.headers['retry-after']) <= 60)
        self.assertEqual(ask('b').status_code,200)
        self.assertEqual(len(calls),2)

    def test_retry_uses_provider_budget_but_not_another_question_allowance(self):
        async def check():
            limits = Limits(2,4,10)
            self.assertTrue((await limits.reserve('a',now=100))[0])
            self.assertTrue((await limits.reserve('a',retry=True,now=101))[0])
            self.assertTrue((await limits.reserve('a',now=102))[0])
            self.assertEqual((await limits.reserve('a',now=103))[1],'tutor_session_limit')
            self.assertTrue((await limits.reserve('b',now=104))[0])
            self.assertEqual((await limits.reserve('c',now=105))[1],'tutor_minute_limit')
            daily = Limits(10,10,1)
            self.assertTrue((await daily.reserve('a',now=100))[0])
            result = await daily.reserve('b',now=101)
            self.assertEqual(result[1],'tutor_daily_limit')
            self.assertEqual(result[2],86400-101+1)
        asyncio.run(check())

    @patch.dict('os.environ', {'GEMINI_API_KEY':'test-secret'}, clear=True)
    def test_primary_quota_can_use_distinct_backup_within_same_budget(self):
        calls = []
        def handler(req):
            calls.append(req)
            if len(calls)==1:return httpx.Response(429)
            self.assertNotEqual(calls[0].url,req.url)
            return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'hint'}]}}]})
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep',new_callable=AsyncMock):
            response = client.post('/ask',json={'question':'help'})
        self.assertEqual(response.json(),{'answer':'hint'})
        self.assertEqual(len(calls),2)

    @patch.dict('os.environ', {'GEMINI_API_KEY':'test-secret','TUTOR_GLOBAL_PER_MINUTE':'1'}, clear=True)
    def test_rotating_session_tokens_cannot_bypass_shared_budget(self):
        client = self.make_client(lambda req:httpx.Response(500))
        self.assertEqual(client.post('/ask',json={'question':'help','client_id':'a'*32}).status_code,503)
        response = client.post('/ask',json={'question':'help','client_id':'b'*32})
        self.assertEqual(response.status_code,429)
        self.assertEqual(response.json()['code'],'tutor_minute_limit')

    @patch.dict('os.environ', {'GEMINI_API_KEY':'test-secret','TUTOR_IP_PER_MINUTE':'1'}, clear=True)
    def test_legacy_clients_share_global_budget_without_single_peer_bucket(self):
        client=self.make_client(lambda req:httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'hint'}]}}]}))
        for _ in range(3):
            self.assertEqual(client.post('/ask',json={'question':'help'}).status_code,200)
