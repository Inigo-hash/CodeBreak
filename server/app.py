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
from src.systems.tutor_guide import built_in_answer, limited_answer

MAX_BODY = 40000
RETRYABLE_STATUS = frozenset((502, 503, 504))
MAX_PROVIDER_ATTEMPTS = 2
PROVIDER_DEADLINE = 55
PROVIDER_ATTEMPT_TIMEOUT = 20
TUTOR_REVISION = 'live-recovery-20261026'
DEFAULT_MODEL = 'gemini-3.5-flash-lite'
DEFAULT_BACKUP = 'gemini-3.1-flash-lite'


def configured_models():
    model = os.environ.get('GEMINI_MODEL', DEFAULT_MODEL).strip()
    if model == 'gemini-2.5-flash-lite' and 'GEMINI_FALLBACK_MODEL' not in os.environ:
        return DEFAULT_MODEL, DEFAULT_BACKUP
    fallback = os.environ.get('GEMINI_FALLBACK_MODEL',
                              DEFAULT_BACKUP if model == DEFAULT_MODEL else
                              DEFAULT_MODEL if model in ('gemini-3.1-flash-lite', 'gemini-2.5-flash-lite')
                              else '').strip()
    # A deploy does not replace existing Render environment values. Upgrade
    # the exact pairs shipped by earlier blueprints, including their 404ing
    # 2.5 backup. Explicit custom models and disabled backups stay deliberate.
    legacy_pairs = {
        ('gemini-2.5-flash-lite', 'gemini-2.5-flash'),
        ('gemini-2.5-flash-lite', 'gemini-3.1-flash-lite'),
        ('gemini-3.1-flash-lite', 'gemini-2.5-flash-lite'),
    }
    if (model, fallback) in legacy_pairs:
        return DEFAULT_MODEL, DEFAULT_BACKUP
    return model, fallback


def provider_answer(response):
    """Only a nonempty final text answer completes a provider attempt."""
    try:
        parts = response.json()['candidates'][0]['content']['parts']
        if not isinstance(parts, list):
            raise ValueError('Invalid parts')
        answer = '\n'.join(part['text'] for part in parts
                           if isinstance(part, dict) and isinstance(part.get('text'), str)
                           and not part.get('thought')).strip()
        if answer:
            return answer[:4000]
    except (ValueError, KeyError, IndexError, TypeError):
        pass
    raise ValueError('No usable answer')


class Turn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    question: str = Field(min_length=1, max_length=1000)
    context: dict[str, str] = Field(default_factory=dict, max_length=3)
    history: list[Turn] = Field(default_factory=list, max_length=8)
    client_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')


