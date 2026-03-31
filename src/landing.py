"""FastAPI router that serves the KYC landing page."""
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src import session_store

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/submit")
async def submit(
    name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...),
    position: str = Form(...),
):
    user_data = {
        "name": name.strip(),
        "email": email.strip(),
        "department": department.strip(),
        "position": position.strip(),
    }
    token = session_store.create_session(user_data)
    logger.info("KYC session created for %s (%s)", name, email)

    response = RedirectResponse(url="/chat", status_code=303)
    response.set_cookie(
        key="hr_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600,  # 1 hour
    )
    return response
