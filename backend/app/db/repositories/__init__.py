"""
Repository package — re-exports all repository classes.

Usage in services / route dependencies:
    from app.db.repositories import HotelRepository
    repo = HotelRepository(session)
"""
from app.db.repositories.base import BaseRepository
from app.db.repositories.hotel import HotelRepository

__all__ = [
    "BaseRepository",
    "HotelRepository",
]
