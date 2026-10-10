# Mang Tahimik shared Gemini tutor

The desktop game now calls your online server. Only the server holds the Gemini
key. Players do not need API keys. Press H in gameplay outside combat, or click
Mang Tahimik in the menu. Escape returns immediately while network work runs
in a background thread. Internet is required.

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
player connects automatically. The current empty URL intentionally reports
that Mang Tahimik is not online yet. CODEBREAK_TUTOR_URL can override the bundled
address for testing. Changing GitHub alone does not update already downloaded
copies of the game: pull/rebuild/distribute the new version.

Keep your Google AI Studio project on its Free Tier if you want free usage.
A Gemini app subscription does not configure this API project. The configured
model is gemini-2.5-flash-lite; availability/quotas depend on your Google account.
Change GEMINI_MODEL on Render if necessary, using a text generateContent model
available on your free project. No live key was used in automated tests.

## Limits and deployment constraints

This is a public, unauthenticated school-prototype endpoint. No shared secret
is shipped in the game. The server owns the prompt and model settings, caps
questions at 1000 characters, history at 8 turns of 4000 characters, request
bodies at 40000 bytes, and responses at 600 output tokens / 4000 characters.
It allows 2 concurrent Gemini calls. Default attempt caps are 8/minute globally,
100/day globally (UTC), and 3/minute per detected peer address. Failed provider
calls count toward the budget; no automatic retries increase spend.

Run exactly ONE worker and ONE instance: the counters are process-local and
reset on restart. They are conservative prototype protections, not durable
billing caps or player authentication. Render's proxy may cause players to
share the same peer bucket because forwarded IP headers are disabled. This
avoids letting callers bypass limits with forged forwarded headers. Do not
enable trust for all proxies without validating Render's forwarding behavior.
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
