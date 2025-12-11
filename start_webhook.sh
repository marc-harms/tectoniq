#!/bin/bash
# TECTONIQ Webhook Server Startup Script
# Run this in Terminal 2

cd /home/marc/Projects/TECTONIQ
source venv/bin/activate

# Load secrets from Streamlit config
# Replace these with your actual values
export STRIPE_SECRET_KEY=$(grep STRIPE_SECRET_KEY .streamlit/secrets.toml | cut -d'"' -f2)
export SUPABASE_URL=$(grep SUPABASE_URL .streamlit/secrets.toml | cut -d'"' -f2)
export SUPABASE_KEY=$(grep SUPABASE_KEY .streamlit/secrets.toml | cut -d'"' -f2)

# Webhook secret (get from Stripe CLI when running)
# You'll need to update this after running: stripe listen
export STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-}"

echo "🚀 Starting TECTONIQ Webhook Server..."
echo "   STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY:0:20}..."
echo "   SUPABASE_URL: $SUPABASE_URL"
echo "   WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET:0:20}..."
echo ""

python webhook_handler.py

