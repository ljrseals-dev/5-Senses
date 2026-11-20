"""Tests for mode selection."""

from body_of_secrets.brain.modes import Mode, get_mode, MODES


def test_all_modes_present():
    expected = {"CLASSICAL", "RESEARCH", "ARCHIVE", "AUDIT", "HYBRID"}
    assert set(m.value for m in Mode if m != Mode.AUTO) == expected


def test_get_mode_classical():
    spec = get_mode("CLASSICAL")
    assert spec.name == Mode.CLASSICAL
    assert "CLASSICAL" in spec.system_addendum


def test_get_mode_case_insensitive():
    spec = get_mode("research")
    assert spec.name == Mode.RESEARCH


def test_unknown_mode_raises():
    import pytest
    with pytest.raises(ValueError):
        get_mode("NONEXISTENT")
