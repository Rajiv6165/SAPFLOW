#!/bin/bash
# Test the GitHub webhook receiver locally

WEBHOOK_SECRET="sapflow-webhook-secret-dev"
PAYLOAD='{
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
}'

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

curl -X POST http://localhost:8000/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: workflow_run" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD"

echo ""
echo "✅ Test webhook sent. Check your dashboard at http://localhost:3000"
