"""ASGI application: mounts the FastAPI landing page and the Chainlit chat UI."""
import os

from dotenv import load_dotenv
load_dotenv()  # must run before mount_chainlit calls ensure_jwt_secret()

from fastapi import FastAPI
from chainlit.utils import mount_chainlit

from src.landing import router as landing_router

app = FastAPI(title="HR Assistant")

# KYC landing page at /
app.include_router(landing_router)

# Chainlit chat at /chat  (target is relative to the working directory)
mount_chainlit(app=app, target="src/ui/app.py", path="/chat")
