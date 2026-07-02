"""SQLAlchemy ORM models for ActinoEdit database.

Used for both SQLite and PostgreSQL backends.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base: Any = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    organism_profile = Column(String)
    organism_id = Column(Integer, ForeignKey("organisms.id", ondelete="SET NULL"))
    genome_id = Column(Integer, ForeignKey("genomes.id", ondelete="SET NULL"))


class Genome(Base):
    __tablename__ = "genomes"
    __table_args__ = (
        UniqueConstraint("name", name="uq_genomes_name"),
        Index("ix_genomes_organism_id", "organism_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    fasta_path = Column(String)
    contigs = Column(Integer, default=0)
    total_length = Column(Integer, default=0)
    gc = Column(Float, default=0.0)
    imported_at = Column(DateTime, default=datetime.utcnow)
    organism_id = Column(Integer, ForeignKey("organisms.id", ondelete="SET NULL"))


class Organism(Base):
    __tablename__ = "organisms"
    __table_args__ = (UniqueConstraint("name", name="uq_organisms_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    species = Column(String)
    strain = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Gene(Base):
    __tablename__ = "genes"
    __table_args__ = (Index("ix_genes_genome_id", "genome_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    genome_id = Column(Integer, ForeignKey("genomes.id"))
    contig = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    strand = Column(String, nullable=False)
    locus_tag = Column(String)
    gene_name = Column(String)
    product = Column(Text)
    feature_type = Column(String, default="gene")


class BGC(Base):
    __tablename__ = "bgc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    genome_id = Column(Integer, ForeignKey("genomes.id"))
    bgc_id = Column(String)
    contig = Column(String)
    start = Column(Integer)
    end = Column(Integer)
    bgc_type = Column(String)
    product = Column(Text)


class DesignRun(Base):
    __tablename__ = "design_runs"
    __table_args__ = (Index("ix_design_runs_project_id", "project_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    genome_path = Column(String)
    annotation_path = Column(String)
    genome_id = Column(Integer, ForeignKey("genomes.id", ondelete="SET NULL"))
    target = Column(String, nullable=False)
    organism_profile = Column(String)
    pam = Column(String)
    design_mode = Column(String, default="knockout")
    spacer_length = Column(Integer)
    max_mismatches = Column(Integer)
    parameters_json = Column(Text)
    status = Column(String, default="completed")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    report_csv_path = Column(String)
    report_xlsx_path = Column(String)
    report_html_path = Column(String)
    guide_count = Column(Integer, default=0)
    warnings_json = Column(Text)


class Guide(Base):
    __tablename__ = "guides"
    __table_args__ = (
        Index("ix_guides_project_id", "project_id"),
        Index("ix_guides_design_run_id", "design_run_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    design_run_id = Column(Integer, ForeignKey("design_runs.id", ondelete="SET NULL"))
    guide_id = Column(String)
    contig = Column(String)
    start = Column(Integer)
    end = Column(Integer)
    strand = Column(String)
    spacer = Column(String)
    pam = Column(String)
    gc_content = Column(Float)
    final_score = Column(Float)
    recommendation = Column(String)
    bgc_id = Column(String)
    bgc_context = Column(String)
    off_target_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    guide_id = Column(String)
    result = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
