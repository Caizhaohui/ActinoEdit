"""Unique constraints, indexes, and design_runs table.

Revision ID: 003
Revises: 002
Create Date: 2026-07-02

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("organisms") as batch_op:
        batch_op.create_unique_constraint("uq_organisms_name", ["name"])

    with op.batch_alter_table("genomes") as batch_op:
        batch_op.create_unique_constraint("uq_genomes_name", ["name"])
        batch_op.create_index("ix_genomes_organism_id", ["organism_id"])

    op.create_index("ix_genes_genome_id", "genes", ["genome_id"])
    op.create_index("ix_guides_project_id", "guides", ["project_id"])

    op.create_table(
        "design_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("genome_path", sa.String),
        sa.Column("annotation_path", sa.String),
        sa.Column("genome_id", sa.Integer, sa.ForeignKey("genomes.id", ondelete="SET NULL")),
        sa.Column("target", sa.String, nullable=False),
        sa.Column("organism_profile", sa.String),
        sa.Column("pam", sa.String),
        sa.Column("design_mode", sa.String, server_default="knockout"),
        sa.Column("spacer_length", sa.Integer),
        sa.Column("max_mismatches", sa.Integer),
        sa.Column("parameters_json", sa.Text),
        sa.Column("status", sa.String, server_default="completed"),
        sa.Column("started_at", sa.DateTime),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("report_csv_path", sa.String),
        sa.Column("report_xlsx_path", sa.String),
        sa.Column("report_html_path", sa.String),
        sa.Column("guide_count", sa.Integer, server_default="0"),
        sa.Column("warnings_json", sa.Text),
    )
    op.create_index("ix_design_runs_project_id", "design_runs", ["project_id"])

    with op.batch_alter_table("guides") as batch_op:
        batch_op.add_column(sa.Column("design_run_id", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "fk_guides_design_run_id",
            "design_runs",
            ["design_run_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_guides_design_run_id", ["design_run_id"])


def downgrade() -> None:
    with op.batch_alter_table("guides") as batch_op:
        batch_op.drop_index("ix_guides_design_run_id")
        batch_op.drop_constraint("fk_guides_design_run_id", type_="foreignkey")
        batch_op.drop_column("design_run_id")

    op.drop_index("ix_design_runs_project_id", table_name="design_runs")
    op.drop_table("design_runs")

    op.drop_index("ix_guides_project_id", table_name="guides")
    op.drop_index("ix_genes_genome_id", table_name="genes")

    with op.batch_alter_table("genomes") as batch_op:
        batch_op.drop_index("ix_genomes_organism_id")
        batch_op.drop_constraint("uq_genomes_name", type_="unique")

    with op.batch_alter_table("organisms") as batch_op:
        batch_op.drop_constraint("uq_organisms_name", type_="unique")
