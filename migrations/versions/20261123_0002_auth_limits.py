"""Limits for log in, verification codes and sessions (penetration test P1, P2 and P3; issue #30).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-23

- user.failed_logins, user.login_paused_until: wrong passwords in a row and the end of the pause they cause.
- user.session_version: part of every session token; log out adds 1, so older copies of a token stop working.
- verification_code.attempts: wrong codes typed for a code; after 5 the code stops working.

Every new column has a default (or may be NULL), so existing rows stay valid and nobody has to log in again
because of the migration itself.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user", sa.Column("failed_logins", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("user", sa.Column("login_paused_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user", sa.Column("session_version", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column(
        "verification_code", sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("verification_code", "attempts")
    op.drop_column("user", "session_version")
    op.drop_column("user", "login_paused_until")
    op.drop_column("user", "failed_logins")
