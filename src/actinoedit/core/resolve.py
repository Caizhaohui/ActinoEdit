"""Resolve design parameters without mutating caller input."""

from __future__ import annotations

from dataclasses import dataclass

from actinoedit.core.design_types import DesignInput
from actinoedit.core.models import OrganismProfile
from actinoedit.core.profiles import get_profile_or_default


@dataclass(frozen=True)
class ResolvedDesignParams:
    """Effective parameters used for a design run."""

    genome_path: str
    annotation_path: str
    target: str
    pam: str
    spacer_length: int
    max_mismatches: int
    organism_profile: str | None
    profile_name: str
    output_prefix: str
    bgc_path: str | None
    design_mode: str

    def as_dict(self) -> dict[str, str | int | None]:
        """Serialize for reports and database audit fields."""
        return {
            "genome_path": self.genome_path,
            "annotation_path": self.annotation_path,
            "target": self.target,
            "pam": self.pam,
            "spacer_length": self.spacer_length,
            "max_mismatches": self.max_mismatches,
            "organism_profile": self.organism_profile,
            "profile_name": self.profile_name,
            "output_prefix": self.output_prefix,
            "bgc_path": self.bgc_path,
            "design_mode": self.design_mode,
        }


def resolve_profile_params(
    input_params: DesignInput,
    profile: OrganismProfile,
) -> tuple[str, int, int]:
    """Apply profile defaults when the caller left factory defaults."""
    pam = input_params.pam
    spacer_length = input_params.spacer_length
    max_mismatches = input_params.max_mismatches

    if pam == "NGG" and profile.default_pam != "NGG":
        pam = profile.default_pam
    if spacer_length == 20 and profile.spacer_length != 20:
        spacer_length = profile.spacer_length
    if max_mismatches == 3 and profile.max_mismatches != 3:
        max_mismatches = profile.max_mismatches

    return pam, spacer_length, max_mismatches


def resolve_design_params(input_params: DesignInput) -> ResolvedDesignParams:
    """Resolve effective design parameters without mutating ``input_params``."""
    profile = get_profile_or_default(input_params.organism_profile)
    pam, spacer_length, max_mismatches = resolve_profile_params(input_params, profile)
    profile_name = profile.name if input_params.organism_profile else "default"

    return ResolvedDesignParams(
        genome_path=input_params.genome_path,
        annotation_path=input_params.annotation_path,
        target=input_params.target,
        pam=pam,
        spacer_length=spacer_length,
        max_mismatches=max_mismatches,
        organism_profile=input_params.organism_profile,
        profile_name=profile_name,
        output_prefix=input_params.output_prefix,
        bgc_path=input_params.bgc_path,
        design_mode=input_params.design_mode,
    )
