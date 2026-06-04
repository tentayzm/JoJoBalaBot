"""Handlers package."""
from aiogram import Router

from . import commands, text, photo


def setup_handlers() -> Router:
    """
    Setup all handlers.
    
    Returns:
        Router with all handlers registered
    """
    router = Router()
    
    # Include all handler routers
    router.include_router(commands.router)
    router.include_router(photo.router)
    router.include_router(text.router)
    
    return router