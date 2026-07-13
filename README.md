# ops-agent

A personal multi-agent ops assistant that lives on Discord. Send it a natural-language message, and it decomposes your request, routes each part to the right specialized worker, and takes real action — creating Google Calendar events, drafting Gmail messages, and tracking personal tasks.

## Example

> "remind me to submit my assignment tonight, schedule a meeting with my professor friday at 3pm, and tell mom I'll be late"

This single message gets split into three sub-tasks, each dispatched to the correct worker:
- A task reminder saved locally
- A real Google Calendar event created for Friday 3pm
- A real Gmail draft created addressed to "mom"

## Architecture
## Tech stack

- **LLM**: Groq API (`llama-3.3-70b-versatile`) — routing, decomposition, and field extraction
- **Real actions**: Google Calendar API + Gmail API (OAuth2)
- **Interface**: Discord bot (`discord.py`)
- **Storage**: local JSON files (tasks/calendar/emails logs)
- **Language**: Python 3

## Setup

1. Clone the repo, create a virtualenv, `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `GROQ_API_KEY` and `DISCORD_TOKEN`
3. Set up a Google Cloud project with Calendar + Gmail APIs enabled, download OAuth `credentials.json` into the project root
4. Run `python orchestrator.py` for terminal mode, or `python bot.py` for Discord mode
5. First run will prompt a browser login for Google OAuth — approve it once, and `token.json` will persist the session

## Files

| File | Purpose |
|---|---|
| `config.py` | Centralized Groq client + env var loading |
| `orchestrator.py` | Multi-intent decomposition + routing logic |
| `task_manager.py` | Task persistence + due-date extraction |
| `calendar_agent.py` | Real Google Calendar event creation with date/time parsing |
| `email_agent.py` | Real Gmail draft creation |
| `bot.py` | Discord interface, reuses orchestrator logic |
| `reminder_checker.py` | Scans due items, proactively messages Discord |

## Status

- ✅ Multi-intent orchestration
- ✅ Real Google Calendar + Gmail integration
- ✅ Discord bot interface
- ✅ Error handling
- ⏳ 24/7 hosting (currently local-only)
- ⏳ Automatic scheduling for reminder_checker (needs hosting)
