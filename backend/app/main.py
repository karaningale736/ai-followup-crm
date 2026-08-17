import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.routers import auth, clients, followups, dashboard, templates, emails, meetings, agreements, responses

app = FastAPI(
    title="AI Client Follow-Up & CRM Automation System",
    description="Deterministic follow-up/next-action/template engine with AI personalization.",
    version="1.0.0",
)

frontend_url = settings.frontend_url
origins = list(dict.fromkeys([frontend_url, *settings.allowed_origins]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(followups.router)
app.include_router(dashboard.router)
app.include_router(templates.router)
app.include_router(emails.router)
app.include_router(meetings.router)
app.include_router(agreements.router)
app.include_router(responses.router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return FileResponse("frontend/crm-ui.html")


@app.get("/crm")
def crm_ui():
    return FileResponse("frontend/crm-ui.html")


@app.get("/health")
def health():
    return {"status": "healthy"}
