# Mang Tahimik Python tutor

Click the existing floating Mang Tahimik sprite in the main menu, or press H.
During gameplay press H when outside combat. The modal pauses gameplay;
Escape returns immediately, including while a request is pending. Enter or
Ask sends the question. Scroll the conversation with the mouse wheel.
The sprite's appearance, animation and placement are unchanged.

## Demo setup

Install the usual requirements; no new Python packages are needed.
Set environment variables in the terminal that launches the game:

```powershell
$env:OPENAI_API_KEY = "your-own-api-key"
$env:CODEBREAK_AI_MODEL = "your-chat-completions-model-id"
python main.py
```

For bash use `export OPENAI_API_KEY=...` and
`export CODEBREAK_AI_MODEL=...` before launching. A .env file is NOT automatically
loaded. Use a Chat Completions compatible text model available to your API account.
API usage requires separate API billing; a ChatGPT subscription is not an API key.
Never commit a key or bundle one with a distributed build.

## Behavior and limits

The prompt instructs Mang Tahimik to help with beginner Python, redirect
unrelated questions and offer hints rather than full challenge solutions.
These are model instructions, not a guaranteed answer filter. Evaluate actual
responses with your selected model before a classroom release.
The current stage and room are sent during gameplay. Player code, hidden tests,
solutions and save files are not sent. Questions and the last four successful
conversation turns go to OpenAI. Chat is kept in memory for this modal only.
There is a 1000-character question limit, 600-token output budget, 25-second
network timeout, one pending request and a three-second local send cooldown.
Closing the modal discards its result, but cannot cancel an already sent API call.

This implements direct API access for a controlled demonstration computer.
For public distribution, replace the transport in ask_mang_tahimik with your
own authenticated backend and enforce quotas and the tutor prompt there.
A cooldown in a desktop client cannot enforce shared-account usage limits.

## Verification

Run `python -m unittest tests.test_ai_tutor tests.test_mang_tahimik`.
Tests mock the API; a real key/model is needed for live response evaluation.
API schema: https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
