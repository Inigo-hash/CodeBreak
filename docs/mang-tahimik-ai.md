# Mang Tahimik shared Gemini tutor

The desktop game now calls your online server. Only the server holds the Gemini
key. Players do not need API keys. Press H in gameplay outside combat, or click
Mang Tahimik in the menu. Escape returns immediately while network work runs
in a background thread. Generated AI answers require internet; recognized basic
questions also have labelled built-in reference answers that work offline.

## Deploy from an iPad (free prototype)

1. Sign into https://dashboard.render.com/ with your own account.
2. Choose New → Blueprint and connect GitHub. Select Inigo-hash/CodeBreak.
   For a private repo, grant Render access; the owner may need to approve it.
3. Render reads render.yaml. Keep the web service on the Free plan.
4. When prompted for GEMINI_API_KEY, paste your key into Render's environment
   variable field, not a GitHub file. Choose Deploy/Apply.
5. After deployment finishes, open https://YOUR-SERVICE.onrender.com/health.
   It should display {"status":"ok"}. This only checks server liveness.
6. Send your service's PUBLIC URL to the person configuring CodeBreak (or to
   ChatGPT). Do not send the key. Edit src/data/tutor_config.json to:

```json
{"url": "https://YOUR-SERVICE.onrender.com/ask"}
```

Once that public address is committed and included in the game build, every
player connects automatically. An empty configured URL reports that Mang Tahimik is not online yet. CODEBREAK_TUTOR_URL can override the bundled
address for testing. Changing GitHub alone does not update already downloaded
copies of the game: pull/rebuild/distribute the new version.

Keep your Google AI Studio project on its Free Tier if you want free usage.
A Gemini app subscription does not configure this API project. The configured
model is gemini-3.1-flash-lite; availability/quotas depend on your Google account.
Change GEMINI_MODEL on Render if necessary, using a text generateContent model
available on your free project. No live key was used in automated tests.

## Limits and deployment constraints

This is a public, unauthenticated school-prototype endpoint. No shared secret
is shipped in the game. The server owns the prompt and model settings, caps
questions at 1000 characters, history at 8 turns of 4000 characters, request
bodies at 40000 bytes, and responses at 600 output tokens / 4000 characters.
It allows 2 concurrent Gemini calls. Default attempt caps are 8/minute globally,
100/day globally (UTC), and 3 questions/minute per anonymous game process.
The legacy `TUTOR_IP_PER_MINUTE` setting now controls this session allowance.
Clients send an in-memory random token, with no saved player/device identity.
Older clients without that token use only the global provider caps, so a
whole school is not incorrectly treated as one player. Failed provider
calls count toward the budget, including the single automatic retry for HTTP
502/503/504. The shipped pair now tries `gemini-3.1-flash-lite` first and
`gemini-2.5-flash-lite` second, using the same two model IDs already configured
by the prior release. Existing legacy pairs are promoted to this order without
requiring an environment edit. `GEMINI_FALLBACK_MODEL` can explicitly override
the backup; an empty string retries the primary instead. Custom primary models
outside this known pair have no implicit backup. A missing model (404) or
model-specific quota (429) can try the distinct backup once. Both models must
be available to the server's Google project. Retries consume the same attempt caps, keep the same concurrency
slot, and stop if the budget is exhausted. Quota, authentication, and model
errors are not retried against the same model. A provider retry consumes
global minute/day budget, but does not consume another question allowance.
The entire provider operation is bounded to 55 seconds.

Run exactly ONE worker and ONE instance: the counters are process-local and
reset on restart. They are conservative prototype protections, not durable
billing caps or player authentication. Anonymous session tokens are fairness
labels, not authentication; rotating them cannot bypass global provider caps.
Forwarded IP headers remain disabled and untrusted.
For larger/public launches add authenticated players and a durable shared quota
store; anyone who knows the public endpoint can consume its prototype quota.

Render free services sleep after 15 minutes of inactivity and can take about a
minute to wake. The game waits up to 75 seconds; if it times out, retry once after
the server has woken. This may not suit a strict-time classroom demonstration.
Free hosting availability and Gemini quotas are not guaranteed.

The server forwards questions, history and stage/room/topic strings to Google.
Avoid personal data: Google's free-tier content may be used to improve products.
Chats are not saved by this application. Hosting access logs can record request
metadata. The tutor's hint-only behavior is an instruction, not a guarantee;
evaluate real responses before teaching with it.

## Local verification

```bash
pip install -r requirements.txt -r server/requirements.txt
python -m unittest tests.test_ai_tutor tests.test_mang_tahimik tests.test_tutor_server
```

To run the server locally, set GEMINI_API_KEY in the server terminal, then:

```bash
uvicorn server.app:app --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers
```

In the game terminal set CODEBREAK_TUTOR_URL=http://127.0.0.1:8000/ask, then
run python main.py. For online deployments HTTPS is required. Install the server
requirements only on the host/development computer, not for game players.

References:
- https://ai.google.dev/api/generate-content
- https://ai.google.dev/gemini-api/docs/pricing
- https://render.com/docs/blueprint-spec
- https://render.com/docs/free

