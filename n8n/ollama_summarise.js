// Ollama summariser — runs after Score Jobs, before Aggregate
// - LinkedIn jobs: skip (no description available via API)
// - Jobs with no description: skip (ollama_summary = null)
// - All others: call Ollama llama3.2 for company blurb + 5 bullet takeaways
// - If Ollama errors/times out: graceful fallback message
//
// NOTE: uses require('http') — fetch/$http/$helpers all unavailable in n8n task runner sandbox.
// NOTE: uses String.fromCharCode(10) for NL — n8n API unescapes \n in jsCode strings on save.
// NOTE: http (not https) — Ollama runs on local network without TLS.

const http = require('http');
const NL = String.fromCharCode(10);

function callOllama(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ model: 'llama3.2', prompt: prompt, stream: false, options: { temperature: 0.3, num_predict: 300 } });
    const opts = { hostname: '192.168.1.151', port: 11434, path: '/api/generate', method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) } };
    const timer = setTimeout(() => { req.destroy(); reject(new Error('timeout')); }, 120000);
    const req = http.request(opts, res => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => { clearTimeout(timer); try { resolve(JSON.parse(data).response || null); } catch(e) { resolve(null); } });
    });
    req.on('error', e => { clearTimeout(timer); reject(e); });
    req.write(body);
    req.end();
  });
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
