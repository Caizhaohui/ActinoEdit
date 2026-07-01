"""Base editing analysis module for ActinoEdit.

Provides computational prediction of base editing outcomes for candidate guides.
Supports Cytosine Base Editor (CBE: C->T) and Adenine Base Editor (ABE: A->G).

This is a *design analysis* tool only. No wet-lab instructions.

Key concepts:
- Editing window: typically positions 4-8 in the spacer (PAM-relative, 1-based from 5' of spacer).
- For guides in CDS: predict codon change, amino acid consequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from actinoedit.core.models import GuideCandidate


@dataclass
class BaseEditPrediction:
    """Prediction for a single guide + base editor combination."""

    guide_id: str
    editor: Literal["CBE", "ABE"]
    editable_bases: list[int]  # 0-based positions in spacer that can be edited
    window: tuple[int, int]  # (start, end) 0-based inclusive in spacer
    predicted_edits: list[dict]  # e.g. [{"pos": 5, "original": "C", "edited": "T", ...}]
    codon_change: str | None = None  # e.g. "ATG -> ATA"
    aa_change: str | None = None  # e.g. "M -> I" or "STOP"
    consequence: str | None = None  # "synonymous", "missense", "nonsense", "no_cds"
    has_early_stop: bool = False


def get_editing_window(spacer_length: int = 20, editor: str = "CBE") -> tuple[int, int]:
    """Return 0-based inclusive editing window for classic SpCas9 editors."""
    # Classic NGG SpCas9: window ~4-8 (1-based positions 4-8 from PAM-distal)
    # 0-based: positions 3-7
    return (3, 7)


def analyze_base_editing(
    guide: GuideCandidate,
    target_sequence: str | None = None,
    editor: Literal["CBE", "ABE"] = "CBE",
    cds_start: int | None = None,
    cds_end: int | None = None,
    is_coding_strand: bool = True,
) -> BaseEditPrediction:
    """Analyze potential base edits for a guide.

    Args:
        guide: The guide candidate.
        target_sequence: The genomic sequence context (at least the spacer + PAM area).
                         If None, limited analysis is performed.
        editor: "CBE" or "ABE".
        cds_start, cds_end: 1-based coordinates of CDS if the guide is in a coding region.
        is_coding_strand: Whether the guide targets the coding (sense) strand.

    Returns:
        BaseEditPrediction with consequences if CDS info provided.
    """
    window = get_editing_window(guide.spacer_length, editor)
    spacer = guide.spacer.upper()
    editable: list[int] = []
    edits: list[dict] = []

    edit_base = "C" if editor == "CBE" else "A"
    new_base = "T" if editor == "CBE" else "G"

    for pos in range(window[0], window[1] + 1):
        if pos < len(spacer) and spacer[pos] == edit_base:
            editable.append(pos)
            edits.append({
                "pos_in_spacer_0based": pos,
                "original": edit_base,
                "edited": new_base,
                "position_1based": pos + 1,
            })

    pred = BaseEditPrediction(
        guide_id=guide.guide_id,
        editor=editor,
        editable_bases=editable,
        window=window,
        predicted_edits=edits,
    )

    # If we have CDS context and sequence, do codon-level prediction (simplified)
    if target_sequence and cds_start and cds_end and len(editable) > 0:
        try:
            # Simplified: assume we have the coding strand sequence for the spacer region
            # In real use the caller would extract proper subsequence + strand handling
            seq = target_sequence.upper()
            # Very simplified codon simulation for demo / unit test purposes
            # Take the middle of the first editable position
            if editable:
                edit_pos = editable[0]
                # Fake a codon around the edit for illustration
                orig_codon = seq[edit_pos:edit_pos+3] if len(seq) > edit_pos + 2 else "NNN"
                if len(orig_codon) < 3:
                    orig_codon = (orig_codon + "NNN")[:3]

                edited_codon_list = list(orig_codon)
                if editor == "CBE" and orig_codon and orig_codon[0] == "C":
                    edited_codon_list[0] = "T"
                elif editor == "ABE" and orig_codon and orig_codon[0] == "A":
                    edited_codon_list[0] = "G"
                edited_codon = "".join(edited_codon_list)

                pred.codon_change = f"{orig_codon} -> {edited_codon}"

                # Extremely simplified AA mapping (real code would use Biopython Seq.translate)
                aa_map: dict[str, str] = {"ATG": "M", "ATA": "I", "TGG": "W", "TGA": "*", "TAG": "*", "TAA": "*"}
                orig_aa = aa_map.get(orig_codon, "X")
                new_aa = aa_map.get(edited_codon, "X")
                pred.aa_change = f"{orig_aa} -> {new_aa}"

                if new_aa == "*" and orig_aa != "*":
                    pred.consequence = "nonsense"
                    pred.has_early_stop = True
                elif new_aa == orig_aa:
                    pred.consequence = "synonymous"
                else:
                    pred.consequence = "missense"
        except Exception:
            pred.consequence = "analysis_error"

    if not cds_start:
        pred.consequence = pred.consequence or "no_cds_context"

    return pred


def batch_analyze_base_editing(
    guides: list[GuideCandidate],
    editor: Literal["CBE", "ABE"] = "CBE",
    get_sequence_func: Any = None,
) -> list[BaseEditPrediction]:
    """Batch version. get_sequence_func(guide) -> str or None for advanced use."""
    results: list[BaseEditPrediction] = []
    for g in guides:
        seq = get_sequence_func(g) if get_sequence_func else None
        results.append(analyze_base_editing(g, seq, editor=editor))
    return results
