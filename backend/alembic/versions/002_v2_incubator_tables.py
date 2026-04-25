"""Add v2 incubator tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


conversation_role_v2 = sa.Enum("user", "assistant", name="conversation_role_v2")
message_source_v2 = sa.Enum("chat", "node", "system", name="message_source_v2")
thinking_node_kind = sa.Enum(
    "idea",
    "question",
    "answer",
    "insight",
    "assumption",
    "decision",
    "risk",
    "next_step",
    name="thinking_node_kind",
)
thinking_node_status = sa.Enum("open", "answered", "suggested", "confirmed", name="thinking_node_status")
suggestion_status = sa.Enum("pending", "accepted", "rejected", name="suggestion_status")


def upgrade() -> None:
    """Upgrade database."""
    op.add_column("projects", sa.Column("system_context_version", sa.String(), nullable=False, server_default="v2.0"))
    op.add_column("projects", sa.Column("thinking_stage", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("thinking_mode", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("summary_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_table(
        "thinking_nodes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("kind", thinking_node_kind, nullable=False),
        sa.Column("status", thinking_node_status, nullable=False, server_default="open"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("answer_summary", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("layout", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_message_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_thinking_nodes_project"),
        sa.ForeignKeyConstraint(["parent_id"], ["thinking_nodes.id"], name="fk_thinking_nodes_parent"),
    )

    op.create_table(
        "conversation_messages_v2",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("node_id", sa.UUID(), nullable=True),
        sa.Column("role", conversation_role_v2, nullable=False),
        sa.Column("source", message_source_v2, nullable=False, server_default="chat"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("thinking_mode", sa.String(), nullable=True),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_conversation_messages_v2_project"),
        sa.ForeignKeyConstraint(["node_id"], ["thinking_nodes.id"], name="fk_conversation_messages_v2_node"),
    )

    op.create_table(
        "restructure_suggestions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("status", suggestion_status, nullable=False, server_default="pending"),
        sa.Column("operations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_from_message_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_restructure_suggestions_project"),
        sa.ForeignKeyConstraint(
            ["created_from_message_id"],
            ["conversation_messages_v2.id"],
            name="fk_restructure_suggestions_created_from_message",
        ),
    )

    op.create_table(
        "incubator_runs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_message_id", sa.UUID(), nullable=True),
        sa.Column("assistant_message_id", sa.UUID(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_incubator_runs_project"),
        sa.ForeignKeyConstraint(["user_message_id"], ["conversation_messages_v2.id"], name="fk_incubator_runs_user_message"),
        sa.ForeignKeyConstraint(["assistant_message_id"], ["conversation_messages_v2.id"], name="fk_incubator_runs_assistant_message"),
    )


def downgrade() -> None:
    """Downgrade database."""
    op.drop_table("incubator_runs")
    op.drop_table("restructure_suggestions")
    op.drop_table("conversation_messages_v2")
    op.drop_table("thinking_nodes")

    op.drop_column("projects", "summary_snapshot")
    op.drop_column("projects", "thinking_mode")
    op.drop_column("projects", "thinking_stage")
    op.drop_column("projects", "system_context_version")

    suggestion_status.drop(op.get_bind(), checkfirst=True)
    thinking_node_status.drop(op.get_bind(), checkfirst=True)
    thinking_node_kind.drop(op.get_bind(), checkfirst=True)
    message_source_v2.drop(op.get_bind(), checkfirst=True)
    conversation_role_v2.drop(op.get_bind(), checkfirst=True)
