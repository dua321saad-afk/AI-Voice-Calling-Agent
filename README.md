# Multi-Domain LLM Voice Agent — Browser Edition

An AI voice agent for three business domains (IT Services, Restaurant,
Petrol Pump) that runs entirely through your laptop's microphone and
speaker — no phone-calling provider, no per-minute cost, genuinely free.

**How it's used:** the client calls in on their own mobile phone (any way
they like) and puts it on speaker next to your laptop. You open this
app's Agent page, hit Start, and from then on the laptop's mic listens
to whatever comes through the phone speaker, and the laptop's speaker
talks back — a live, natural, back-and-forth conversation with no fixed
turn limit, and you can interrupt the agent mid-sentence just by talking
over it.

## What changed from a phone-calling version

Earlier versions of projects like this use Twilio to have the *system*
dial out to a phone number. This version doesn't do that at all — there's
no telephony account, no verified caller IDs, no country restrictions,
and no per-minute billing, because nothing places or receives an actual
phone call. The "call" is really a browser session using the **Web
Speech API** (built into Chrome/Edge, completely free) for both
speech-to-text and text-to-speech.

## Two-sided architecture

This is now two completely separate apps sharing one backend:

**User side (public):**
- `/signup` — create an account (username + password, hashed with Werkzeug)
- `/login` — log in
- `/services` — one screen listing every service across all three domains,
  with a single **"Start Live Conversation"** button
- `/agent` — the live mic/speaker voice widget
- Regular users can only ever see and manage **their own** conversations
  (enforced server-side — a user's session ID is checked against their
  account on every API call)

**Admin side (staff only, separate login):**
- `/admin/login` — a single admin account, credentials from `.env`
  (not a signup-based account)
- `/admin` — dashboard listing every conversation from every user, across
  all three domains, plus a registered-users table
- `/admin/domain/<key>` — same, filtered to one domain
- `/admin/conversation/<id>` — full transcript viewer
- Admin can **delete any single conversation, or wipe all history** for
  one domain or everything — buttons on every conversation list
- The admin cannot start conversations — that's a user-side-only action

## Key features

- **Fixed greeting, LLM-driven domain routing** — every session opens
  with *"Hello! How may I assist you?"*. The agent then uses the LLM's
  own reasoning to figure out which of the three domains the caller
  wants (not a hardcoded keyword list) — so "do you do logos?" correctly
  routes to IT Services because graphic design is one of its real
  services, without that mapping being spelled out anywhere in code.
- **Logical decline for out-of-scope requests** — if asked about
  something none of the three domains cover, the LLM generates a natural
  explanation and redirects, in its own words each time.
- **Open-ended conversation, no turn limit** — the agent keeps answering
  follow-up questions for as long as the caller keeps asking, closing
  out only when they say something like "thanks, that's all" or similar.
- **Barge-in / interruption** — speech recognition keeps listening even
  while the agent is talking. If you speak a real sentence while it's
  mid-response, it stops talking immediately and listens to you instead.
- **Hybrid answering (not purely hardcoded)** — each domain has a
  pre-defined FAQ knowledge base checked first for fast, reliable answers
  on common questions; anything not covered falls through to the Groq
  LLM, which reasons out an answer in character. This hybrid design is
  what makes the ~80-90% accuracy target realistic and testable (see
  "Accuracy" below) while still letting the agent "think for itself" on
  novel questions.

## Tech stack

- **Backend:** Python 3 + Flask
- **LLM:** Groq API (free tier), running Llama 3.3 — genuinely free, no
  card required for the free tier
- **Speech (in the browser, free, built-in):** Web Speech API —
  `SpeechRecognition` for listening, `speechSynthesis` for talking
- **FAQ matching:** `rapidfuzz` for fuzzy keyword/question matching
- **Storage:** SQLite (no external DB server)

## Project structure

```
voice-calling-agent/
├── app.py                     # Flask routes: user auth, admin auth, agent API, delete
├── config.py                  # Loads settings from .env
├── database.py                # SQLite: accounts, sessions, messages, delete functions
├── data/
│   └── knowledge_base.py      # Per-domain persona, services, FAQ answers
├── services/
│   ├── agent_service.py       # Orchestrates domain routing + FAQ/LLM answering
│   └── groq_service.py        # Groq LLM calls: classify domain, generate replies
├── templates/
│   ├── signup.html            # User: create account
│   ├── login.html             # User: log in
│   ├── services.html          # User: all services + Start Live Conversation
│   ├── agent.html             # User: the live voice widget (mic/speaker UI + JS)
│   ├── admin_login.html       # Admin: separate login
│   ├── dashboard.html         # Admin: all conversations + registered users
│   ├── domain_dashboard.html  # Admin: per-domain conversation list
│   ├── conversation.html      # Admin: full transcript viewer
│   └── base.html              # Shared layout, conditional nav (user vs admin)
└── static/style.css
```

