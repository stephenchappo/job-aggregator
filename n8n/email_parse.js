// Email parser — Function node in n8n
// Input: item.json from Gmail node (raw message)
// Output: items[] of normalised job objects extracted from email body
//
// Handles:
//   - Built In daily digest (builtin.com)
//   - Wellfound job alerts (wellfound.com)
//   - LinkedIn job alerts (linkedin.com)

const source_map = {
  'builtin.com': 'builtin',
  'wellfound.com': 'wellfound',
  'linkedin.com': 'linkedin',
};

function detectSource(from, subject) {
  const combined = `${from} ${subject}`.toLowerCase();
  for (const [domain, source] of Object.entries(source_map)) {
    if (combined.includes(domain)) return source;
  }
  return 'email_unknown';
}

// Extracts all hrefs and surrounding text from a block of HTML
function extractLinksAndText(html) {
  const results = [];
  // Match anchor tags with href
  const linkRe = /<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = linkRe.exec(html)) !== null) {
    results.push({ href: m[1], text: m[2].replace(/<[^>]+>/g, '').trim() });
  }
  return results;
}

function parseBuiltIn(html) {
  // Built In emails contain job cards with title links and company/location nearby
  const jobs = [];
  const links = extractLinksAndText(html);
  for (const link of links) {
    if (!link.href.includes('builtin.com/job') && !link.href.includes('builtin.com/jobs')) continue;
    if (!link.text || link.text.length < 3) continue;
    jobs.push({
      source: 'builtin',
      title: link.text,
      company: null,
      location: null,
      url: link.href.split('?')[0],
      salary_min: null,
      salary_max: null,
      employment_type: 'unknown',
      description: null,
      posted_at: null,
    });
  }
  return jobs;
}

function parseWellfound(html) {
  const jobs = [];
  const links = extractLinksAndText(html);
  for (const link of links) {
    if (!link.href.includes('wellfound.com/jobs') && !link.href.includes('angel.co/job')) continue;
    if (!link.text || link.text.length < 3) continue;
    jobs.push({
      source: 'wellfound',
      title: link.text,
      company: null,
      location: null,
      url: link.href.split('?')[0],
      salary_min: null,
      salary_max: null,
      employment_type: 'unknown',
      description: null,
      posted_at: null,
    });
  }
  return jobs;
}

function parseLinkedIn(html) {
  const jobs = [];
  const links = extractLinksAndText(html);
  for (const link of links) {
    if (!link.href.includes('linkedin.com/jobs/view') && !link.href.includes('linkedin.com/comm/jobs')) continue;
    if (!link.text || link.text.length < 3) continue;
    jobs.push({
      source: 'linkedin',
      title: link.text,
      company: null,
      location: null,
      url: link.href.split('?')[0],
      salary_min: null,
      salary_max: null,
      employment_type: 'unknown',
      description: null,
      posted_at: null,
    });
  }
  return jobs;
}

const crypto = require('crypto');
function makeJobId(source, title, url) {
  const raw = `${source}:${(title || "").toLowerCase()}:${(url || "").slice(-40)}`;
  return crypto.createHash('md5').update(raw).digest('hex');
}

const item = items[0];
const email = item.json;
const html = email.body || email.html || email.snippet || "";
const from = email.from || "";
const subject = email.subject || "";

const source = detectSource(from, subject);

let rawJobs = [];
if (source === 'builtin') rawJobs = parseBuiltIn(html);
else if (source === 'wellfound') rawJobs = parseWellfound(html);
else if (source === 'linkedin') rawJobs = parseLinkedIn(html);

const output = rawJobs.map(job => ({
  json: {
    ...job,
    job_id: makeJobId(job.source, job.title, job.url),
    raw_json: { email_subject: subject, email_from: from },
  }
}));

return output.length > 0 ? output : [{ json: { _skip: true } }];
