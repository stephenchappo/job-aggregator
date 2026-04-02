// Discord formatter — Function node in n8n
// Input: items[] of scored, deduped jobs
// Output: one item per Discord embed batch (max 10 embeds per message)
// Jobs are sorted descending by score before batching.

const WEBHOOK_BATCH_SIZE = 10;

function formatSalary(min, max) {
  if (!min && !max) return "Salary not listed";
  const fmt = (n) => `$${Math.round(n / 1000)}k`;
  if (min && max && min !== max) return `${fmt(min)}–${fmt(max)}`;
  return fmt(min || max);
}

function jobEmbed(job) {
  const isContract = job.flagged_contract;
  const emoji = isContract ? "🟡" : "🟢";
  const tag = isContract ? "[CONTRACT ⚠️]" : "[FTE]";
  const sourceLabel = (job.source || "unknown").toUpperCase();
  const salary = formatSalary(job.salary_min, job.salary_max);
  const location = job.location || "Location not listed";

  return {
    title: `${emoji} ${tag} ${job.title} — ${job.company || "Unknown Company"}`,
    url: job.url || "",
    color: isContract ? 0xFFA500 : 0x00C853,
    fields: [
      { name: "📍 Location", value: location, inline: true },
      { name: "💰 Salary", value: salary, inline: true },
      { name: "🔗 Source", value: sourceLabel, inline: true },
      { name: "⭐ Score", value: String(job.score), inline: true },
    ],
    footer: { text: isContract ? `Flagged: contract/C2C — included on merit` : "FTE" },
  };
}

const allJobs = (items[0].json.data || items.map(i => i.json))
  .sort((a, b) => b.score - a.score);

const fteCount = allJobs.filter(j => !j.flagged_contract).length;
const contractCount = allJobs.filter(j => j.flagged_contract).length;

const output = [{
  json: {
    content: `📋 **Daily Job Digest** — ${allJobs.length} new jobs (${fteCount} FTE, ${contractCount} contract)`,
    embeds: []
  }
}];

for (let i = 0; i < allJobs.length; i += WEBHOOK_BATCH_SIZE) {
  output.push({
    json: {
      content: "",
      embeds: allJobs.slice(i, i + WEBHOOK_BATCH_SIZE).map(jobEmbed)
    }
  });
}

return output;
