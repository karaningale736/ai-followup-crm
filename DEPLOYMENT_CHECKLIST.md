# Quick Start Deployment Checklist

## Before Deployment
- [ ] GitHub repository created and pushed
- [ ] All environment variables prepared
- [ ] Vercel and Render accounts created
- [ ] GEMINI_API_KEY obtained (optional, but recommended)

## Backend Deployment (Render)

### Step 1: Create Render Service
- [ ] Go to render.com → New Web Service
- [ ] Connect GitHub repository
- [ ] Set Root Directory to `backend/`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 2: Environment Variables
Add to Render dashboard:
```
DATABASE_URL=sqlite:///./crm.db
FRONTEND_URL=https://ai-followup-crm.vercel.app
GEMINI_API_KEY=your-key-here
SECRET_KEY=your-secret-here
ALLOWED_ORIGINS=https://ai-followup-crm.vercel.app
```

### Step 3: Deploy
- [ ] Click Deploy
- [ ] Wait 3-5 minutes
- [ ] Note your backend URL (e.g., https://ai-followup-crm-backend.onrender.com)

---

## Frontend Deployment (Vercel)

### Step 1: Create Vercel Project
- [ ] Go to vercel.com → Add New Project
- [ ] Import GitHub repository
- [ ] Root Directory: `backend/frontend/`
- [ ] Framework: Other
- [ ] Click Deploy

### Step 2: Update API Configuration
- [ ] Edit `backend/frontend/config.js`
- [ ] Replace `RENDER_BACKEND_URL` with your Render backend URL

### Step 3: Deploy
- [ ] Push changes to GitHub
- [ ] Vercel auto-deploys
- [ ] Your site is live at https://ai-followup-crm.vercel.app

---

## Post-Deployment

### Test Backend
```bash
curl https://your-backend.onrender.com/docs
curl https://your-backend.onrender.com/api/dashboard
```

### Test Frontend
- [ ] Visit https://ai-followup-crm.vercel.app
- [ ] Check browser console (F12)
- [ ] Should see "Backend: online"

### Monitor
- [ ] Check Render logs for errors
- [ ] Check Vercel build/deployment logs
- [ ] Monitor API response times

---

## Rollback
If issues occur:

**Render**: Click Deployment History → Redeploy previous version
**Vercel**: Click Deployments → Select previous version

---

## Estimated Costs
- **Render**: Free tier available (0.5 GB RAM, sleeps after 15 min inactivity)
- **Vercel**: Free tier (unlimited bandwidth)
- **Optional**: GitHub Pro ($4/month) for private repos