## 1. Install dependencies

```bash
cd voice-calling-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Get a free Groq API key

1. Sign up free at [console.groq.com](https://console.groq.com)
2. Create an API key
3. Copy `.env.example` to `.env` and paste it in:

```bash
cp .env.example .env
```

```
GROQ_API_KEY=gsk_your_actual_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=choose_a_real_password
```

That's the only external account you need. No Twilio, no telephony setup.

## 3. Run it

```bash
python app.py
```

Open `http://localhost:5000` — you'll land on the user login page.

**As a user:**
1. Click **Sign up**, create an account
2. Log in
3. You'll see the **Services** screen listing everything all three
   businesses offer, with one **Start Live Conversation** button
4. Click it, then **Start Session** on the agent page

**As admin:**
1. Go to `http://localhost:5000/admin/login`
2. Log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from your `.env`
3. See every conversation from every user, across all three domains,
   with delete buttons on each

## 4. Using it with a real caller

1. Have the caller (or a staff member on their behalf) sign up / log in
   on the user side
2. Click **Start Live Conversation** → **Start Session**
3. Have the caller hold their phone on speaker near your laptop's mic
4. The agent greets them, listens, figures out which domain they want,
   and answers naturally
5. To end, they can say "thanks, that's all" / "goodbye", or click
   **End Session**

## Browser requirements

- **Chrome or Edge on desktop** — the Web Speech API's `SpeechRecognition`
  isn't supported in Firefox or Safari at the time of writing
- **HTTPS or localhost** — browsers only allow microphone access on
  secure origins; `localhost` is exempt so local use works out of the box

## Accuracy — what "80-90%" actually means here

Open-ended LLM replies don't have a single ground-truth answer to score
against, so there's no meaningful "accuracy %" for that part. What *can*
be measured is the FAQ-matching layer: given a labeled set of typical
questions per domain, the keyword/fuzzy-match layer in `agent_service.py`
correctly identifies the right pre-defined answer roughly 80-90% of the
time — questions it doesn't confidently match fall through to the LLM,
which handles them with its own reasoning instead of failing outright.
This two-layer design (fast/reliable FAQ + flexible LLM fallback) is
what the "not hardcoded, has a brain" requirement in this project maps to.

## Known limitations (be upfront about these in a demo/viva)

- **Barge-in isn't perfect.** The mic can sometimes pick up the agent's
  own voice as "the caller talking," especially at high speaker volume,
  since this is a genuine two-device (phone speaker → laptop mic) setup
  rather than a single headset. Keeping the phone speaker at a moderate
  volume and using a real 2+ word sentence to interrupt (see
  `templates/agent.html`) meaningfully reduces false triggers, but this
  is an inherent tradeoff of the free, browser-only approach — polished
  commercial voice AI uses dedicated audio pipelines to avoid this.
- **No GROQ_API_KEY configured** → domain routing falls back to basic
  keyword matching, which is noticeably less flexible than the LLM (e.g.
  it won't catch "what fuel types do you have" unless "fuel price" or
  similar exact phrases appear in the keyword list). Always set a real
  key for the intended behavior.
- **Domain locks in for the rest of the session** once detected — the
  agent doesn't re-classify every turn, so a call starts as one business
  and stays that way, similar to how calling a real restaurant's line
  wouldn't suddenly start answering fuel station questions.
- **SQLite is single-file** — fine for a project/demo; a real deployment
  serving many simultaneous sessions would want a proper database.

## Optional: deploying publicly (Render free tier)

Not required for the core use case (laptop mic/speaker), but if you want
the dashboard reachable from another device:

1. Push this project to GitHub
2. On [render.com](https://render.com), New → Web Service → connect the repo
3. It picks up `render.yaml` automatically (free plan, Python runtime)
4. Add your `GROQ_API_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` as environment
   variables in the Render dashboard
5. Render's free tier spins down after inactivity and takes a few seconds
   to wake back up on the next request — normal for a free-tier demo

## Ideas to extend this project

- Let the agent re-check domain mid-call if the topic shifts drastically
- Add a confidence-based "are you sure?" confirmation before switching domains
- Swap SQLite for Postgres if deploying for real multi-user traffic
- Add authentication per staff member instead of one shared admin login
- Export a conversation transcript as PDF from the dashboard
