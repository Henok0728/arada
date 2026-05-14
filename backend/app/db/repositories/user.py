"""
UserRepository — queries for the User model.

Used by the auth service for login credential lookup.
All password operations happen in services/auth.py, never here.
"""
from typing import Optional

from sqlalchemy import select

from app.db.models.user import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD."""

    model = User

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by their email address. Returns None if not found."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def is_email_taken(self, email: str) -> bool:
        """Return True if the email is already registered."""
        return await self.get_by_email(email) is not None
