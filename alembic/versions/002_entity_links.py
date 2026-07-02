"""Link organisms, genomes, and projects.

Revision ID: 002
Revises: 001
Create Date: 2026-07-02

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("genomes") as batch_op:
        batch_op.add_column(sa.Column("organism_id", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "fk_genomes_organism_id",
            "organisms",
            ["organism_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(sa.Column("organism_id", sa.Integer, nullable=True))
        batch_op.add_column(sa.Column("genome_id", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "fk_projects_organism_id",
            "organisms",
            ["organism_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_projects_genome_id",
            "genomes",
            ["genome_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("fk_projects_genome_id", type_="foreignkey")
        batch_op.drop_constraint("fk_projects_organism_id", type_="foreignkey")
        batch_op.drop_column("genome_id")
        batch_op.drop_column("organism_id")

    with op.batch_alter_table("genomes") as batch_op:
        batch_op.drop_constraint("fk_genomes_organism_id", type_="foreignkey")
        batch_op.drop_column("organism_id")
