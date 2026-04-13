# Discord Demo Bot — Implementation Plan

## Overview

An interactive Discord bot that manages demo meeting registration:
live attendance check-in, presentation topic registration per project,
and a persistent status embed that updates in real time.
Hosted as a bitswan automation in the test1 workspace gitops repo.

---

## Repository Structure

Placed inside the test1 workspace at:
`~/.config/bitswan/workspaces/test1/workspace/discord-demo-bot/`

```
discord-demo-bot/
├── automation.toml          # expose=false, postgres service, secrets ref
├── image/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py              # bot entry point — Client, CommandTree, on_ready
    ├── database.py          # SQLAlchemy async engine, init_db(), get_db()
    ├── seed.py              # preseed_projects() and preseed_persons() on first boot
    ├── embed.py             # build_status_embed() — pure render, no DB access
    ├── docx_export.py       # generate_docx() → bytes for /export
    ├── models/
    │   ├── __init__.py
    │   ├── person.py
    │   ├── project.py
    │   ├── meeting.py
    │   ├── attendance.py
    │   └── topic.py
    └── cogs/
        ├── __init__.py
        ├── checkin.py       # /checkin, /checkout
        ├── topics.py        # /topic add, /topic remove
        ├── meetings.py      # /meeting new
        ├── registry.py      # /person add, /project add
        ├── status.py        # /status
        └── export.py        # /export
```

---

## Data Model

### `persons`
| Column       | Type    | Notes                          |
|--------------|---------|--------------------------------|
| id           | INTEGER | PK                             |
| name         | TEXT    | UNIQUE NOT NULL                |
| email        | TEXT    | UNIQUE NOT NULL                |
| discord_id   | TEXT    | NULL — snowflake, optional     |

### `projects`
| Column       | Type    | Notes                          |
|--------------|---------|--------------------------------|
| id           | INTEGER | PK                             |
| name         | TEXT    | UNIQUE NOT NULL                |
| guarantor_id | INTEGER | FK → persons.id                |

### `meetings`
| Column             | Type    | Notes                                    |
|--------------------|---------|------------------------------------------|
| id                 | INTEGER | PK                                       |
| meeting_date       | DATE    | UNIQUE NOT NULL                          |
| status_channel_id  | TEXT    | Discord channel snowflake                |
| status_message_id  | TEXT    | NULL until first embed is posted         |

Active meeting = row with latest `meeting_date`.

### `attendance`
| Column      | Type    | Notes                                         |
|-------------|---------|-----------------------------------------------|
| id          | INTEGER | PK                                            |
| meeting_id  | INTEGER | FK → meetings.id CASCADE                      |
| person_id   | INTEGER | FK → persons.id CASCADE                       |
| present     | BOOLEAN | DEFAULT FALSE                                 |
| UNIQUE      |         | (meeting_id, person_id)                       |

### `topics`
| Column       | Type    | Notes                      |
|--------------|---------|----------------------------|
| id           | INTEGER | PK                         |
| meeting_id   | INTEGER | FK → meetings.id CASCADE   |
| project_id   | INTEGER | FK → projects.id CASCADE   |
| title        | TEXT    | NOT NULL                   |
| presenter_id | INTEGER | FK → persons.id            |

---

## automation.toml

```toml
[deployment]
expose = false

[services.postgres]
enabled = true

[secrets]
dev = ["discord-demo-bot"]
```

`expose = false` — bot connects outbound to Discord gateway, listens on no port.

---

## Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

## entrypoint.sh

```sh
#!/bin/sh
set -e
exec python -m app.main
```

## requirements.txt

```
discord.py>=2.3.0
SQLAlchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
python-docx>=1.1.0
```

---

## Secrets File

Create `~/.config/bitswan/workspaces/test1/secrets/discord-demo-bot`:

```
DISCORD_TOKEN=<bot token from Discord Developer Portal>
DISCORD_GUILD_ID=<your server's snowflake ID>
DISCORD_STATUS_CHANNEL_ID=<channel snowflake for the live embed>
```

`POSTGRES_*` variables are injected automatically by the postgres service.

---

## Slash Commands

