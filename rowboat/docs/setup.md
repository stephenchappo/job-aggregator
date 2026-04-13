# Setup

## Zaphod

Install the official Rowboat app and bind the workspace:

- app install location: `C:\Users\steph\AppData\Local\Rowboat-win32-x64`
- workspace binding: `C:\Users\steph\.rowboat`

The binding should point to:

- `C:\Users\steph\projects\rowboat-workspace`

## Deepthought

Use the existing Ollama service instead of replacing it.

Verify:

```powershell
curl http://192.168.1.151:11434/api/tags
```

## Workspace Model Config

Current model config lives in:

- `C:\Users\steph\projects\rowboat-workspace\config\models.json`

Default model:

- `qwen3:8b`
