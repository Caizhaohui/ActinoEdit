"""K-mer seed index for fast genome-wide off-target search.

Builds a cached inverted index over contig sequences so each guide reuses
one genome index instead of scanning every contig per guide.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import lru_cache

from actinoedit.core.models import Contig, GuideCandidate, OffTargetHit
from actinoedit.core.offtarget import _count_mismatches, _get_mismatch_positions
from actinoedit.core.sequence import reverse_complement

DEFAULT_SEED_K = 12


@dataclass(frozen=True)
class _IndexHit:
    contig: str
    position: int
    strand: str


@dataclass
class GenomeOffTargetIndex:
    """Inverted k-mer index for a loaded genome."""

    contigs: dict[str, Contig]
    seed_k: int = DEFAULT_SEED_K
    _forward_index: dict[str, list[_IndexHit]] = field(default_factory=dict)
    _reverse_index: dict[str, list[_IndexHit]] = field(default_factory=dict)
    _forward_sequences: dict[str, str] = field(default_factory=dict)
    _reverse_sequences: dict[str, str] = field(default_factory=dict)

    @classmethod
    def build(cls, contigs: dict[str, Contig], seed_k: int = DEFAULT_SEED_K) -> GenomeOffTargetIndex:
        """Build a seed index from contig sequences."""
        index = cls(contigs=contigs, seed_k=seed_k)
        for contig_name, contig in contigs.items():
            sequence = contig.sequence.upper()
            rc_sequence = reverse_complement(sequence)
            index._forward_sequences[contig_name] = sequence
            index._reverse_sequences[contig_name] = rc_sequence
            index._index_strand(sequence, contig_name, "+", index._forward_index)
            index._index_strand(rc_sequence, contig_name, "-", index._reverse_index)
        return index

    def _index_strand(
        self,
        sequence: str,
        contig_name: str,
        strand: str,
        store: dict[str, list[_IndexHit]],
    ) -> None:
        seed_k = self.seed_k
        seq_len = len(sequence)
        if seq_len < seed_k:
            return
        for i in range(seq_len - seed_k + 1):
            seed = sequence[i : i + seed_k]
            store.setdefault(seed, []).append(_IndexHit(contig_name, i, strand))

    def search_guide(
        self,
        guide: GuideCandidate,
        max_mismatches: int = 3,
        ignore_on_target: bool = True,
    ) -> list[OffTargetHit]:
        """Search off-targets for one guide using the cached index."""
        spacer = guide.spacer.upper()
        spacer_len = len(spacer)
        if spacer_len == 0:
            return []

        seeds: set[str] = set()
        if spacer_len >= self.seed_k:
            for offset in range(spacer_len - self.seed_k + 1):
                seeds.add(spacer[offset : offset + self.seed_k])
            # Also index seeds from RC spacer so minus-strand hits are not missed.
            rc_spacer = reverse_complement(spacer)
            for offset in range(spacer_len - self.seed_k + 1):
                seeds.add(rc_spacer[offset : offset + self.seed_k])
        else:
            seeds.add(spacer)
            seeds.add(reverse_complement(spacer))

        candidates: list[_IndexHit] = []
        for seed in seeds:
            candidates.extend(self._forward_index.get(seed, []))
            candidates.extend(self._reverse_index.get(seed, []))

        hits: list[OffTargetHit] = []
        seen: set[tuple[str, int, str]] = set()

        for candidate in candidates:
            if candidate.strand == "+":
                sequence = self._forward_sequences[candidate.contig]
            else:
                sequence = self._reverse_sequences[candidate.contig]

            max_offset = spacer_len - self.seed_k
            for align_offset in range(max_offset + 1):
                start_pos = candidate.position - align_offset
                if start_pos < 0:
                    continue
                key = (candidate.contig, start_pos, candidate.strand)
                if key in seen:
                    continue

                window = sequence[start_pos : start_pos + spacer_len]
                if len(window) != spacer_len:
                    continue

                mismatches = _count_mismatches(spacer, window)
                if mismatches > max_mismatches:
                    continue

                seen.add(key)
                hits.append(
                    OffTargetHit(
                        guide_id=guide.guide_id,
                        contig=candidate.contig,
                        start=start_pos + 1,
                        end=start_pos + spacer_len,
                        strand=candidate.strand,
                        sequence=window,
                        mismatch_count=mismatches,
                        mismatch_positions=_get_mismatch_positions(spacer, window),
                    )
                )

        if ignore_on_target:
            hits = [
                h
                for h in hits
                if not (
                    h.contig == guide.contig
                    and h.start == guide.start
                    and h.mismatch_count == 0
                )
            ]
        return hits


def genome_cache_key(contigs: dict[str, Contig]) -> str:
    """Stable cache key from contig metadata (no full sequence hash)."""
    parts: list[str] = []
    for name in sorted(contigs):
        contig = contigs[name]
        seq = contig.sequence
        digest = hashlib.md5(seq.encode("ascii"), usedforsecurity=False).hexdigest()[:12]
        parts.append(f"{name}:{contig.length}:{digest}")
    return "|".join(parts)


@lru_cache(maxsize=8)
def get_genome_index(cache_key: str, contigs: tuple[tuple[str, str], ...], seed_k: int) -> GenomeOffTargetIndex:
    """Return a cached index; ``contigs`` is a tuple of (name, sequence) pairs."""
    contig_map = {name: Contig(name=name, sequence=seq) for name, seq in contigs}
    return GenomeOffTargetIndex.build(contig_map, seed_k=seed_k)


def get_or_build_index(contigs: dict[str, Contig], seed_k: int = DEFAULT_SEED_K) -> GenomeOffTargetIndex:
    """Build or retrieve a cached genome off-target index."""
    key = genome_cache_key(contigs)
    frozen = tuple((name, contigs[name].sequence) for name in sorted(contigs))
    return get_genome_index(key, frozen, seed_k)


def clear_index_cache() -> None:
    """Clear the LRU cache (useful in tests)."""
    get_genome_index.cache_clear()
