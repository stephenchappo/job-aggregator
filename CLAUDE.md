# CLAUDE.md — job-aggregator

## What this project is

Daily SRE job aggregation pipeline. Pulls jobs from multiple sources, scores/deduplicates, posts to Discord.

**Owner:** Scon (Steve Chapman) — Senior SRE, active job search as of April 2026.
**Target roles:** SRE / DevOps / Platform / Infrastructure Engineer
**Criteria:** 5+ YOE, $170k+ (target $200k+), FTE preferred, Bay Area or remote

## Machines

| Machine | Role | Address |
|---------|------|---------|
| Zaphod | Windows workstation — this machine, where code lives | local |
| Deepthought | Linux AI/GPU box — deploy target | 192.168.1.151 |
| Trillian | Linux primary server | 192.168.1.100 |

SSH: `ssh scon@192.168.1.151` (Deepthought), `ssh scon@192.168.1.100` (Trillian)

## Architecture

```
n8n on Deepthought (daily 7am schedule)
  ├── HTTP → jobspy-api (Indeed, LinkedIn, Dice, ZipRecruiter)
  ├── Gmail → Built In daily digest email parse
  ├── Gmail → Wellfound alert email parse
  └── Gmail → LinkedIn alert email parse
        ↓
  Normalise → Postgres dedup → Score → Discord webhook
```

## Key paths

| Resource | Path |
|----------|------|
| This project (Zaphod) | `C:\Users\steph\projects\job-aggregator\` |
| Deploy target (Deepthought) | `/srv/docker/deepthought/jobspy/` |
| n8n UI | http://192.168.1.151:5678 |
| jobspy-api (after deploy) | http://192.168.1.151:8088 |
| Postgres (after deploy) | `192.168.1.151:5433` db=jobspy |
| n8n compose | `/srv/docker/deepthought/n8n/docker-compose.yml` |
| Deepthought global env | `/srv/docker/deepthought/.env` (TZ, DOCKER_USER only) |

## Discord webhook

Stored in: n8n credentials (do NOT commit to git)
Channel: Scon's personal Discord job alerts channel
The webhook URL is known — ask Scon if needed, do not hardcode in files.

## Project layout

```
docker/
  docker-compose.yml     # jobspy-api + jobspy-db services
  .env.example           # secrets template — copy to .env on Deepthought, never commit .env
  postgres/
    init.sql             # jobs table schema
config/
  searches.json          # search terms, locations, filters, keywords
n8n/
  scoring.js             # Function node: score + include/exclude logic
  normalise.js           # Function node: JobSpy response → common schema
  email_parse.js         # Function node: email HTML → job objects
  discord_format.js      # Function node: jobs → Discord embed batches
scripts/
  deploy.sh              # rsync docker/ to Deepthought, optional --restart
```

## Current status (as of 2026-04-01)

- [x] Project scaffolded, git initialised
- [x] docker-compose.yml written
- [x] Postgres schema written
- [x] All n8n Function node JS written
- [x] Deploy script written
- [ ] **Phase 1**: Deploy Docker services to Deepthought (`./scripts/deploy.sh --restart`)
- [ ] **Phase 2**: Set .env on Deepthought, verify jobspy-api responds
- [ ] **Phase 3**: Build n8n workflows (paste JS from n8n/ into Function nodes)
- [ ] **Phase 4**: Connect Gmail credential in n8n
- [ ] **Phase 5**: Test end-to-end, verify Discord output

## Asana

Project: trillian2 (GID: 1213656559375019), New Features section (GID: 1213578293643100)
All tasks assigned to Scon.
Parent ticket: [PLAN] Job Search - Daily Job Aggregator (created 2026-04-01 — fetch from Asana for URL)

## Scoring logic summary

- Base score: 50
- FTE / direct hire: +20
- Contract/C2C/1099: -30, flagged=true (only include if score ≥ 60)
- Staffing agency (company name heuristic): -20
- Senior/Staff/Principal title: +15
- Junior/entry title: -20
- Equity/RSU mentioned: +10
- Salary ≥ $200k: +10 | ≥ $170k: +5 | explicit < $170k: exclude
- Include threshold: FTE=40, contract=60

## Rules

- Follow global CLAUDE.md rules (in `~/.claude/CLAUDE.md` and `~/CLAUDE.md`)
- Never commit `.env` files
- After any deploy: verify with `docker ps` on Deepthought
- After n8n workflow changes: export workflow JSON and save to `n8n/workflows/`
- Every completed phase: create/update Asana task + wiki page on Outline (http://192.168.1.100:3002)
