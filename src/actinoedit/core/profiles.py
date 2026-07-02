"""Organism profile management for ActinoEdit.

This module provides functions for loading and managing organism-specific
design profiles.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from actinoedit.core.models import OrganismProfile


def _default_profiles_dir() -> Path:
    from actinoedit.resources import get_profiles_dir

    return get_profiles_dir()

# Built-in profile names
BUILTIN_PROFILES = [
    "actinomycete",
    "streptomyces",
    "ecoli",
    "bacillus",
    "yeast",
    "custom",
]


def load_profile(
    name: str,
    profiles_dir: Path | None = None,
) -> OrganismProfile:
    """Load an organism profile by name.

    Args:
        name: Profile name (e.g., "streptomyces", "ecoli").
        profiles_dir: Directory containing profile YAML files.
                      If None, uses default examples/profiles directory.

    Returns:
        OrganismProfile object.

    Raises:
        FileNotFoundError: If profile file not found.
        ValueError: If profile data is invalid.
    """
    if profiles_dir is None:
        profiles_dir = _default_profiles_dir()

    profile_path = profiles_dir / f"{name}.yaml"

    if not profile_path.exists():
        raise FileNotFoundError(
            f"Profile '{name}' not found at {profile_path}. "
            f"Available profiles: {list_profiles(profiles_dir)}"
        )

    with open(profile_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Empty profile file: {profile_path}")

    return OrganismProfile.from_dict(data)


def list_profiles(profiles_dir: Path | None = None) -> list[str]:
    """List available organism profiles.

    Args:
        profiles_dir: Directory containing profile YAML files.

    Returns:
        List of profile names.
    """
    if profiles_dir is None:
        profiles_dir = _default_profiles_dir()

    if not profiles_dir.exists():
        return []

    profiles = []
    for path in profiles_dir.glob("*.yaml"):
        profiles.append(path.stem)

    return sorted(profiles)


def load_all_profiles(
    profiles_dir: Path | None = None,
) -> dict[str, OrganismProfile]:
    """Load all available organism profiles.

    Args:
        profiles_dir: Directory containing profile YAML files.

    Returns:
        Dictionary mapping profile names to OrganismProfile objects.
    """
    profiles: dict[str, OrganismProfile] = {}

    for name in list_profiles(profiles_dir):
        try:
            profiles[name] = load_profile(name, profiles_dir)
        except (ValueError, FileNotFoundError):
            # Skip invalid profiles
            continue

    return profiles


def get_profile_or_default(
    name: str | None = None,
    profiles_dir: Path | None = None,
) -> OrganismProfile:
    """Get a profile by name, or return default profile.

    Args:
        name: Profile name. If None, returns default profile.
        profiles_dir: Directory containing profile YAML files.

    Returns:
        OrganismProfile object.
    """
    if name is None:
        # Return default streptomyces profile
        return OrganismProfile(
            name="default",
            display_name="Default",
        )

    return load_profile(name, profiles_dir)


def save_profile(
    profile: OrganismProfile,
    profiles_dir: Path | None = None,
) -> Path:
    """Save an organism profile to a YAML file.

    Args:
        profile: OrganismProfile object.
        profiles_dir: Directory to save profile.

    Returns:
        Path to saved profile file.
    """
    if profiles_dir is None:
        profiles_dir = _default_profiles_dir()

    profiles_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profiles_dir / f"{profile.name}.yaml"

    data = {
        "name": profile.name,
        "display_name": profile.display_name,
        "default_pam": profile.default_pam,
        "spacer_length": profile.spacer_length,
        "max_mismatches": profile.max_mismatches,
        "recommended_gc_min": profile.recommended_gc_min,
        "recommended_gc_max": profile.recommended_gc_max,
        "high_gc_warning_threshold": profile.high_gc_warning_threshold,
        "prefer_cds_first_third_for_knockout": profile.prefer_cds_first_third_for_knockout,
        "enable_bgc_annotation": profile.enable_bgc_annotation,
        "offtarget_strictness": profile.offtarget_strictness,
    }

    with open(profile_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    return profile_path
