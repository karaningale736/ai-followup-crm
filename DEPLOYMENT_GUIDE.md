# Deployment Guide: Vercel (Frontend) + Render (Backend)

## Overview
This guide will help you deploy the AI Follow-up CRM system:
- **Frontend**: Vercel (Static hosting)
- **Backend**: Render (Python/FastAPI)

---

## Prerequisites
1. GitHub account with the project repository
2. Vercel account (vercel.com)
3. Render account (render.com)
4. Environment variables/secrets ready

---

## Part 1: Deploy Backend on Render

### Step 1: Prepare Backend for Render
Your backend is already configured with:
- `Procfile` - Specifies how to run the app
- `render.yaml` - Render-specific configuration
- `requirements.txt` - Python dependencies

### Step 2: Create Render Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Fill in the service details:
   - **Name**: `ai-followup-crm-backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend/`

### Step 3: Add Environment Variables on Render

Add these variables in Render dashboard (Settings → Environment):

```
DATABASE_URL=sqlite:///./crm.db
FRONTEND_URL=https://ai-followup-crm.vercel.app
GEMINI_API_KEY=<your-api-key>
SECRET_KEY=<generate-a-random-string>
ALLOWED_ORIGINS=https://ai-followup-crm.vercel.app,http://localhost:3000
SMTP_HOST=<optional>
SMTP_PORT=587
SMTP_USERNAME=<optional>
SMTP_PASSWORD=<optional>
SMTP_FROM_EMAIL=<optional>
```

### Step 4: Deploy
- Click **Deploy**
- Wait for the build to complete (3-5 minutes)
- Your backend URL will be: `https://ai-followup-crm-backend.onrender.com`
- API docs available at: `https://ai-followup-crm-backend.onrender.com/docs`

---

## Part 2: Deploy Frontend on Vercel

### Step 1: Prepare Frontend Files

The frontend files are in `backend/frontend/`:
- `index.html` - Main HTML
- `styles.css` - Styling
- `app.js` - JavaScript logic
- `config.js` - API configuration (NEW)

### Step 2: Update Frontend API Configuration

The `config.js` file handles API URL based on environment:
- **Local**: `http://localhost:8000`
- **Production**: Uses Render backend URL

### Step 3: Create Vercel Project

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure project:
   - **Framework**: Other (Static HTML)
   - **Root Directory**: Leave blank or set to `backend/frontend/`
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty

### Step 4: Add Environment Variables on Vercel

In Vercel project settings, add:

```
VITE_API_BASE_URL=https://ai-followup-crm-backend.onrender.com
```

### Step 5: Update Configuration

Update `backend/frontend/config.js` with your Render backend URL:

```javascript
const RENDER_BACKEND_URL = 'https://your-backend.onrender.com';
```

### Step 6: Deploy
- Click **Deploy**
- Wait for deployment (1-2 minutes)
- Your frontend URL: `https://ai-followup-crm.vercel.app`

---

## Testing Deployment

### Backend
```bash
curl https://ai-followup-crm-backend.onrender.com/docs
curl https://ai-followup-crm-backend.onrender.com/api/dashboard
```

### Frontend
Visit: `https://ai-followup-crm.vercel.app`

Check browser console for API connectivity messages.

---

## Troubleshooting

### Backend won't start on Render
- Check build logs for missing dependencies
- Verify `requirements.txt` has all packages
- Ensure `Procfile` has correct command

### Frontend can't connect to backend
- Verify backend URL in `config.js`
- Check CORS settings in backend's `main.py`
- Ensure `FRONTEND_URL` is set in backend environment variables

### Database issues
- For production, use PostgreSQL instead of SQLite
- Update `DATABASE_URL` to PostgreSQL connection string
- Run migrations if needed

### Environment variables not working
- Redeploy after adding variables
- Check Render/Vercel dashboard for variable visibility
- Use `window.location.hostname` to verify environment

---

## Next Steps

1. **Custom Domain**: Add your domain in Vercel/Render settings
2. **SSL Certificate**: Automatically provided by Vercel/Render
3. **Database**: Upgrade to PostgreSQL for production
4. **Monitoring**: Enable logging/error tracking
5. **CI/CD**: Automatic deployments on git push (enabled by default)

---

## Files Created for Deployment

✅ `vercel.json` - Vercel configuration
✅ `render.yaml` - Render configuration
✅ `Procfile` - Process file for backend
✅ `backend/frontend/config.js` - Environment-aware API config
✅ `backend/.env.example` - Environment variables template

---

## Support

For detailed documentation:
- Vercel: https://vercel.com/docs
- Render: https://render.com/docs
- FastAPI: https://fastapi.tiangolo.com/deployment/

