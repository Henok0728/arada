"""
APIKey ORM model — platform.api_keys table.

Security design (CLAUDE.md §Key API Patterns):
  - The plaintext key (`ll_dev_<48-char-base62>` or `ll_live_<48-char-base62>`)
    is shown EXACTLY ONCE at generation time and is never persisted anywhere.
  - Only `SHA-256(plaintext_key)` is stored in `key_hash`.
  - `key_prefix` stores the first 16 characters of the plaintext key so
    receptionists can identify which key is which without revealing the secret.
  - `environment` stores "dev" or "live" which corresponds to the prefix in the
    key itself (`ll_dev_` vs `ll_live_`).

Scope constants are defined here and validated in the auth service.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.hotel import Hotel


# ---------------------------------------------------------------------------
# Valid API key scopes (enforced at the service layer)
# ---------------------------------------------------------------------------
VALID_SCOPES: list[str] = [
    "availability:read",
    "availability:write",
    "referral:create",
    "referral:read",
    "referral:confirm",
    "trust:read",
    "analytics:read",
]

# ---------------------------------------------------------------------------
# Key environment constants
# ---------------------------------------------------------------------------
ENV_DEV = "dev"
ENV_LIVE = "live"
KEY_PREFIX_MAP = {
    ENV_DEV: "ll_dev_",
    ENV_LIVE: "ll_live_",
}


class APIKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a hashed API key credential for a hotel partner.

    Schema: `platform`.
    Plaintext keys are NEVER stored — only their SHA-256 digest.
    """

    __tablename__ = "api_keys"
    __table_args__ = {"schema": "platform"}

    # ---- Hotel tenancy --------------------------------------------------
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform.hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---- Key material ---------------------------------------------------
    # SHA-256 hex digest of the full plaintext key — indexed for O(1) lookup.
    key_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 → 64 hex chars
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256(plaintext_key) — never store the plaintext",
    )
    # Safe display prefix: first 16 chars of plaintext (e.g. "ll_dev_aB3kR9...")
    key_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="First 16 chars of plaintext key for UI identification",
    )

    # ---- Environment + Scopes -------------------------------------------
    environment: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=ENV_DEV,
        comment="'dev' or 'live' — matches ll_dev_ / ll_live_ prefix",
    )
    # PostgreSQL native ARRAY(TEXT) for scopes — fast for overlap queries.
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        comment="Granted permission scopes, e.g. ['availability:read','referral:create']",
    )

    # ---- Metadata -------------------------------------------------------
    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Human-readable label, e.g. 'Receptionist desk key'",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_at: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="ISO datetime of last successful authentication"
    )
    expires_at: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="ISO datetime; null = non-expiring"
    )

    # ---- Relationships --------------------------------------------------
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="api_keys")

    def __repr__(self) -> str:
        return (
            f"<APIKey id={self.id} prefix={self.key_prefix!r} "
            f"env={self.environment} active={self.is_active}>"
        )