class Limits:
    """Atomic provider budgets and optional session cap; restarts reset counters."""
    def __init__(self, per_ip=0, per_minute=8, per_day=100):
        self.per_ip, self.per_minute, self.per_day = per_ip, per_minute, per_day
        self.recent = deque()
        self.questions = deque()
        self.day = None
        self.count = 0
        self.lock = asyncio.Lock()

    async def allow(self, ip, now=None):
        return (await self.reserve(ip, now=now))[0]

    async def reserve(self, client, *, retry=False, now=None):
        now = time.time() if now is None else now
        async with self.lock:
            day = int(now // 86400)
            if self.day != day:
                self.day, self.count = day, 0
            while self.recent and self.recent[0][0] <= now - 60:
                self.recent.popleft()
            while self.questions and self.questions[0][0] <= now - 60:
                self.questions.popleft()
            if self.count >= self.per_day:
                return False, 'tutor_daily_limit', max(1, int((day + 1) * 86400 - now) + 1)
            if len(self.recent) >= self.per_minute:
                return False, 'tutor_minute_limit', max(1, int(self.recent[0][0] + 60 - now) + 1)
            own = [when for when, identity in self.questions if identity == client]
            if self.per_ip and not retry and len(own) >= self.per_ip:
                return False, 'tutor_session_limit', max(1, int(own[0] + 60 - now) + 1)
            self.recent.append((now, client))
            if not retry:
                self.questions.append((now, client))
            self.count += 1
            return True, None, 0


def positive_setting(name, default):
    value = int(os.environ.get(name, default))
    if value <= 0:
        raise ValueError(name + ' must be positive')
    return value


def session_limit_setting():
    # Existing Render services retain the old blueprint's value of 3 even
    # after a code deploy. Migrate that shipped default; retain custom caps.
    configured = os.environ.get('TUTOR_SESSION_PER_MINUTE')
    if configured is None:
        configured = os.environ.get('TUTOR_IP_PER_MINUTE', '0')
        if configured == '3':
            configured = '0'
    value = int(configured)
    if value < 0:
        raise ValueError('TUTOR_SESSION_PER_MINUTE must be nonnegative')
    return value


def create_app():
    limits = Limits(session_limit_setting(),
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
        # Liveness probes must not wait for a request body or call Gemini.
        if request.method in ('GET', 'HEAD') and request.url.path in ('/', '/health'):
            return await call_next(request)
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

    @app.api_route('/', methods=['GET', 'HEAD'])
    @app.api_route('/health', methods=['GET', 'HEAD'])
    async def health():
        # Host liveness only; deliberately reveals no settings or secrets.
        return JSONResponse({'status': 'ok'}, headers={'X-Tutor-Revision': TUTOR_REVISION})

    def saved_help(question, reason, retry_after):
        # A completed, labelled reference reply works in older game clients
        # too. Provider calls remain blocked; only saved knowledge is served.
        history = [turn.model_dump() for turn in question.history]
        return JSONResponse({
            'answer': limited_answer(question.question, question.context, history, reason=reason),
            'source': 'offline_guide', 'code': reason, 'retry_after': retry_after,
        }, headers={'X-Tutor-Source': 'offline_guide', 'X-Tutor-Reason': reason})

    @app.post('/ask')
    async def ask(question: Question, request: Request):
        if not question.question.strip():
            return JSONResponse({'error': 'Please ask a question.'}, status_code=422)
        if any(k not in ('stage', 'room', 'topic') or len(v) > 100
               for k, v in question.context.items()):
            return JSONResponse({'error': 'Invalid level context.'}, status_code=422)
        guide = built_in_answer(question.question)
        if guide:
            return {'answer': guide, 'source': 'built_in'}
        key = os.environ.get('GEMINI_API_KEY', '').strip()
        model, fallback = configured_models()
        if (not key or not re.fullmatch(r'[a-zA-Z0-9._-]+', model)
                or (fallback and not re.fullmatch(r'[a-zA-Z0-9._-]+', fallback))):
            return JSONResponse({'error': 'The tutor is not configured.',
                                 'code': 'tutor_not_configured'}, status_code=503)
        # Uvicorn/proxy owns request.client. Do not trust raw forwarded headers.
        ip = request.client.host if request.client else 'unknown'
        # Anonymous fairness token, not authentication. Global provider budgets
        # still apply even if a caller creates new tokens. Never trust XFF.
        identity = 'session:' + question.client_id if question.client_id else 'peer:' + ip
        if busy.locked():
            return saved_help(question, 'tutor_busy', 5)
        async with busy:
            # Older game builds have no session token; only shared provider
            # caps apply rather than putting a whole lab into one player bucket.
            allowed, limit_code, wait = await limits.reserve(identity, retry=question.client_id is None)
            if not allowed:
                return saved_help(question, limit_code, wait)
            contents = [{'role': 'model' if t.role == 'assistant' else 'user',
                         'parts': [{'text': t.content}]} for t in question.history]
            import json
            contents.append({'role': 'user', 'parts': [{'text': json.dumps({
                'question': question.question, 'level_context': question.context})}]})
            payload = {'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                       'contents': contents,
                       'generationConfig': {'maxOutputTokens': 600}}
            try:
                # Keep retries server-side, bounded, and within the same
                # concurrency slot. Each provider attempt consumes the budget.
                # A deadline bounds the whole operation, not just socket reads.
                async with asyncio.timeout(PROVIDER_DEADLINE):
                    for attempt in range(MAX_PROVIDER_ATTEMPTS):
                        # A second request to an overloaded model often fails
                        # identically. Use the configured backup in that slot,
                        # without adding attempts or bypassing the budget.
                        attempt_model = fallback if attempt and fallback else model
                        # A timed-out primary must not skip the backup slot.
                        # Bound each attempt so the backup still has time left.
                        failure = None
                        attempt_payload = dict(payload)
                        if attempt_model in (DEFAULT_MODEL, DEFAULT_BACKUP):
                            attempt_payload['generationConfig'] = {
                                **payload['generationConfig'],
                                'thinkingConfig': {'thinkingLevel': 'minimal'},
                            }
                        try:
                            async with asyncio.timeout(PROVIDER_ATTEMPT_TIMEOUT):
                                response = await app.state.http.post(
                                    'https://generativelanguage.googleapis.com/v1beta/models/' + attempt_model + ':generateContent',
                                    headers={'x-goog-api-key': key}, json=attempt_payload)
                        except (httpx.HTTPError, TimeoutError) as exc:
                            if attempt + 1 == MAX_PROVIDER_ATTEMPTS:
                                raise
                            failure = exc
                        else:
                            if response.status_code == 200:
                                try:
                                    answer = provider_answer(response)
                                except ValueError as exc:
                                    # HTTP 200 with no text used to stop the
                                    # loop, so the healthy backup was skipped.
                                    failure = exc
                                else:
                                    return JSONResponse({'answer': answer}, headers={
                                        'X-Tutor-Source': 'live_ai',
                                        'X-Tutor-Route': 'backup' if attempt else 'primary',
                                    })
                            alternate_model = response.status_code in (404, 429) and fallback and fallback != model
                            if (failure is None and response.status_code not in RETRYABLE_STATUS
                                    and not alternate_model):
                                break
                        if attempt + 1 == MAX_PROVIDER_ATTEMPTS:
                            if failure is not None:
                                raise failure
                            break
                        await asyncio.sleep(1)
                        if not (await limits.reserve(identity, retry=True))[0]:
                            if failure is not None:
                                raise failure
                            break  # Return the last error without exceeding caps.
                if response.status_code == 429:
                    return saved_help(question, 'gemini_quota', 60)
                if response.status_code != 200:
                    return JSONResponse({'error': 'The tutor is temporarily unavailable.',
                                         'code': 'gemini_http_' + str(response.status_code)}, status_code=503)
                raise ValueError('No usable answer')
            except (httpx.TimeoutException, TimeoutError):
                return JSONResponse({'error': 'The AI service took too long. Please try again.',
                                     'code': 'gemini_timeout'}, status_code=503)
            except httpx.HTTPError:
                return JSONResponse({'error': 'The AI service could not be reached.',
                                     'code': 'gemini_network_error'}, status_code=503)
            except (ValueError, KeyError, IndexError, TypeError):
                return JSONResponse({'error': 'The tutor could not answer. Please try later.',
                                     'code': 'gemini_invalid_reply'}, status_code=503)

    return app


app = create_app()
