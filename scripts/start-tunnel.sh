#!/bin/bash
# Start ngrok tunnel for SAPFlow webhook testing
if ! command -v ngrok &> /dev/null
then
    echo "❌ ngrok could not be found."
    echo "Please install it from: https://ngrok.com/download"
    exit 1
fi

echo "🚀 Starting ngrok tunnel on port 8000..."
echo "Press Ctrl+C to stop the tunnel."
echo "Once started, copy the Forwarding URL (looks like https://xxxx.ngrok-free.app) and set it as SAPFLOW_WEBHOOK_URL in your repo secrets."
echo ""
ngrok http 8000
