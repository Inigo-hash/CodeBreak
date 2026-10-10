"""Optional, environment-configured Python tutor; never executes model output."""
import json
import os
import socket
import threading
import time
from queue import Queue, Empty
from urllib import request, error

MAX_QUESTION = 1000


class TutorError(Exception):
    """A safe error suitable for displaying to the player."""


def ask_mang_tahimik(question, context=None, history=()):
    question = question.strip()
    if not question or len(question) > MAX_QUESTION:
        raise TutorError('Ask a question between 1 and 1000 characters.')
    from urllib.parse import urlparse
    from pathlib import Path
    endpoint = os.environ.get('CODEBREAK_TUTOR_URL', '').strip()
    if not endpoint:
        try:
            config = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'tutor_config.json').read_text())
            endpoint = config.get('url', '')
        except (OSError, ValueError, AttributeError):
            endpoint = ''
    if not isinstance(endpoint, str) or not endpoint:
        raise TutorError('Mang Tahimik is not online yet. The game host needs to configure the tutor server.')
    parsed = urlparse(endpoint)
    if parsed.scheme != 'https' and not (
            parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')):
        raise TutorError('The tutor server must use a secure HTTPS connection.')
    if not parsed.hostname or parsed.username or parsed.password:
        raise TutorError('The tutor server address is invalid.')
    safe_context = {k: str(v)[:100] for k, v in (context or {}).items()
                    if k in ('stage', 'room', 'topic')}
    safe_history = [{'role': item['role'], 'content': str(item.get('content', ''))[:4000]}
                    for item in list(history)[-8:]
                    if item.get('role') in ('user', 'assistant')]
    payload = {'question': question, 'context': safe_context, 'history': safe_history}
    req = request.Request(endpoint, data=json.dumps(payload).encode('utf-8'),
                          headers={'Content-Type': 'application/json'})
    try:
        with request.urlopen(req, timeout=75) as response:
            result = json.loads(response.read(128000))
        answer = result['answer']
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError('empty answer')
        return answer.strip()[:4000]
    except error.HTTPError as exc:
        if exc.code == 429:
            raise TutorError('Mang Tahimik has reached a usage limit. Please try later.') from None
        raise TutorError('My AI connection failed. Please try again later.') from None
    except (error.URLError, TimeoutError, socket.timeout):
        raise TutorError('I cannot connect right now. Check the internet and try again.') from None
    except (ValueError, KeyError, IndexError, TypeError):
        raise TutorError('I did not receive a usable answer. Please try again.') from None


class TutorSession:
    """One daemon worker per session; only the Pygame thread updates chat state."""
    def __init__(self, ask=ask_mang_tahimik):
        self.ask = ask
        self.history = []
        self.pending = False
        self.last_sent = float('-inf')
        self.results = Queue()

    def submit(self, question, context=None):
        question = question.strip()
        if self.pending or not question or len(question) > MAX_QUESTION:
            return False
        if time.monotonic() - self.last_sent < 3:
            return False
        self.pending = True
        self.last_sent = time.monotonic()
        history = [dict(item) for item in self.history[-8:]]
        def work():
            try:
                answer = self.ask(question, context, history)
                self.results.put((question, answer, True))
            except TutorError as exc:
                self.results.put((question, str(exc), False))
            except Exception:
                self.results.put((question, 'Something went wrong. Please try again.', False))
        threading.Thread(target=work, daemon=True).start()
        return True

    def poll(self):
        try:
            question, answer, success = self.results.get_nowait()
        except Empty:
            return None
        self.pending = False
        if success:
            self.history.extend([{'role': 'user', 'content': question},
                                 {'role': 'assistant', 'content': answer}])
            self.history = self.history[-8:]
        return answer
