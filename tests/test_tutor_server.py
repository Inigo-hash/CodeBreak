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
    def assert_saved_reply(self, response, reason):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], reason)
        self.assertEqual(response.headers['x-tutor-source'], 'offline_guide')
        self.assertTrue(response.json()['answer'].startswith(('Built-in guide:', 'Offline guide:')))
        self.assertNotIn('wait', response.json()['answer'].lower())

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
            self.assertEqual([s['name'] for s in facts['stages']], ['Island', 'Castle', 'Citadel'])
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
        self.assert_saved_reply(client.post('/ask', json={'question':'again?'}), 'tutor_daily_limit')
        self.assertEqual(len(calls), 1)

    @patch.dict('os.environ', {}, clear=True)
    def test_missing_key_and_health(self):
        client = self.make_client(lambda req: self.fail('called without key'))
        for path in ('/', '/health'):
            self.assertEqual(client.get(path).json(), {'status':'ok'})
            self.assertEqual(client.get(path).headers['x-tutor-revision'], 'citadel-campaign-20261026')
            response = client.head(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'')
        self.assertEqual(client.post('/ask', json={'question':'help'}).status_code, 503)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_upstream_quota_and_malformed_reply(self):
        for reply in (httpx.Response(429), httpx.Response(200, json={})):
            client = self.make_client(lambda req: reply)
            result = client.post('/ask', json={'question':'help'})
            if reply.status_code == 429:
                self.assert_saved_reply(result, 'gemini_quota')
            else:
                self.assertEqual(result.status_code, 503)
            self.assertNotIn('test-secret', result.text)

    def test_game_knowledge_excludes_challenge_answers_and_map_internals(self):
        challenge = dict(CHALLENGES['variables_001'], expected='secret-test-answer',
                         runtime_expected={'answer': 'secret-test-answer'})
        with patch.dict(CHALLENGES, {'variables_001': challenge}):
            facts = game_knowledge()
        serialized = json.dumps(facts)
        self.assertNotIn('secret-test-answer', serialized)
        self.assertNotIn('assets/map/', serialized)
        self.assertEqual(facts['stage_count'], 3)
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

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_IP_PER_MINUTE': '3'}, clear=True)
    def test_existing_render_default_allows_followups_until_shared_budget(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': 'live hint'}]}}]})
        client = self.make_client(handler)
        for _ in range(8):
            response = client.post('/ask', json={'question': 'explain for loops', 'client_id': 'a'*32})
            self.assertEqual(response.json()['answer'], 'live hint')
            self.assertEqual(response.headers['x-tutor-source'], 'live_ai')
        # The ninth question still gets help, without a ninth provider call.
        response = client.post('/ask', json={'question': 'explain for loops', 'client_id': 'a'*32})
        self.assert_saved_reply(response, 'tutor_minute_limit')
        self.assertIn('range', response.json()['answer'])
        self.assertEqual(len(calls), 8)

    def test_explicit_session_setting_overrides_legacy_migration(self):
        from server.app import session_limit_setting
        for settings, expected in (({}, 0), ({'TUTOR_IP_PER_MINUTE': '3'}, 0),
                ({'TUTOR_IP_PER_MINUTE': '1'}, 1),
                ({'TUTOR_IP_PER_MINUTE': '3', 'TUTOR_SESSION_PER_MINUTE': '3'}, 3),
                ({'TUTOR_IP_PER_MINUTE': '1', 'TUTOR_SESSION_PER_MINUTE': '0'}, 0)):
            with self.subTest(settings=settings), patch.dict('os.environ', settings, clear=True):
                self.assertEqual(session_limit_setting(), expected)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_GLOBAL_PER_DAY': '1'}, clear=True)
    def test_daily_budget_still_serves_saved_knowledge_for_legacy_clients(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': 'live hint'}]}}]})
        client = self.make_client(handler)
        client.post('/ask', json={'question': 'inspect my program'})
        reply = client.post('/ask', json={'question': 'explain while loops'})
        self.assert_saved_reply(reply, 'tutor_daily_limit')
        self.assertIn('eventually', reply.json()['answer'])
        self.assertEqual(len(calls), 1)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_two_inflight_calls_give_third_player_saved_help_without_queueing(self):
        async def check():
            app = create_app()
            both_started, release = asyncio.Event(), asyncio.Event()
            calls = []
            async def handler(req):
                calls.append(req)
                if len(calls) == 2:
                    both_started.set()
                await release.wait()
                return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': 'live hint'}]}}]})
            async with app.router.lifespan_context(app), httpx.AsyncClient(
                    transport=httpx.MockTransport(handler)) as provider:
                app.state.http = provider
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://test') as client:
                    jobs = [asyncio.create_task(client.post('/ask', json={'question': 'help'})) for _ in range(2)]
                    try:
                        await asyncio.wait_for(both_started.wait(), timeout=2)
                        reply = await asyncio.wait_for(client.post('/ask', json={'question': 'explain lists'}), timeout=2)
                        self.assert_saved_reply(reply, 'tutor_busy')
                        self.assertIn('list', reply.json()['answer'].lower())
                        self.assertEqual(len(calls), 2)
                    finally:
                        release.set()
                        await asyncio.gather(*jobs)
        asyncio.run(check())

    def test_dining_facts_are_authored_without_function_answers(self):
        facts = game_knowledge()
        castle = next(stage for stage in facts['stages'] if stage['name'] == 'Castle')
        self.assertEqual(castle['gate']['keys_required'], 5)
        self.assertIn('eleven challenges', castle['summary'])
        self.assertEqual(len(castle['learning_content']), 5)
        self.assertEqual(sum(len(topic['challenges']) for topic in castle['learning_content']), 11)
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
        self.assertIn('/gemini-3.5-flash-lite:generateContent', str(calls[0].url))
        self.assertIn('/gemini-3.1-flash-lite:generateContent', str(calls[1].url))
        wait.assert_awaited_once_with(1)
        self.assert_saved_reply(client.post('/ask', json={'question': 'again?'}), 'tutor_daily_limit')
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
                if status == 429:
                    self.assert_saved_reply(response, 'gemini_quota')
                else:
                    self.assertEqual(response.status_code, 503)
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
            response = client.post('/ask',json={'question':'why does my movement code fail?'})
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
        self.assert_saved_reply(limited, 'tutor_session_limit')
        self.assertTrue(1 <= limited.json()['retry_after'] <= 60)
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
        self.assert_saved_reply(response, 'tutor_minute_limit')

    @patch.dict('os.environ', {'GEMINI_API_KEY':'test-secret','TUTOR_IP_PER_MINUTE':'1'}, clear=True)
    def test_legacy_clients_share_global_budget_without_single_peer_bucket(self):
        client=self.make_client(lambda req:httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'hint'}]}}]}))
        for _ in range(3):
            self.assertEqual(client.post('/ask',json={'question':'help'}).status_code,200)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_primary_timeout_reaches_backup_and_recovers(self):
        calls = []
        def handler(req):
            calls.append(req)
            if len(calls) == 1:
                raise httpx.ReadTimeout('private upstream details', request=req)
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': 'Try tracing each iteration.'}]}}]})
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = client.post('/ask', json={'question': 'why does my loop repeat forever?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['answer'], 'Try tracing each iteration.')
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(calls[0].url, calls[1].url)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_per_attempt_deadline_leaves_room_for_backup(self):
        calls = []
        async def handler(req):
            calls.append(req)
            if len(calls) == 1:
                await asyncio.sleep(1)
            return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': 'Check your condition.'}]}}]})
        client = self.make_client(handler)
        with patch('server.app.PROVIDER_ATTEMPT_TIMEOUT', 0.01):
            response = client.post('/ask', json={'question': 'why does my loop never stop?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 2)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_GLOBAL_PER_DAY': '1'}, clear=True)
    def test_timeout_retry_cannot_exceed_budget(self):
        calls = []
        def handler(req):
            calls.append(req)
            raise httpx.ReadTimeout('test-secret', request=req)
        client = self.make_client(handler)
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = client.post('/ask', json={'question': 'why does this loop not stop?'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'gemini_timeout')
        self.assertNotIn('test-secret', response.text)
        self.assertEqual(len(calls), 1)

    @patch.dict('os.environ', {}, clear=True)
    def test_basic_guide_works_without_provider_and_is_labelled(self):
        client = self.make_client(lambda req: self.fail('guide must not call Gemini'))
        for question in ('who is python', 'what is python', 'how do i play codebreak'):
            response = client.post('/ask', json={'question': question})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['source'], 'built_in')
            self.assertTrue(response.json()['answer'].startswith('Built-in guide: '))
        # The guide must not bypass validation or become an arbitrary answer.
        self.assertEqual(client.post('/ask', json={'question': 'what is python', 'context': {'secret': 'x'}}).status_code, 422)
        self.assertEqual(client.post('/ask', json={'question': 'solve my complete challenge'}).status_code, 503)

    @patch.dict('os.environ', {}, clear=True)
    def test_screenshot_answer_requires_no_graphics_or_desktop_configuration(self):
        import sys
        client = self.make_client(lambda req: self.fail('saved answer reached provider'))
        with patch.dict(sys.modules, {'pygame': None, 'src.config': None}):
            response = client.post('/ask', json={'question': 'how to cheat'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['source'], 'built_in')
        self.assertIn('with developer controls enabled', response.json()['answer'])
        self.assertNotIn('wait', response.json()['answer'].lower())

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_current_primary_uses_minimal_thinking_and_marks_generated_reply(self):
        calls = []
        def handler(req):
            calls.append(req)
            self.assertIn('/gemini-3.5-flash-lite:generateContent', str(req.url))
            body = json.loads(req.content)
            self.assertEqual(body['generationConfig']['thinkingConfig'], {'thinkingLevel':'minimal'})
            return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'A generated hint.'}]}}]})
        response = self.make_client(handler).post('/ask',json={'question':'why does this expression fail?'})
        self.assertEqual(response.headers['x-tutor-source'],'live_ai')
        self.assertEqual(response.headers['x-tutor-route'],'primary')
        self.assertEqual(len(calls),1)

    @patch.dict('os.environ', {'GEMINI_API_KEY':'test-secret','GEMINI_MODEL':'custom-model','GEMINI_FALLBACK_MODEL':''}, clear=True)
    def test_custom_model_and_disabled_backup_are_preserved(self):
        def handler(req):
            self.assertIn('/custom-model:generateContent',str(req.url))
            self.assertNotIn('thinkingConfig',json.loads(req.content)['generationConfig'])
            return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'hint'}]}}]})
        self.assertEqual(self.make_client(handler).post('/ask',json={'question':'help'}).status_code,200)

    def test_existing_blueprints_migrate_both_model_slots_and_keep_custom_choices(self):
        from server.app import configured_models
        for pair in (('gemini-3.1-flash-lite', 'gemini-2.5-flash-lite'),
                     ('gemini-2.5-flash-lite', 'gemini-3.1-flash-lite'),
                     ('gemini-2.5-flash-lite', 'gemini-2.5-flash')):
            with self.subTest(pair=pair), patch.dict('os.environ', {
                    'GEMINI_MODEL': pair[0], 'GEMINI_FALLBACK_MODEL': pair[1]}, clear=True):
                self.assertEqual(configured_models(), ('gemini-3.5-flash-lite', 'gemini-3.1-flash-lite'))
        for pair in (('gemini-3.1-flash-lite', ''), ('custom-model', 'custom-backup')):
            with self.subTest(pair=pair), patch.dict('os.environ', {
                    'GEMINI_MODEL': pair[0], 'GEMINI_FALLBACK_MODEL': pair[1]}, clear=True):
                self.assertEqual(configured_models(), pair)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret'}, clear=True)
    def test_empty_or_malformed_primary_reply_can_recover_through_backup(self):
        from unittest.mock import AsyncMock
        for bad in ({}, {'candidates': []}, {'candidates': [{'content': {'parts': [{'thought': True, 'text': 'private'}]}}]},
                    {'candidates': [{'content': {'parts': [None, {'text': '  '}]}}]}):
            calls = []
            def handler(req):
                calls.append(req)
                return httpx.Response(200, json=bad if len(calls) == 1 else {
                    'candidates': [{'content': {'parts': [{'text': 'A recovered live hint.'}]}}]})
            with self.subTest(bad=bad), patch('server.app.asyncio.sleep', new_callable=AsyncMock):
                response = self.make_client(handler).post('/ask', json={'question': 'help'})
            self.assertEqual(response.json(), {'answer': 'A recovered live hint.'})
            self.assertEqual(response.headers['x-tutor-source'], 'live_ai')
            self.assertEqual(response.headers['x-tutor-route'], 'backup')
            self.assertEqual(len(calls), 2)

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-secret', 'TUTOR_GLOBAL_PER_DAY': '1'}, clear=True)
    def test_invalid_reply_recovery_cannot_bypass_attempt_budget(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(200, json={})
        from unittest.mock import AsyncMock
        with patch('server.app.asyncio.sleep', new_callable=AsyncMock):
            response = self.make_client(handler).post('/ask', json={'question': 'help'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'gemini_invalid_reply')
        self.assertEqual(len(calls), 1)
