// Normalisation function node — maps JobSpy API response fields to common schema
// Also used for email-parsed jobs (pass what you have, nulls are fine)
// Input: items[] from HTTP Request (JobSpy) or email parse node
// Output: items[] with consistent schema

const crypto = require('crypto');

function makeJobId(source, company, title, url) {
  const raw = `${source}:${(company || "").toLowerCase()}:${(title || "").toLowerCase()}:${(url || "").slice(-40)}`;
  return crypto.createHash('md5').update(raw).digest('hex');
}

function parseSalary(salaryStr) {
  if (!salaryStr) return { min: null, max: null };
  // Handle "$170,000 - $220,000", "$95/hr", "170k", etc.
  const str = salaryStr.replace(/,/g, '').toLowerCase();
  const hourly = str.includes('/hr') || str.includes('per hour') || str.includes('hourly');
  const nums = str.match(/\d+\.?\d*/g);
  if (!nums) return { min: null, max: null };
  let vals = nums.map(Number);
  if (hourly) vals = vals.map(v => v * 2080); // annualise
  if (vals.some(v => v < 1000)) vals = vals.map(v => v * 1000); // handle "170k" style
  return { min: vals[0] || null, max: vals[1] || vals[0] || null };
}

const output = [];
for (const item of items) {
  const raw = item.json;

  // JobSpy API returns jobs in a `jobs` array on the response
  const jobs = Array.isArray(raw.jobs) ? raw.jobs : [raw];

  for (const job of jobs) {
    const source = (job.site || job.source || "unknown").toLowerCase();
    const salary = parseSalary(job.salary || job.salary_range || job.min_amount_str);
    const salMin = job.min_amount ? Math.round(job.min_amount) : salary.min;
    const salMax = job.max_amount ? Math.round(job.max_amount) : salary.max;

    const normalised = {
      job_id: makeJobId(source, job.company, job.title, job.job_url || job.url),
      source: source,
      title: job.title || null,
      company: job.company || null,
      location: job.location || null,
      url: job.job_url || job.url || null,
      salary_min: salMin,
      salary_max: salMax,
      employment_type: job.job_type || job.employment_type || "unknown",
      description: job.description || null,
      posted_at: job.date_posted || job.posted_at || null,
      raw_json: job,
    };

    output.push({ json: normalised });
  }
}

return output;
