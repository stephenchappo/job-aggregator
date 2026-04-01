# job-aggregator

Daily SRE job aggregation pipeline. Pulls jobs from multiple sources, scores them, deduplicates, and posts to Discord.

## Sources
- **JobSpy API** (Docker): Indeed, LinkedIn, Dice, ZipRecruiter
- **Gmail parsing** (n8n): Built In, Wellfound, LinkedIn alerts

## Stack
- `jobspy-api` — FastAPI wrapper around JobSpy (Docker on Deepthought)
- `jobspy-db` — Postgres 16 for deduplication (Docker on Deepthought)
- `n8n` — orchestration, email parsing, Discord output (existing, Deepthought)

## Project layout

```
docker/              # Docker Compose + Postgres init
  docker-compose.yml
  .env.example
  postgres/
    init.sql
config/
  searches.json      # Search terms, locations, filters
n8n/
  scoring.js         # Scoring logic (paste into n8n Function node)
  normalise.js       # Field normalisation
  email_parse.js     # Email body → job objects
  discord_format.js  # Job objects → Discord embeds
scripts/
  deploy.sh          # rsync to Deepthought
```

## Deploy

```bash
# First time — set up .env on Deepthought
ssh scon@192.168.1.151 "cp /srv/docker/deepthought/jobspy/.env.example /srv/docker/deepthought/jobspy/.env"
# edit .env with real secrets, then:
./scripts/deploy.sh --restart
```

## n8n workflows

Two workflows to build manually in n8n (http://192.168.1.151:5678):

1. **JobSpy Daily Scrape** — Schedule → HTTP (jobspy-api) → Normalise → Dedup (Postgres) → Score → Discord
2. **Email Digest Parse** — Gmail trigger → Email Parse → Dedup (Postgres) → Score → Discord

Paste the JS files from `n8n/` into the relevant Function nodes.

## Scoring

- FTE: base 50 + 20 = 70 → included
- Contract: base 50 - 30 = 20 → excluded unless other signals push to 60+
- Salary < $170k: excluded outright
- Salary ≥ $200k: +10
- Senior/Staff/Principal title: +15
- Equity mentioned: +10
