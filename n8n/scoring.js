// Job scoring logic — used as a Function node in n8n
// Input: items[] where each item.json is a normalised job object
// Output: items[] with score, flagged_contract, include fields added

const FILTERS = {
  minSalary: 170000,
  targetSalary: 200000,
  contractKeywords: ["contract", "c2c", "corp-to-corp", "1099", "w2 only", "w2 contract", "6-month", "12-month", "temp"],
  agencyKeywords: ["staffing", "recruiting", "talent", "solutions llc", "consulting group", "resources inc", "workforce"],
  fteKeywords: ["full-time", "full time", "permanent", "fte", "direct hire"],
  seniorKeywords: ["staff ", "principal", "senior", "sr.", "lead", "head of", "director"],
  juniorKeywords: ["junior", "entry level", "associate", "intern", "graduate"],
  contractIncludeThreshold: 60,
  fteIncludeThreshold: 40,
};

function containsAny(text, keywords) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return keywords.some(k => lower.includes(k));
}

function scoreJob(job) {
  let score = 50;
  let flaggedContract = false;
  const titleAndDesc = `${job.title || ""} ${job.description || ""}`;
  const companyName = job.company || "";

  // --- Salary ---
  const salMin = job.salary_min || 0;
  const salMax = job.salary_max || 0;
  const salRef = salMax || salMin;

  if (salRef > 0 && salRef < FILTERS.minSalary) return { score: 0, flaggedContract: false, include: false, excludeReason: "salary_too_low" };
  if (salRef >= FILTERS.targetSalary) score += 10;
  else if (salRef >= FILTERS.minSalary) score += 5;

  // --- FTE signals ---
  const isFTE = job.employment_type === "fulltime" || containsAny(titleAndDesc, FILTERS.fteKeywords);
  if (isFTE) score += 20;

  // --- Contract signals ---
  const isContractTitle = containsAny(titleAndDesc, FILTERS.contractKeywords);
  const isAgency = containsAny(companyName, FILTERS.agencyKeywords);
  if (isContractTitle || isAgency) {
    score -= (isContractTitle ? 30 : 0) + (isAgency ? 20 : 0);
    flaggedContract = true;
  }

  // --- Seniority ---
  if (containsAny(job.title, FILTERS.seniorKeywords)) score += 15;
  if (containsAny(job.title, FILTERS.juniorKeywords)) score -= 20;

  // --- Equity ---
  if (containsAny(titleAndDesc, ["equity", "rsu", "stock options", "espp"])) score += 10;

  // --- Include decision ---
  const threshold = flaggedContract ? FILTERS.contractIncludeThreshold : FILTERS.fteIncludeThreshold;
  const include = score >= threshold;

  return { score, flaggedContract, include, excludeReason: include ? null : "score_below_threshold" };
}

// n8n Function node entry point
const output = [];
for (const item of items) {
  const job = item.json;
  const result = scoreJob(job);
  if (result.include) {
    output.push({
      json: {
        ...job,
        score: result.score,
        flagged_contract: result.flaggedContract,
      }
    });
  }
}

return output;
