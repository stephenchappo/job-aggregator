$ErrorActionPreference = "Stop"

$url = "http://192.168.1.151:11434/api/tags"
$result = Invoke-RestMethod -Uri $url -Method Get
$result.models | Select-Object name, modified_at, size
