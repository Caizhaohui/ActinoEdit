"""Tests for k-mer seed off-target index."""

from __future__ import annotations

from actinoedit.core.models import Contig, GuideCandidate
from actinoedit.core.offtarget import search_offtargets
from actinoedit.core.offtarget_index import (
    GenomeOffTargetIndex,
    clear_index_cache,
    get_or_build_index,
)


def _sample_guide() -> GuideCandidate:
    return GuideCandidate(
        guide_id="guide_001",
        contig="contig1",
        spacer="ATCGATCGATCGATCGATCG",
        pam="NGG",
        start=100,
        end=119,
        strand="+",
        pam_start=120,
        pam_end=122,
        cut_site=117,
        gc_content=0.5,
    )


def _sample_contigs() -> dict[str, Contig]:
    seq1 = "N" * 99 + "ATCGATCGATCGATCGATCG" + "N" * 100
    seq1 += "ATCGATCGATCGATCGATCN" + "N" * 50
    seq1 += "NNNNATCGATCGATCGATCG" + "N" * 50
    return {
        "contig1": Contig(name="contig1", sequence=seq1),
        "contig2": Contig(name="contig2", sequence="N" * 500),
    }


def test_index_matches_brute_force() -> None:
    guide = _sample_guide()
    contigs = _sample_contigs()
    index = GenomeOffTargetIndex.build(contigs)

    brute = search_offtargets(guide, contigs, max_mismatches=3, ignore_on_target=True)
    indexed = index.search_guide(guide, max_mismatches=3, ignore_on_target=True)

    brute_keys = {(h.contig, h.start, h.strand, h.mismatch_count) for h in brute}
    indexed_keys = {(h.contig, h.start, h.strand, h.mismatch_count) for h in indexed}
    assert brute_keys == indexed_keys


def test_cached_index_reuse() -> None:
    clear_index_cache()
    contigs = _sample_contigs()
    index1 = get_or_build_index(contigs)
    index2 = get_or_build_index(contigs)
    assert index1 is index2
