"""figma models

Revision ID: c8e2f1a9b3d4
Revises: f51aa204b04c
Create Date: 2026-07-04 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c8e2f1a9b3d4'
down_revision = 'f51aa204b04c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'figma_file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('file_key', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('last_modified', sa.String(length=50), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'figma_snapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('figma_file_id', sa.Integer(), nullable=False),
        sa.Column('nodes_json', sa.Text(), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['figma_file_id'], ['figma_file.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'ai_insight',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('insight_type', sa.String(length=50), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('sources_json', sa.Text(), nullable=True),
        sa.Column('changes_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('ai_insight')
    op.drop_table('figma_snapshot')
    op.drop_table('figma_file')
