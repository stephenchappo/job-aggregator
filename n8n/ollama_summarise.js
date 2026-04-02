// Ollama summariser — runs after Score Jobs, before Aggregate
// - LinkedIn jobs: skip (no description available via API)
// - Jobs with no description: skip (ollama_summary = null)
// - All others: call Ollama llama3.2 for company blurb + 5 bullet takeaways
// - If Ollama errors/times out: graceful fallback message

const OLLAMA_URL = 'http://192.168.1.151:11434/api/generate';
const MODEL = 'llama3.2';
const TIMEOUT_MS = 60000;
const NL = String.fromCharCode(10); // avoid \n in string literals — n8n API unescapes them on save

async function callOllama(prompt) {
  const body = JSON.stringify({ model: MODEL, prompt: prompt, stream: false, options: { temperature: 0.3, num_predict: 300 } });
  const response = await $helpers.httpRequest({ method: 'POST', url: OLLAMA_URL, body: body, headers: { 'Content-Type': 'application/json' }, timeout: TIMEOUT_MS });
  return response.response || (response.body && response.body.response) || null;
}

const output = [];
for (const item of items) {
  const job = Object.assign({}, item.json);

  if (job.source === 'linkedin') {
    job.ollama_summary = 'LinkedIn does not provide job descriptions via API so none provided.';
    output.push({ json: job });
    continue;
  }

  if (!job.description) {
    job.ollama_summary = null;
    output.push({ json: job });
    continue;
  }

  const lines = [
    'You are summarising a job listing for a senior SRE/DevOps engineer reviewing job opportunities.',
    '',
    'Job title: ' + job.title,
    'Company: ' + (job.company || 'Unknown'),
    'Location: ' + (job.location || 'Unknown'),
    '',
    'Job description:',
    (job.description || '').slice(0, 3000),
    '',
    'Respond in exactly this format, nothing else:',
    '',
    'Company: <2 sentences max about the company>',
    'Takeaways:',
    '* <key takeaway 1>',
    '* <key takeaway 2>',
    '* <key takeaway 3>',
    '* <key takeaway 4>',
    '* <key takeaway 5>'
  ];
  const prompt = lines.join(NL);

  try {
    const result = await callOllama(prompt);
    job.ollama_summary = result ? result.trim() : '(Ollama returned empty response)';
  } catch (err) {
    job.ollama_summary = '(Ollama did not respond: ' + (err.message || 'timeout') + ')';
  }

  output.push({ json: job });
}

return output;
