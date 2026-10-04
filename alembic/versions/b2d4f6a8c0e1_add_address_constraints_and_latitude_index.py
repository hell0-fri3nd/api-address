"""add address coordinate constraints and latitude index

Revision ID: b2d4f6a8c0e1
Revises: a1c3e5f7b9d2
Create Date: 2026-10-03 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b2d4f6a8c0e1"
down_revision: Union[str, Sequence[str], None] = "a1c3e5f7b9d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("addresses") as batch_op:
        batch_op.create_check_constraint(
            "ck_addresses_latitude_range", "latitude BETWEEN -90 AND 90"
        )
        batch_op.create_check_constraint(
            "ck_addresses_longitude_range", "longitude BETWEEN -180 AND 180"
        )
        batch_op.create_index("ix_addresses_latitude", ["latitude"])


def downgrade() -> None:
    with op.batch_alter_table("addresses") as batch_op:
        batch_op.drop_index("ix_addresses_latitude")
        batch_op.drop_constraint("ck_addresses_longitude_range", type_="check")
        batch_op.drop_constraint("ck_addresses_latitude_range", type_="check")
