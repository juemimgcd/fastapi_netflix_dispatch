"""Fix updated_at server defaults

Revision ID: 7f8c2e1d4b0a
Revises: 20398a750807
Create Date: 2026-03-19 08:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f8c2e1d4b0a"
down_revision: Union[str, Sequence[str], None] = "20398a750807"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = (
    "users",
    "incidents",
    "incident_comments",
    "incident_events",
    "incident_tasks",
    "notifications",
    "teams",
    "team_memberships",
)


def upgrade() -> None:
    """Upgrade schema."""
    for table_name in TABLES:
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(),
            existing_nullable=False,
            server_default=sa.text("now()"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table_name in TABLES:
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(),
            existing_nullable=False,
            server_default=None,
        )
