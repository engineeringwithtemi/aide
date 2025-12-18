from fastapi import APIRouter
from typing import Any

# Create router with global dependencies - all routes will require authentication
router = APIRouter()


router.get("")


async def get_all_workspaces() -> Any:
    pass
