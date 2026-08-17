@echo off
REM Windows batch script for deployment setup
REM Usage: deploy.bat <backend-url>

setlocal enabledelayedexpansion

set "BACKEND_URL=%1"
if "!BACKEND_URL!"=="" set "BACKEND_URL=https://ai-followup-crm-backend.onrender.com"

set "FRONTEND_URL=https://ai-followup-crm.vercel.app"

echo.
echo 🚀 AI Follow-up CRM Deployment Script (Windows)
echo ======================================
echo.
echo Backend URL:  !BACKEND_URL!
echo Frontend URL: !FRONTEND_URL!
echo.

echo 📝 Updating frontend configuration...

REM Read current config.js and update it
powershell -Command "(Get-Content 'backend\frontend\config.js') -replace 'RENDER_BACKEND_URL = ''.*''', 'RENDER_BACKEND_URL = ''!BACKEND_URL!''' | Set-Content 'backend\frontend\config.js'"

echo ✓ Updated backend/frontend/config.js
echo.

echo 🔍 Testing backend connectivity...
powershell -Command "try { (Invoke-WebRequest -Uri '!BACKEND_URL!/docs' -ErrorAction Stop).StatusCode; echo '✓ Backend is online' } catch { echo '⚠️  Backend is not responding' }"
echo.

echo 📋 Next Steps:
echo   1. Push changes to GitHub:
echo      git add .
echo      git commit -m "Update deployment configuration"
echo      git push origin main
echo.
echo   2. For Render backend:
echo      - Set environment variables in Render dashboard
echo      - Check: https://dashboard.render.com
echo.
echo   3. For Vercel frontend:
echo      - Set environment variables in Vercel dashboard
echo      - Check: https://vercel.com/dashboard
echo.
echo   4. Test:
echo      curl !BACKEND_URL!/api/dashboard
echo.

echo ✅ Deployment configuration complete!
echo.
pause
