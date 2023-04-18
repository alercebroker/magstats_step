from unittest import mock

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from magstats_step.core import MagnitudeStatistics


def test_calculate_uncorrected_stats_gives_statistics_for_magnitudes_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "mag": 2, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mag": 2, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mag": 5, "candid": "c"},
        {"aid": "AID2", "fid": 1, "mag": 1, "candid": "d"},
        {"aid": "AID1", "fid": 2, "mag": 1, "candid": "e"},
        {"aid": "AID1", "fid": 2, "mag": 2, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator._calculate_stats(False)

    expected = pd.DataFrame(
        {
            "magmean": [3, 1, 1.5],
            "magmedian": [2, 1, 1.5],
            "magmax": [5, 1, 2],
            "magmin": [2, 1, 1],
            "magsigma": [np.sqrt(2), 0, 0.5],
            "aid": ["AID1", "AID2", "AID1"],
            "fid": [1, 1, 2],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_corrected_stats_gives_statistics_for_corrected_magnitudes_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "mag_corr": 2, "corrected": True, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mag_corr": 2, "corrected": True, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mag_corr": 5, "corrected": True, "candid": "c"},
        {"aid": "AID1", "fid": 1, "mag_corr": 5, "corrected": False, "candid": "c1"},
        {"aid": "AID2", "fid": 1, "mag_corr": 1, "corrected": True, "candid": "d"},
        {"aid": "AID1", "fid": 2, "mag_corr": 1, "corrected": True, "candid": "e"},
        {"aid": "AID1", "fid": 2, "mag_corr": 2, "corrected": True, "candid": "f"},
        {"aid": "AID2", "fid": 2, "mag_corr": 2, "corrected": False, "candid": "f1"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator._calculate_stats(True)

    expected = pd.DataFrame(
        {
            "magmean_corr": [3, 1, 1.5],
            "magmedian_corr": [2, 1, 1.5],
            "magmax_corr": [5, 1, 2],
            "magmin_corr": [2, 1, 1],
            "magsigma_corr": [np.sqrt(2), 0, 0.5],
            "aid": ["AID1", "AID2", "AID1"],
            "fid": [1, 1, 2],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_uncorrected_stats_over_time_gives_first_and_last_magnitude_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "mjd": 3, "mag": 1, "candid": "a"},  # last
        {"aid": "AID1", "fid": 1, "mjd": 1, "mag": 2, "candid": "b"},  # first
        {"aid": "AID1", "fid": 1, "mjd": 2, "mag": 3, "candid": "c"},
        {"aid": "AID2", "fid": 1, "mjd": 1, "mag": 1, "candid": "d"},  # last and first
        {"aid": "AID1", "fid": 2, "mjd": 1, "mag": 1, "candid": "e"},  # first
        {"aid": "AID1", "fid": 2, "mjd": 2, "mag": 2, "candid": "f"},  # last
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator._calculate_stats_over_time(False)

    expected = pd.DataFrame(
        {
            "magfirst": [2, 1, 1],
            "maglast": [1, 1, 2],
            "aid": ["AID1", "AID2", "AID1"],
            "fid": [1, 1, 2],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_corrected_stats_over_time_gives_first_and_last_corrected_magnitude_per_aid_and_fid():
    detections = [
        {
            "aid": "AID1",
            "fid": 1,
            "mjd": 3,
            "mag_corr": 1,
            "corrected": True,
            "candid": "a",
        },
        {
            "aid": "AID1",
            "fid": 1,
            "mjd": 1,
            "mag_corr": 2,
            "corrected": True,
            "candid": "b",
        },
        {
            "aid": "AID1",
            "fid": 1,
            "mjd": 2,
            "mag_corr": 3,
            "corrected": True,
            "candid": "c",
        },
        {
            "aid": "AID1",
            "fid": 1,
            "mjd": 4,
            "mag_corr": 3,
            "corrected": False,
            "candid": "c1",
        },
        {
            "aid": "AID2",
            "fid": 1,
            "mjd": 1,
            "mag_corr": 1,
            "corrected": True,
            "candid": "d",
        },
        {
            "aid": "AID1",
            "fid": 2,
            "mjd": 1,
            "mag_corr": 1,
            "corrected": True,
            "candid": "e",
        },
        {
            "aid": "AID1",
            "fid": 2,
            "mjd": 2,
            "mag_corr": 2,
            "corrected": True,
            "candid": "f",
        },
        {
            "aid": "AID2",
            "fid": 2,
            "mjd": 0,
            "mag_corr": 2,
            "corrected": False,
            "candid": "f1",
        },
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator._calculate_stats_over_time(True)

    expected = pd.DataFrame(
        {
            "magfirst_corr": [2, 1, 1],
            "maglast_corr": [1, 1, 2],
            "aid": ["AID1", "AID2", "AID1"],
            "fid": [1, 1, 2],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_statistics_calls_stats_and_stats_over_time_with_both_corrected_and_full_magnitudes():
    detections = [{"candid": "a"}]
    calculator = MagnitudeStatistics(detections)

    calculator._calculate_stats = mock.Mock()
    calculator._calculate_stats_over_time = mock.Mock()
    calculator.calculate_statistics()

    calculator._calculate_stats.assert_any_call(corrected=True)
    calculator._calculate_stats.assert_any_call(corrected=False)
    calculator._calculate_stats_over_time.assert_any_call(corrected=True)
    calculator._calculate_stats_over_time.assert_any_call(corrected=False)


def test_calculate_firstmjd_gives_first_date_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "mjd": 3, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mjd": 0, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mjd": 2, "candid": "c"},
        {"aid": "AID2", "fid": 1, "mjd": 0.5, "candid": "d"},
        {"aid": "AID1", "fid": 2, "mjd": 1, "candid": "e"},
        {"aid": "AID1", "fid": 2, "mjd": 2, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_firstmjd()

    expected = pd.DataFrame({"firstmjd": [0, 0.5, 1], "aid": ["AID1", "AID2", "AID1"], "fid": [1, 1, 2]})
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_lastmjd_gives_last_date_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "mjd": 3, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mjd": 1, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mjd": 2, "candid": "c"},
        {"aid": "AID2", "fid": 1, "mjd": 1, "candid": "d"},
        {"aid": "AID1", "fid": 2, "mjd": 1, "candid": "e"},
        {"aid": "AID1", "fid": 2, "mjd": 2, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_lastmjd()

    expected = pd.DataFrame({"lastmjd": [3, 1, 2], "aid": ["AID1", "AID2", "AID1"], "fid": [1, 1, 2]})
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_corrected_gives_whether_first_detection_per_aid_and_fid_is_corrected():
    detections = [
        {"aid": "AID1", "fid": 1, "mjd": 3, "corrected": True, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mjd": 1, "corrected": False, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mjd": 2, "corrected": True, "candid": "c"},
        {"aid": "AID2", "fid": 1, "mjd": 1, "corrected": True, "candid": "d"},
        {"aid": "AID1", "fid": 2, "mjd": 1, "corrected": True, "candid": "e"},
        {"aid": "AID1", "fid": 2, "mjd": 2, "corrected": False, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_corrected()

    expected = pd.DataFrame(
        {
            "corrected": [False, True, True],
            "aid": ["AID1", "AID2", "AID1"],
            "fid": [1, 1, 2],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_stellar_gives_whether_first_detection_per_aid_and_fid_is_stellar():
    detections = [
        {"aid": "AID1", "fid": 1, "mjd": 3, "stellar": True, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mjd": 1, "stellar": False, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mjd": 2, "stellar": True, "candid": "c"},
        {"aid": "AID2", "fid": 1, "mjd": 1, "stellar": True, "candid": "d"},
        {"aid": "AID1", "fid": 2, "mjd": 1, "stellar": True, "candid": "e"},
        {"aid": "AID1", "fid": 2, "mjd": 2, "stellar": False, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_stellar()

    expected = pd.DataFrame(
        {
            "stellar": [False, True, True],
            "aid": ["AID1", "AID2", "AID1"],
            "fid": [1, 1, 2],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_ndet_gives_number_of_detections_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "candid": "a"},
        {"aid": "AID1", "fid": 1, "candid": "b"},
        {"aid": "AID1", "fid": 1, "candid": "c"},
        {"aid": "AID2", "fid": 1, "candid": "d"},
        {"aid": "AID1", "fid": 2, "candid": "e"},
        {"aid": "AID1", "fid": 2, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_ndet()

    expected = pd.DataFrame({"ndet": [3, 1, 2], "aid": ["AID1", "AID2", "AID1"], "fid": [1, 1, 2]})
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_ndubious_gives_number_of_dubious_detections_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "dubious": True, "candid": "a"},
        {"aid": "AID1", "fid": 1, "dubious": True, "candid": "b"},
        {"aid": "AID1", "fid": 1, "dubious": False, "candid": "c"},
        {"aid": "AID2", "fid": 1, "dubious": False, "candid": "d"},
        {"aid": "AID1", "fid": 2, "dubious": True, "candid": "e"},
        {"aid": "AID1", "fid": 2, "dubious": False, "candid": "f"},
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_ndubious()

    expected = pd.DataFrame({"ndubious": [2, 0, 1], "aid": ["AID1", "AID2", "AID1"], "fid": [1, 1, 2]})
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)


def test_calculate_saturation_rate_gives_saturation_ratio_per_aid_and_fid():
    detections = [
        {"aid": "AID1", "fid": 1, "mag_corr": 0, "candid": "a"},
        {"aid": "AID1", "fid": 1, "mag_corr": 100, "candid": "b"},
        {"aid": "AID1", "fid": 1, "mag_corr": 100, "candid": "c"},
        {"aid": "AID1", "fid": 1, "mag_corr": 0, "candid": "c1"},
        {"aid": "AID2", "fid": 2, "mag_corr": np.nan, "candid": "d"},
        {"aid": "AID2", "fid": 3, "mag_corr": np.nan, "candid": "d1"},
        {"aid": "AID2", "fid": 3, "mag_corr": 100, "candid": "d2"},
        {"aid": "AID1", "fid": 10, "mag_corr": 0, "candid": "e"},  # No threshold
        {"aid": "AID1", "fid": 10, "mag_corr": 100, "candid": "f"},  # No threshold
    ]
    calculator = MagnitudeStatistics(detections)
    result = calculator.calculate_saturation_rate()

    expected = pd.DataFrame(
        {
            "saturation_rate": [0.5, np.nan, 0, 0],
            "aid": ["AID1", "AID2", "AID2", "AID1"],
            "fid": [1, 2, 3, 10],
        }
    )
    assert_frame_equal(result, expected.set_index(["aid", "fid"]), check_like=True)