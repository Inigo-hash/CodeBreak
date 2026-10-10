"""Public Gemini tutor relay, intended for a single-worker school prototype."""
import asyncio
import os
import re
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from server.tutor_prompt import SYSTEM_PROMPT

MAX_BODY = 40000


class Turn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    question: str = Field(min_length=1, max_length=1000)
    context: dict[str, str] = Field(default_factory=dict, max_length=3)
    history: list[Turn] = Field(default_factory=list, max_length=8)


class Limits:
    """Atomic global/minute/day + IP minute limits; restarts reset counters."""
    def __init__(self, per_ip=3, per_minute=8, per_day=100):
        self.per_ip, self.per_minute, self.per_day = per_ip, per_minute, per_day
        self.recent = deque()
        self.day = None
        self.count = 0
        self.lock = asyncio.Lock()

    async def allow(self, ip, now=None):
        now = time.time() if now is None else now
        async with self.lock:
            day = int(now // 86400)
            if self.day != day:
                self.day, self.count = day, 0
            while self.recent and self.recent[0][0] <= now - 60:
                self.recent.popleft()
            if (self.count >= self.per_day or len(self.recent) >= self.per_minute
                    or sum(address == ip for _, address in self.recent) >= self.per_ip):
                return False
            self.recent.append((now, ip))
            self.count += 1
            return True


def positive_setting(name, default):
    value = int(os.environ.get(name, default))
    if value <= 0:
        raise ValueError(name + ' must be positive')
    return value


def create_app():
    limits = Limits(positive_setting('TUTOR_IP_PER_MINUTE', 3),
                    positive_setting('TUTOR_GLOBAL_PER_MINUTE', 8),
                    positive_setting('TUTOR_GLOBAL_PER_DAY', 100))
    busy = asyncio.Semaphore(2)

    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(timeout=25, follow_redirects=False) as client:
            app.state.http = client
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def bound_body(request, call_next):
        # Count actual streamed bytes, not only the client-provided length.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_BODY:
                return JSONResponse({'error': 'Request is too large.'}, status_code=413)
        request._body = bytes(body)
        return await call_next(request)

    @app.exception_handler(Exception)
    async def safe_failure(request, exc):
        return JSONResponse({'error': 'The tutor is temporarily unavailable.'}, status_code=503)

    @app.get('/health')
    async def health():
        # Host liveness only; deliberately reveals no settings or secrets.
        return {'status': 'ok'}

    @app.post('/ask')
    async def ask(question: Question, request: Request):
        key = os.environ.get('GEMINI_API_KEY', '').strip()
        model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite').strip()
        if not key or not re.fullmatch(r'[a-zA-Z0-9._-]+', model):
            return JSONResponse({'error': 'The tutor is not configured.'}, status_code=503)
        if not question.question.strip():
            return JSONResponse({'error': 'Please ask a question.'}, status_code=422)
        if any(k not in ('stage', 'room', 'topic') or len(v) > 100
               for k, v in question.context.items()):
            return JSONResponse({'error': 'Invalid level context.'}, status_code=422)
        # Uvicorn/proxy owns request.client. Do not trust raw forwarded headers.
        ip = request.client.host if request.client else 'unknown'
        if busy.locked():
            return JSONResponse({'error': 'The tutor is busy.'}, status_code=429,
                                headers={'Retry-After': '30'})
        async with busy:
            if not await limits.allow(ip):
                return JSONResponse({'error': 'Tutor usage limit reached.'}, status_code=429,
                                    headers={'Retry-After': '60'})
            contents = [{'role': 'model' if t.role == 'assistant' else 'user',
                         'parts': [{'text': t.content}]} for t in question.history]
            import json
            contents.append({'role': 'user', 'parts': [{'text': json.dumps({
                'question': question.question, 'level_context': question.context})}]})
            payload = {'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                       'contents': contents,
                       'generationConfig': {'maxOutputTokens': 600}}
            try:
                response = await app.state.http.post(
                    'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent',
                    headers={'x-goog-api-key': key}, json=payload)
                if response.status_code == 429:
                    return JSONResponse({'error': 'Gemini quota reached.'}, status_code=429,
                                        headers={'Retry-After': '60'})
                if response.status_code != 200:
                    return JSONResponse({'error': 'The tutor is temporarily unavailable.',
                                         'code': 'gemini_http_' + str(response.status_code)}, status_code=503)
                result = response.json()
                answer = '\n'.join(p['text'] for p in result['candidates'][0]['content']['parts']
                                   if isinstance(p.get('text'), str) and not p.get('thought'))
                if not answer.strip():
                    raise ValueError('No answer')
                return {'answer': answer.strip()[:4000]}
            except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
                return JSONResponse({'error': 'The tutor could not answer. Please try later.'}, status_code=503)

    return app


app = create_app()