| Command                                  | Effect                                                    |
|------------------------------------------|-----------------------------------------------------------|
| `/checkin <name>`                        | Mark person present in active meeting                     |
| `/checkout <name>`                       | Mark person absent                                        |
| `/topic add <project> <title> <presenter>` | Register a presentation topic                           |
| `/topic remove <project> <title>`        | Remove a topic from this meeting                          |
| `/meeting new <date>`                    | Start a new meeting (YYYY-MM-DD), seeds attendance rows   |
| `/person add <name> <email>`             | Add someone to the standing attendee list                 |
| `/project add <name> <guarantor>`        | Add a project to the registry                             |
| `/status`                                | Force-refresh the status embed                            |
| `/export`                                | Post a filled .docx to the channel                        |

All mutating commands are ephemeral replies; the status embed channel stays clean.
`/export` posts a visible attachment.

`project` and `presenter` parameters use autocomplete (discord.py `app_commands.autocomplete`).

---

## Status Embed

Persistent message edited in-place after every mutation.

```
Demo Meeting — 30 March 2026
─────────────────────────────────────────
Present (11)          Absent (4)
Alice                 Bob
Carol                 Dave
...

[Product]  guarantor: Lukáš Večerka
  • Traefik — Tim
  • Position Paper — Pavel Enderle

[CETIN]  guarantor: Jáchym Doležal
  • Battery Sizing — Tomáš Ebert
─────────────────────────────────────────
Last updated: 14:32 UTC
```

Projects with no registered topics are omitted.

---

## Seeded Data (first boot)

### Persons
| Name              | Email                          |
|-------------------|--------------------------------|
| Pavel Enderle     | pavel.enderle@wingsdata.ai     |
| Roman Dvořák      | roman.dvorak@wingsdata.ai      |
| Jan Kotrč         | jan.kotrc@wingsdata.ai         |
| Tomas Dolezal     | tomas.dolezal@wingsdata.ai     |
| Timothy Hobbs     | timothy.hobbs@wingsdata.ai     |
| Lukáš Večerka     | lukas.vecerka@wingsdata.ai     |
| Michal Dvořák     | michal.dvorak@wingsdata.ai     |
| Matěj Outrata     | matej.outrata@wingsdata.ai     |
| Anita Doležalová  | anita.dolezalova@wingsdata.ai  |
| Tomáš Ebert       | tomas.ebert@wingsdata.ai       |
| Jakub Pogádl      | jakub.pogadl@wingsdata.ai      |
| Tomáš Peroutka    | tomas.peroutka@wingsdata.ai    |
| Jáchym Doležal    | jachym.dolezal@wingsdata.ai    |
| Patrik Kišeda     | patrik.kiseda@wingsdata.ai     |
| Matěj Novak       | matej.novak@wingsdata.ai       |

### Projects
| Project             | Guarantor         |
|---------------------|-------------------|
| Product             | Lukáš Večerka     |
| CETIN               | Jáchym Doležal    |
| Avant               | Jan Kotrč         |
| Medin               | Timothy Hobbs     |
| Faxchimp / Other    | Patrik Kišeda     |
| Organization        | Patrik Kišeda     |
| VAFO                | Patrik Kišeda     |

---

## Deployment Flow

1. Files placed in `~/.config/bitswan/workspaces/test1/workspace/discord-demo-bot/`
2. Secrets file `discord-demo-bot` created in workspace secrets directory
3. Gitops picks up the new automation, builds the image, starts the container
4. On startup: `init_db()` creates tables, `preseed()` seeds persons+projects if empty
5. Bot logs in, syncs slash commands to the configured guild
6. `DISCORD_STATUS_CHANNEL_ID` determines where the live embed appears

---

## Docker Manual Verification

Build and run locally before deploying:

```sh
cd ~/.config/bitswan/workspaces/test1/workspace/discord-demo-bot
docker build -f image/Dockerfile -t discord-demo-bot-test .
docker run --rm \
  --network bitswan_network \
  -e DISCORD_TOKEN=... \
  -e DISCORD_GUILD_ID=... \
  -e DISCORD_STATUS_CHANNEL_ID=... \
  -e POSTGRES_HOST=test1__postgres \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=... \
  -e POSTGRES_DB=postgres \
  -e POSTGRES_PORT=5432 \
  discord-demo-bot-test
```

Bot should log: `Logged in as DemoBot#XXXX` and slash commands should appear in Discord.
