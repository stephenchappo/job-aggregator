// Discord formatter — Function node in n8n
// Input: items[] of scored, deduped jobs
// Output: one item per Discord embed batch (max 10 embeds per message)

const WEBHOOK_BATCH_SIZE = 10;

function formatSalary(min, max) {
  if (!min && !max) return "Salary not listed";
  const fmt = (n) => `$${Math.round(n / 1000)}k`;
  if (min && max && min !== max) return `${fmt(min)}–${fmt(max)}`;
  return fmt(min || max);
}

function jobEmbed(job) {
  const fte = job.flagged_contract;
  const emoji = fte ? "🟡" : "🟢";
  const tag = fte ? "[CONTRACT ⚠️]" : "[FTE]";
  const sourceLabel = (job.source || "unknown").toUpperCase();
  const salary = formatSalary(job.salary_min, job.salary_max);
  const location = job.location || "Location not listed";

  return {
    title: `${emoji} ${tag} ${job.title} — ${job.company || "Unknown Company"}`,
    url: job.url || "",
    color: fte ? 0xFFA500 : 0x00C853,
    fields: [
      { name: "📍 Location", value: location, inline: true },
      { name: "💰 Salary", value: salary, inline: true },
      { name: "🔗 Source", value: sourceLabel, inline: true },
      { name: "⭐ Score", value: String(job.score), inline: true },
    ],
    footer: { text: fte ? `Flagged: contract/C2C — included on merit` : "FTE" },
  };
}

// Group into batches
const batches = [];
for (let i = 0; i < items.length; i += WEBHOOK_BATCH_SIZE) {
  batches.push(items.slice(i, i + WEBHOOK_BATCH_SIZE));
}

const output = [];

// Summary message first
const fteCount = items.filter(i => !i.json.flagged_contract).length;
const contractCount = items.filter(i => i.json.flagged_contract).length;
output.push({
  json: {
    content: `📋 **Daily Job Digest** — ${items.length} new jobs (${fteCount} FTE, ${contractCount} contract)`,
    embeds: []
  }
});

// One Discord payload per batch
for (const batch of batches) {
  output.push({
    json: {
      content: "",
      embeds: batch.map(i => jobEmbed(i.json))
    }
  });
}

return output;
