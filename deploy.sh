#!/bin/bash

# Deployment script for Vercel + Render
# Usage: ./deploy.sh <backend-url>

set -e

BACKEND_URL="${1:-https://ai-followup-crm-backend.onrender.com}"
FRONTEND_URL="https://ai-followup-crm.vercel.app"

echo "🚀 AI Follow-up CRM Deployment Script"
echo "======================================"
echo ""
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Step 1: Update config.js with backend URL
echo "📝 Updating frontend configuration..."
sed -i "s|RENDER_BACKEND_URL = '.*'|RENDER_BACKEND_URL = '$BACKEND_URL'|g" backend/frontend/config.js
echo "✓ Updated backend/frontend/config.js"

# Step 2: Test backend connectivity
echo ""
echo "🔍 Testing backend connectivity..."
if curl -f "$BACKEND_URL/docs" -o /dev/null -s; then
    echo "✓ Backend is online"
else
    echo "⚠️  Backend is not responding (might still be starting up)"
fi

# Step 3: Verify configuration
echo ""
echo "🔐 Configuration Summary:"
echo "  - Backend: $BACKEND_URL/api"
echo "  - Frontend: $FRONTEND_URL"
echo "  - CORS Enabled for frontend"
echo ""

# Step 4: Instructions
echo "📋 Next Steps:"
echo "  1. Push changes to GitHub:"
echo "     git add ."
echo "     git commit -m 'Update deployment configuration'"
echo "     git push origin main"
echo ""
echo "  2. For Render backend:"
echo "     - Ensure environment variables are set in Render dashboard"
echo "     - Check deployment at: https://dashboard.render.com"
echo ""
echo "  3. For Vercel frontend:"
echo "     - Ensure environment variables are set in Vercel dashboard"
echo "     - Check deployment at: https://vercel.com/dashboard"
echo ""
echo "  4. Test the deployment:"
echo "     curl $BACKEND_URL/api/dashboard"
echo "     curl $FRONTEND_URL"
echo ""

echo "✅ Deployment configuration complete!"
