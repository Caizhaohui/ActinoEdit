"""Tests for organism profile module."""

from pathlib import Path

import pytest

from actinoedit.core.models import OrganismProfile
from actinoedit.core.profiles import (
    get_profile_or_default,
    list_profiles,
    load_all_profiles,
    load_profile,
)


@pytest.fixture
def profiles_dir() -> Path:
    """Get the default profiles directory."""
    return Path(__file__).parent.parent / "examples" / "profiles"


class TestLoadProfile:
    """Tests for load_profile function."""

    def test_load_streptomyces(self, profiles_dir: Path) -> None:
        """Test loading streptomyces profile."""
        profile = load_profile("streptomyces", profiles_dir)
        assert isinstance(profile, OrganismProfile)
        assert profile.name == "streptomyces"
        assert profile.default_pam == "NGG"

    def test_load_ecoli(self, profiles_dir: Path) -> None:
        """Test loading E. coli profile."""
        profile = load_profile("ecoli", profiles_dir)
        assert profile.name == "ecoli"

    def test_load_not_found(self, profiles_dir: Path) -> None:
        """Test loading nonexistent profile."""
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent", profiles_dir)


class TestListProfiles:
    """Tests for list_profiles function."""

    def test_list(self, profiles_dir: Path) -> None:
        """Test listing profiles."""
        profiles = list_profiles(profiles_dir)
        assert len(profiles) > 0
        assert "streptomyces" in profiles
        assert "ecoli" in profiles


class TestLoadAllProfiles:
    """Tests for load_all_profiles function."""

    def test_load_all(self, profiles_dir: Path) -> None:
        """Test loading all profiles."""
        profiles = load_all_profiles(profiles_dir)
        assert len(profiles) > 0
        assert "streptomyces" in profiles


class TestGetProfileOrDefault:
    """Tests for get_profile_or_default function."""

    def test_get_named(self, profiles_dir: Path) -> None:
        """Test getting named profile."""
        profile = get_profile_or_default("streptomyces", profiles_dir)
        assert profile.name == "streptomyces"

    def test_get_default(self) -> None:
        """Test getting default profile."""
        profile = get_profile_or_default(None)
        assert profile.name == "default"
