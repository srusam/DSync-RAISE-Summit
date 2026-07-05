"""github models

Revision ID: e5f8a3b2c9e1d0
Revises: d4a7b2c9e1f0
Create Date: 2026-07-04 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f8a3b2c9e1d0'
down_revision = 'd4a7b2c9e1f0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'github_repo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('owner', sa.String(length=100), nullable=False),
        sa.Column('repo_name', sa.String(length=100), nullable=False),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'pull_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('pr_url', sa.String(length=500), nullable=True),
        sa.Column('diff_files_json', sa.Text(), nullable=True),
        sa.Column('is_design_change', sa.Boolean(), nullable=True),
        sa.Column('mismatch_report', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('pull_request')
    op.drop_table('github_repo')
