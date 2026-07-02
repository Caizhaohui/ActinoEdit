"""Initial schema for ActinoEdit v0.2+

Revision ID: 001
Revises:
Create Date: 2026-07-01

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime),
        sa.Column('organism_profile', sa.String),
    )

    op.create_table(
        'genomes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('fasta_path', sa.String),
        sa.Column('contigs', sa.Integer),
        sa.Column('total_length', sa.Integer),
        sa.Column('gc', sa.Float),
        sa.Column('imported_at', sa.DateTime),
    )

    op.create_table(
        'organisms',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('species', sa.String),
        sa.Column('strain', sa.String),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime),
    )

    op.create_table(
        'genes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('genome_id', sa.Integer, sa.ForeignKey('genomes.id')),
        sa.Column('contig', sa.String, nullable=False),
        sa.Column('start', sa.Integer, nullable=False),
        sa.Column('end', sa.Integer, nullable=False),
        sa.Column('strand', sa.String, nullable=False),
        sa.Column('locus_tag', sa.String),
        sa.Column('gene_name', sa.String),
        sa.Column('product', sa.Text),
        sa.Column('feature_type', sa.String),
    )

    op.create_table(
        'bgc',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('genome_id', sa.Integer, sa.ForeignKey('genomes.id')),
        sa.Column('bgc_id', sa.String),
        sa.Column('contig', sa.String),
        sa.Column('start', sa.Integer),
        sa.Column('end', sa.Integer),
        sa.Column('bgc_type', sa.String),
        sa.Column('product', sa.Text),
    )

    op.create_table(
        'guides',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id')),
        sa.Column('guide_id', sa.String),
        sa.Column('contig', sa.String),
        sa.Column('start', sa.Integer),
        sa.Column('end', sa.Integer),
        sa.Column('strand', sa.String),
        sa.Column('spacer', sa.String),
        sa.Column('pam', sa.String),
        sa.Column('gc_content', sa.Float),
        sa.Column('final_score', sa.Float),
        sa.Column('recommendation', sa.String),
        sa.Column('bgc_id', sa.String),
        sa.Column('bgc_context', sa.String),
        sa.Column('off_target_count', sa.Integer),
        sa.Column('created_at', sa.DateTime),
    )

    op.create_table(
        'validation_results',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id')),
        sa.Column('guide_id', sa.String),
        sa.Column('result', sa.String),
        sa.Column('details', sa.Text),
        sa.Column('created_at', sa.DateTime),
    )


def downgrade() -> None:
    op.drop_table('validation_results')
    op.drop_table('guides')
    op.drop_table('bgc')
    op.drop_table('genes')
    op.drop_table('organisms')
    op.drop_table('genomes')
    op.drop_table('projects')
