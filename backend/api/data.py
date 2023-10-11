""" /api/data """
import time
import secrets
import threading
from pathlib import PosixPath

from fastapi import Body, HTTPException

from backend import db
from backend.http import APIRouter
from backend.system import run_async
from backend.system import SECRETS, EFS_VOLUME_PATH

router = APIRouter("data")


@router.professional.get("/test")
async def login(user=router.professional.auth):
    return user
