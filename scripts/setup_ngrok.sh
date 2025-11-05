#!/bin/bash
"""
Setup ngrok tunnel for ElevenLabs webhook access
"""

echo "🚀 Setting up ngrok tunnel for ElevenLabs webhooks"
echo "=================================================="

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install it first:"
    echo "   brew install ngrok/ngrok/ngrok"
    echo "   or download from: https://ngrok.com/download"
    exit 1
fi

# Check if ngrok is authenticated
if ! ngrok config check &> /dev/null; then
    echo "⚠️  ngrok is not authenticated. Please run:"
    echo "   ngrok config add-authtoken YOUR_AUTHTOKEN"
    echo "   Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

# Start ngrok tunnel
echo "🌐 Starting ngrok tunnel on port 44000..."
echo "   This will expose your local backend to the internet"
echo "   for ElevenLabs webhook access."
echo ""
echo "📋 Next steps:"
echo "   1. Copy the HTTPS URL from the ngrok output below"
echo "   2. Use this URL in ElevenLabs webhook configuration:"
echo "      - Post-call webhook: https://YOUR_URL.ngrok.io/api/webhooks/interaction/log"
echo "      - Server tools: https://YOUR_URL.ngrok.io/api/webhooks/student/status"
echo ""
echo "🔒 Security: Your webhook endpoints are protected with API key authentication"
echo "   API Key: $(grep ELEVENLABS_API_KEY .env | cut -d'=' -f2)"
echo ""

# Start ngrok
ngrok http 44000
