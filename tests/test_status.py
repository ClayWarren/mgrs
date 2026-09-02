import warnings

import pytest

import mgrs
from mgrs import core


def test_mgrs_to_utm_with_status_returns_latitude_warning_without_emitting():
    converter = mgrs.MGRS()

    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        result, status = converter.MGRSToUTMWithStatus("50TMK5045027900")

    assert result == (50, "N", 450450.0, 4427900.0)
    assert status == mgrs.MGRS_LAT_WARNING == core.MGRS_LAT_WARNING
    assert seen == []


def test_mgrs_to_utm_with_status_returns_zero_for_valid_coordinate():
    result, status = mgrs.MGRS().MGRSToUTMWithStatus("15TWG0000049776")

    assert result == (15, "N", 500000.0, 4649776.0)
    assert status == 0


def test_mgrs_to_utm_with_status_still_raises_hard_errors():
    with pytest.raises(core.MGRSError, match="String Error"):
        mgrs.MGRS().MGRSToUTMWithStatus("not-an-mgrs-coordinate")


def test_existing_mgrs_to_utm_retains_warning_behavior():
    with pytest.warns(RuntimeWarning, match="Latitude Warning"):
        result = mgrs.MGRS().MGRSToUTM("50TMK5045027900")

    assert result == (50, "N", 450450.0, 4427900.0)
