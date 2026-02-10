"""Tests for NBA constants and team abbreviation standardization."""

from __future__ import annotations

import pytest

from cuic_quant.data.nba.constants import (
    SEASONS,
    STANDARD_TEAM_ABBRS,
    TEAM_ABBR_MAP,
    standardize_team_abbr,
)


class TestTeamAbbreviations:
    """Tests for team abbreviation standardization."""

    def test_all_30_teams_in_standard_list(self) -> None:
        assert len(STANDARD_TEAM_ABBRS) == 30

    def test_standard_abbr_passes_through(self) -> None:
        assert standardize_team_abbr("LAL") == "LAL"
        assert standardize_team_abbr("BOS") == "BOS"
        assert standardize_team_abbr("GSW") == "GSW"

    def test_historical_variants_normalized(self) -> None:
        assert standardize_team_abbr("NJN") == "BKN"
        assert standardize_team_abbr("CHO") == "CHA"
        assert standardize_team_abbr("CHH") == "CHA"
        assert standardize_team_abbr("NOH") == "NOP"
        assert standardize_team_abbr("NOK") == "NOP"
        assert standardize_team_abbr("SEA") == "OKC"
        assert standardize_team_abbr("PHO") == "PHX"

    def test_unknown_abbr_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown team abbreviation"):
            standardize_team_abbr("XXX")

    def test_seasons_list(self) -> None:
        assert SEASONS == ["2021-22", "2022-23", "2023-24", "2024-25"]


class TestTeamAbbrMap:
    """Tests for the abbreviation mapping dict."""

    def test_all_standard_abbrs_map_to_themselves(self) -> None:
        for abbr in STANDARD_TEAM_ABBRS:
            assert TEAM_ABBR_MAP.get(abbr, abbr) == abbr

    def test_map_covers_known_variants(self) -> None:
        variants = ["NJN", "CHO", "CHH", "NOH", "NOK", "SEA", "PHO"]
        for v in variants:
            assert v in TEAM_ABBR_MAP
