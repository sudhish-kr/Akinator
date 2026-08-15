"""Add popularity_score to characters for natural gameplay priority."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    if _has_column("characters", "popularity_score"):
        return
    op.add_column(
        "characters",
        sa.Column(
            "popularity_score",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    if not _has_column("characters", "popularity_score"):
        return
    op.drop_column("characters", "popularity_score")
