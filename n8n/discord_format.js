// Discord formatter — Function node in n8n
// Input: items[] of scored, deduped jobs (with optional ollama_summary)
// Output: one item per Discord embed batch (max 10 embeds per message)
// Jobs are sorted descending by score before batching.

const WEBHOOK_BATCH_SIZE = 10;
const DISCORD_EMBED_CHAR_LIMIT = 5500; // Discord hard limit is 6000; leave headroom

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

  const fields = [
    { name: "📍 Location", value: job.location || "Not listed", inline: true },
    { name: "💰 Salary", value: formatSalary(job.salary_min, job.salary_max), inline: true },
    { name: "🔗 Source", value: (job.source || "unknown").toUpperCase(), inline: true },
    { name: "⭐ Score", value: String(job.score), inline: true },
  ];

  if (job.ollama_summary) {
    fields.push({ name: "🤖 Summary", value: job.ollama_summary.slice(0, 1024), inline: false });
  }

  return {
    title: `${emoji} ${tag} ${job.title} — ${job.company || "Unknown Company"}`,
    url: job.url || "",
    color: isContract ? 0xFFA500 : 0x00C853,
    fields,
    footer: { text: isContract ? "Flagged: contract/C2C — included on merit" : "FTE" },
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

// Batch by both count (max 10) and total embed char count (max 5500)
let batch = [];
let batchChars = 0;
for (const job of allJobs) {
  const embed = jobEmbed(job);
  const embedChars = JSON.stringify(embed).length;
  if (batch.length > 0 && (batch.length >= WEBHOOK_BATCH_SIZE || batchChars + embedChars > DISCORD_EMBED_CHAR_LIMIT)) {
    output.push({ json: { content: "", embeds: batch } });
    batch = [];
    batchChars = 0;
  }
  batch.push(embed);
  batchChars += embedChars;
}
if (batch.length > 0) {
  output.push({ json: { content: "", embeds: batch } });
}

return output;
