"""initial BarberSaaS schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(255)),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_businesses_slug", "businesses", ["slug"])

    op.create_table(
        "business_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "user_id", name="uq_business_member"),
        sa.CheckConstraint("role IN ('owner','barber','client')", name="ck_business_member_role"),
    )
    op.create_index("ix_business_members_business_id", "business_members", ["business_id"])
    op.create_index("ix_business_members_user_id", "business_members", ["user_id"])

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("duration_minutes > 0 AND duration_minutes <= 480", name="ck_service_duration"),
        sa.CheckConstraint("price_minor >= 0", name="ck_service_price_nonnegative"),
    )
    op.create_index("ix_services_business_id", "services", ["business_id"])

    op.create_table(
        "working_intervals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("barber_member_id", sa.Integer(), sa.ForeignKey("business_members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_weekday"),
    )
    op.create_index("ix_working_intervals_barber_member_id", "working_intervals", ["barber_member_id"])

    op.create_table(
        "schedule_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("barber_member_id", sa.Integer(), sa.ForeignKey("business_members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="ck_schedule_block_time_order"),
    )
    op.create_index("ix_schedule_blocks_barber_member_id", "schedule_blocks", ["barber_member_id"])
    op.create_index("ix_schedule_blocks_starts_at", "schedule_blocks", ["starts_at"])
    op.create_index("ix_schedule_blocks_ends_at", "schedule_blocks", ["ends_at"])

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "user_id", name="uq_client_business_user"),
    )
    op.create_index("ix_clients_business_id", "clients", ["business_id"])
    op.create_index("ix_clients_user_id", "clients", ["user_id"])

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("barber_member_id", sa.Integer(), sa.ForeignKey("business_members.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="confirmed"),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("reminder_task_id", sa.String(255)),
        sa.CheckConstraint("ends_at > starts_at", name="ck_appointment_time_order"),
        sa.CheckConstraint("price_minor >= 0", name="ck_appointment_price_nonnegative"),
        sa.CheckConstraint("status IN ('pending','confirmed','completed','cancelled','no_show')", name="ck_appointment_status"),
    )
    for name, cols in (
        ("ix_appointments_business_id", ["business_id"]),
        ("ix_appointments_barber_member_id", ["barber_member_id"]),
        ("ix_appointments_client_id", ["client_id"]),
        ("ix_appointments_service_id", ["service_id"]),
        ("ix_appointments_starts_at", ["starts_at"]),
        ("ix_appointments_ends_at", ["ends_at"]),
        ("ix_appointments_status", ["status"]),
    ):
        op.create_index(name, "appointments", cols)

    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_by_member_id", sa.Integer(), sa.ForeignKey("business_members.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="barber"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invitations_business_id", "invitations", ["business_id"])
    op.create_index("ix_invitations_token_hash", "invitations", ["token_hash"])
    op.create_index("ix_invitations_expires_at", "invitations", ["expires_at"])

    op.execute("""
        ALTER TABLE appointments
        ADD CONSTRAINT appointments_no_overlap
        EXCLUDE USING gist (
            barber_member_id WITH =,
            tstzrange(starts_at, ends_at, '[)') WITH &&
        )
        WHERE (status IN ('pending', 'confirmed'));
    """)


def downgrade() -> None:
    op.drop_constraint("appointments_no_overlap", "appointments", type_="exclude")
    op.drop_table("invitations")
    op.drop_table("appointments")
    op.drop_table("clients")
    op.drop_table("schedule_blocks")
    op.drop_table("working_intervals")
    op.drop_table("services")
    op.drop_table("business_members")
    op.drop_table("businesses")
    op.drop_table("users")
