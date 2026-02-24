"""Initial database tables

Revision ID: 001
Revises:
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database."""
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('framework', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('active', 'archived', name='project_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_projects_user'),
    )

    op.create_table(
        'mindmap_nodes',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('extracted_points', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('unanswered', 'in_progress', 'answered', name='node_status'), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('position', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_nodes_project'),
        sa.ForeignKeyConstraint(['parent_id'], ['mindmap_nodes.id'], name='fk_nodes_parent'),
    )

    op.create_table(
        'conversation_history',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=True),
        sa.Column('role', sa.Enum('user', 'assistant', name='conversation_role'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_conv_project'),
        sa.ForeignKeyConstraint(['node_id'], ['mindmap_nodes.id'], name='fk_conv_node'),
    )

    op.create_table(
        'evolution_history',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('old_answer', sa.Text(), nullable=True),
        sa.Column('new_answer', sa.Text(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['mindmap_nodes.id'], name='fk_evol_node'),
    )


def downgrade() -> None:
    """Downgrade database."""
    op.drop_table('evolution_history')
    op.drop_table('conversation_history')
    op.drop_table('mindmap_nodes')
    op.drop_table('projects')
    op.drop_table('users')
