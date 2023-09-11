from fastapi import Request, Depends

from backend import db
from backend.http import APIRouter, PayPalAPI

router = APIRouter("webhooks")