## Troubleshooting an AI connection failure

`/health` returning `ok` proves that Render is reachable, not that Gemini can
answer. An `/ask` response with `code: gemini_http_503` means Gemini returned
HTTP 503; it is not evidence of a missing API key. Google documents this as
an overloaded or temporarily unavailable service. The relay now waits one
second and tries the configured backup once, subject to its budget. Continued provider downtime
still returns an error; retries cannot guarantee availability.

The game reads only recognized error codes and displays an actionable message;
it does not show raw provider error bodies, keys, or secrets. Errors are not
saved as successful conversation history. No automatic client retry duplicates
the server's attempts. Deploy the server changes and update the game client to
use both improvements. Existing Render environment values are unchanged.

The client distinguishes concurrent-player capacity, the relay's shared usage
limit, and Google's quota. A capacity error asks the player to retry in 30
seconds rather than incorrectly reporting that the daily quota is exhausted.
Pushes must finish deploying on Render before the server improvement is live;
already installed game clients must also be updated for the new error messages.

The `X-Tutor-Revision` health response header identifies the deployed server
fix without spending provider quota. `model-recovery-20261019` includes model
404 recovery and the upgraded backup. `session-limits-20261019` additionally
separates session/minute/day limits and includes precise retry times. The
daily counter resets at 00:00 UTC (08:00 Philippine time). The health body
remains a liveness check.

Mang Tahimik's larger helper card is anchored at the bottom left in gameplay
and the main menu. The minimap stacks above it; the chat opens in a wider,
bottom-left panel. The entire menu helper card is clickable.

Reference: https://ai.google.dev/gemini-api/docs/troubleshooting

## Timeout failover and built-in reference help (2026-10-21)

A primary model timeout now reaches the second provider slot instead of exiting
before the backup is tried. Each slot has a 20-second deadline inside the
existing 55-second overall deadline. Both attempts consume the same global
budget and concurrency slot; a retry cannot bypass those caps. Authentication
errors are still not retried. The live Gemini service can remain unavailable
regardless of the retry logic.

Recognized basic Python definitions and game-control questions are answered by
`src/systems/tutor_guide.py` on both desktop and server. Answers begin with
`Built-in guide:` and server responses include `source: built_in`; these are
reference answers, not generated AI responses. They work without an API key or
internet on updated game clients and do not consume Gemini quota. For example,
`who is python`, `what is python`, and `how do i play codebreak` return immediately.
Only whole known questions match. Debugging, follow-ups and unrecognized
questions continue to use the live AI, with its existing safe error handling.
No built-in guide entry supplies a complete challenge solution.

After pulling the game update, ask `who is python` to verify the local guide.
To verify the deployed server, `/health` should return header
`X-Tutor-Revision: timeout-failover-guide-20261021`, and a POST to `/ask` with
`{"question":"what is python"}` should return `source: built_in`. Use a distinct
open-ended debugging question to test live Gemini separately; a successful guide
answer alone does not prove Gemini has recovered. Never publish API keys in logs
or game files.

## Defence backup and rehearsal (2026-10-23)

The desktop includes `src/data/tutor_knowledge.py`: reference material for Python
syntax, variables, types, input/output, formatting, operators, strings,
collections, loops, functions, errors and testing. Retrieval also uses current
stage, room, control, enemy and player-rule records for game questions.
Reworded English/Taglish questions use phrase matching; this is reference
retrieval, not model training or a local language model. Arbitrary code is not
executed and hidden tests/full challenge solutions are not included.

Exact FAQs still answer immediately. Other questions try the online AI first.
If no reply arrives after eight seconds, the chat shows a labelled reference
(or admits that no saved answer is known) while the real request continues.
A later generated answer is labelled `Live AI:`. On network, quota or server
failure, supported questions use local reference help. Unknown questions get
an honest limitation plus suggested topics, never an invented answer. Offline
mode can repeat a relevant reference for simple follow-ups; it cannot generate
a novel example or debug unseen code. Topic context does not reveal player progress.

For a fully disconnected rehearsal, set `CODEBREAK_TUTOR_MODE=offline` before
launching. The default mode continues to prefer live AI for flexible questions.
No API key is needed in the game.

```bash
python tools/check_tutor.py --offline
python tools/check_tutor.py --live
```

The live check deliberately uses an open-ended question and rejects reference
answers as proof of AI health. Run it before a defence, then open the actual
game, test a reworded lesson question, disconnect internet and test again.
Pull the latest game code before rehearsing; server deployment alone cannot
update a downloaded desktop game. Free hosting and external AI availability
remain outside the game's control.

The server now exposes `X-Tutor-Source: live_ai` and `X-Tutor-Route: primary` or
`backup` on generated replies, and health revision `defence-backup-20261023`.
These diagnostics reveal no keys, player data or raw provider errors. Gemini
3.1 Flash-Lite uses explicit minimal thinking for these brief explanations.
The primary migration adds no extra attempt and does not bypass usage limits.
