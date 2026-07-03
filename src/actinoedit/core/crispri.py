"""CRISPRi guide annotation for ActinoEdit.

Annotates guide candidates with promoter / early-CDS region labels and
strand relationship for transcriptional repression design mode.
"""

from __future__ import annotations

from actinoedit.core.models import GuideCandidate, TargetRegion


def annotate_crispri_guides(
    guides: list[GuideCandidate],
    target_region: TargetRegion,
) -> list[GuideCandidate]:
    """Annotate guides with CRISPRi-specific fields (mutates guides in place).

    Args:
        guides: Guide candidates to annotate.
        target_region: Resolved target gene region.

    Returns:
        The same guide list with CRISPRi fields populated.
    """
    tr = target_region
    is_plus = tr.strand == "+"
    tss = tr.start if is_plus else tr.end
    gene_len = abs(tr.end - tr.start) or 300
    early_cds_threshold = gene_len // 3

    for guide in guides:
        pos = guide.cut_site
        dist = abs(pos - tss)
        guide.distance_to_start_codon = dist

        if is_plus:
            if pos < tss:
                guide.crispri_region_type = "promoter"
            elif pos < tss + early_cds_threshold:
                guide.crispri_region_type = "early_cds"
            else:
                guide.crispri_region_type = "cds"
        else:
            if pos > tss:
                guide.crispri_region_type = "promoter"
            elif pos > tss - early_cds_threshold:
                guide.crispri_region_type = "early_cds"
            else:
                guide.crispri_region_type = "cds"

        guide.target_strand_relation = (
            "non_template" if guide.strand == tr.strand else "template"
        )

    return guides
