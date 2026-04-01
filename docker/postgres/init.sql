CREATE TABLE IF NOT EXISTS jobs (
    id              SERIAL PRIMARY KEY,
    job_id          TEXT UNIQUE NOT NULL,        -- source:company:title hash or native ID
    source          TEXT NOT NULL,               -- indeed, linkedin, dice, ziprecruiter, builtin, wellfound
    title           TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    url             TEXT,
    salary_min      INTEGER,                     -- annual, USD
    salary_max      INTEGER,
    employment_type TEXT,                        -- full_time, contract, part_time, unknown
    score           INTEGER NOT NULL DEFAULT 50,
    flagged_contract BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen       TIMESTAMP NOT NULL DEFAULT NOW(),
    posted_at       TIMESTAMP,
    raw_json        JSONB
);

CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_flagged_contract ON jobs(flagged_contract);
