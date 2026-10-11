import asyncio
import json
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from server.app import create_app, Limits


class ServerTests(unittest.TestCase):
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
