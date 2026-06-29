$secret = "sapflow-webhook-secret-dev"
$payload = @'
{
  "action": "completed",
  "workflow_run": {
    "id": 99999,
    "name": "SAPFlow CI",
    "status": "completed", 
    "conclusion": "success",
    "head_branch": "main",
    "head_sha": "abc1234def5678",
    "html_url": "https://github.com/Rajiv6165/sapflow/actions/runs/99999"
  }
}
'@

# Generate signature
$hmacsha = New-Object System.Security.Cryptography.HMACSHA256
$hmacsha.Key = [System.Text.Encoding]::UTF8.GetBytes($secret)
$signatureBytes = $hmacsha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))
$signature = [System.BitConverter]::ToString($signatureBytes).Replace("-", "").ToLower()

# Headers
$headers = @{
    "Content-Type" = "application/json"
    "X-GitHub-Event" = "workflow_run"
    "X-Hub-Signature-256" = "sha256=$signature"
}

# Post request
$response = Invoke-RestMethod -Uri "http://localhost:8000/webhooks/github" -Method Post -Body $payload -Headers $headers -ContentType "application/json"
$responseJson = $response | ConvertTo-Json -Compress
Write-Host "Response from server: $responseJson"
Write-Host "✅ Test webhook sent. Check your dashboard at http://localhost:3000"
