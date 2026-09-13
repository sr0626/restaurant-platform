"""Phase 1 initial schema — all 11 core entities.

Creates, in FK dependency order: owner_account, restaurant_brand,
restaurant_location, cuisine_tag, restaurant_cuisine, location_manager,
user_follow, audit_log, platform_pricing, admin_free_offer,
restaurant_hours.

Hand-authored (not run through `alembic revision --autogenerate`
against a live database — see root CLAUDE.md "NEVER run Alembic
migrations — generate migration files only"). Content matches the
models in `app/models/` exactly; see `docs/DATA_MODEL.md` for the
column-by-column rationale.

Revision ID: 0001_initial_phase1_schema
Revises:
Create Date: 2026-09-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_phase1_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS is required for the geography column on restaurant_location
    # (root CLAUDE.md "Database: Aurora PostgreSQL Serverless v2 +
    # PostGIS extension"). Idempotent — safe to re-run.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # --- owner_account ----------------------------------------------
    op.create_table(
        "owner_account",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("cognito_sub", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_sub_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cognito_sub"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("stripe_sub_id"),
    )

    # --- restaurant_brand ---------------------------------------------
    op.create_table(
        "restaurant_brand",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_claimed", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["owner_account.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        "ix_restaurant_brand_owner_id", "restaurant_brand", ["owner_id"]
    )

    # --- restaurant_location ------------------------------------------
    op.create_table(
        "restaurant_location",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("brand_id", sa.BigInteger(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=False),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("postal_code", sa.String(length=10), nullable=False),
        sa.Column(
            "country", sa.String(length=2), server_default="US", nullable=False
        ),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column(
            "timezone",
            sa.String(length=64),
            server_default="America/Chicago",
            nullable=False,
        ),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "geom",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column(
            "is_paid", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("paid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_sub_item_id", sa.String(length=255), nullable=True),
        sa.Column(
            "is_verified", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["restaurant_brand.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_sub_item_id"),
    )
    op.create_index(
        "ix_restaurant_location_brand_id", "restaurant_location", ["brand_id"]
    )
    # GIST index for PostGIS radius search (ST_DWithin) — root CLAUDE.md
    # "geom | geography(Point, 4326) | PostGIS, indexed GIST".
    op.create_index(
        "ix_restaurant_location_geom",
        "restaurant_location",
        ["geom"],
        postgresql_using="gist",
    )

    # --- cuisine_tag ----------------------------------------------------
    op.create_table(
        "cuisine_tag",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_cuisine_tag_category", "cuisine_tag", ["category"])

    # --- restaurant_cuisine (join table, brand-level — see model docstring) --
    op.create_table(
        "restaurant_cuisine",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("brand_id", sa.BigInteger(), nullable=False),
        sa.Column("cuisine_tag_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["restaurant_brand.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["cuisine_tag_id"], ["cuisine_tag.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "brand_id", "cuisine_tag_id", name="uq_restaurant_cuisine_brand_tag"
        ),
    )
    op.create_index(
        "ix_restaurant_cuisine_brand_id", "restaurant_cuisine", ["brand_id"]
    )
    op.create_index(
        "ix_restaurant_cuisine_cuisine_tag_id",
        "restaurant_cuisine",
        ["cuisine_tag_id"],
    )

    # --- location_manager ------------------------------------------------
    op.create_table(
        "location_manager",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("assigned_by_owner_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["restaurant_location.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_owner_id"], ["owner_account.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_location_manager_location_active",
        "location_manager",
        ["location_id", "is_active"],
    )
    op.create_index("ix_location_manager_user_id", "location_manager", ["user_id"])
    # Partial unique index: a user may hold only one *active* assignment
    # row per location at a time (data-integrity backstop — the "max 2
    # per location" cap itself is enforced by Backend Dev's service
    # layer, not by this constraint; see model docstring).
    op.create_index(
        "uq_location_manager_active_user",
        "location_manager",
        ["location_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    # --- user_follow -------------------------------------------------
    op.create_table(
        "user_follow",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("brand_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["restaurant_brand.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "brand_id", name="uq_user_follow_user_brand"
        ),
    )
    op.create_index("ix_user_follow_user_id", "user_follow", ["user_id"])
    op.create_index("ix_user_follow_brand_id", "user_follow", ["brand_id"])

    # --- audit_log -----------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("table_name", sa.String(length=64), nullable=False),
        sa.Column("record_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("actor_role", sa.String(length=16), nullable=False),
        sa.Column(
            "old_val", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "new_val", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_log_table_record", "audit_log", ["table_name", "record_id"]
    )

    # --- platform_pricing -----------------------------------------------
    op.create_table(
        "platform_pricing",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("monthly_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("yearly_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="USD", nullable=False
        ),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_platform_pricing_effective_date",
        "platform_pricing",
        ["effective_date"],
    )

    # --- admin_free_offer --------------------------------------------
    op.create_table(
        "admin_free_offer",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("granted_by", sa.String(length=64), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["owner_account.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_free_offer_owner_id", "admin_free_offer", ["owner_id"]
    )

    # --- restaurant_hours -----------------------------------------------
    op.create_table(
        "restaurant_hours",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=True),
        sa.Column("close_time", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["restaurant_location.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "location_id", "day_of_week", name="uq_restaurant_hours_location_day"
        ),
    )
    op.create_index(
        "ix_restaurant_hours_location_id", "restaurant_hours", ["location_id"]
    )


def downgrade() -> None:
    # Reverse FK dependency order.
    op.drop_table("restaurant_hours")
    op.drop_table("admin_free_offer")
    op.drop_table("platform_pricing")
    op.drop_table("audit_log")
    op.drop_table("user_follow")
    op.drop_table("location_manager")
    op.drop_table("restaurant_cuisine")
    op.drop_table("cuisine_tag")
    op.drop_index("ix_restaurant_location_geom", table_name="restaurant_location")
    op.drop_table("restaurant_location")
    op.drop_table("restaurant_brand")
    op.drop_table("owner_account")
    # Deliberately NOT dropping the postgis extension — other schemas /
    # objects in the same database may depend on it.
