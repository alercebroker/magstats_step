from unittest import mock

import numpy as np
import pandas as pd
from pandas.testing import assert_series_equal, assert_frame_equal
from magstats_step.core import ObjectStatistics

from data.messages import data


def test_arcsec_to_degree_conversion():
    arcsec = 3600
    degrees = ObjectStatistics._arcsec2deg(arcsec)
    assert degrees == arcsec / 3600


def test_degree_to_arcsec_conversion():
    degrees = 1
    arcsec = ObjectStatistics._deg2arcsec(degrees)
    assert degrees == arcsec / 3600


def test_composition_of_arcsec2dec_and_dec2arcsec_results_in_same_input():
    degrees = 1
    result = ObjectStatistics._arcsec2deg(ObjectStatistics._deg2arcsec(degrees))
    assert degrees == result


def test_calculate_weights_gives_inverse_square_of_errors():
    sigs = pd.Series([2., 3.])
    result = ObjectStatistics._compute_weights(sigs)
    assert (result == 1 / sigs ** 2).all()


def test_calculate_weighted_mean_with_equal_errors_is_standard_mean():
    vals = pd.Series([100, 200])
    sigs = pd.Series([4., 4.])
    result = ObjectStatistics._weighted_mean(vals, sigs)
    assert result == 150


def test_calculate_weighted_mean_with_one_very_small_error_has_that_value_as_result():
    vals = pd.Series([100, 200])
    sigs = pd.Series([1e-6, 4.])
    result = ObjectStatistics._weighted_mean(vals, sigs)
    assert np.isclose(result, 100)


def test_calculate_weighted_mean_with_one_very_large_error_has_that_value_disregarded():
    vals = pd.Series([100, 200])
    sigs = pd.Series([1e6, 4.])
    result = ObjectStatistics._weighted_mean(vals, sigs)
    assert np.isclose(result, 200)


def test_calculate_weighted_mean_error_with_equal_weights_is_sigma_divided_by_sqrt_number_of_samples():
    sigs = pd.Series([4., 4.])
    result = ObjectStatistics._weighted_mean_error(sigs)
    assert np.isclose(result, 4 / np.sqrt(2))


def test_calculate_weighted_mean_error_with_one_very_small_error_has_that_error_as_result():
    sigs = pd.Series([1e-6, 4.])
    result = ObjectStatistics._weighted_mean_error(sigs)
    assert np.isclose(result, 1e-6)


def test_calculate_weighted_mean_error_with_one_very_large_error_has_that_error_disregarded():
    sigs = pd.Series([1e6, 4.])
    result = ObjectStatistics._weighted_mean_error(sigs)
    assert np.isclose(result, 4)


def test_calculate_coordinates_with_ra_uses_weighted_mean_and_weighted_mean_error_per_aid():
    detections = [
        {"aid": "AID1", "ra": 10, "e_ra": 2, "candid": "a"},
        {"aid": "AID2", "ra": 20, "e_ra": 4, "candid": "c"},
        {"aid": "AID1", "ra": 20, "e_ra": 4, "candid": "b"},
    ]
    calculator = ObjectStatistics(detections)

    calculator._weighted_mean = mock.Mock()
    calculator._weighted_mean.return_value = 1  # Dummy value for check
    calculator._weighted_mean_error = mock.Mock()  # DO NOT USE MagicMock!! Messes with some checks in pandas
    calculator._weighted_mean_error.return_value = 2  # Dummy value for check

    result = calculator._calculate_coordinates("ra")
    assert "meanra" in result and "sigmara" in result
    assert (result["meanra"] == 1).all()
    assert (result["sigmara"] == 2 * 3600).all()

    for call in calculator._weighted_mean.call_args_list:
        val, err = call.args
        assert call.kwargs == {}
        if len(val) == 2:  # This is AID1, the order cannot be assured
            assert_series_equal(val, pd.Series([10, 20], index=pd.Index(["a", "b"], name="candid"), name="ra"))
            assert_series_equal(err, pd.Series([2 / 3600, 4 / 3600], index=pd.Index(["a", "b"], name="candid"), name="e_ra"))
        else:  # Should be AID2
            assert_series_equal(val, pd.Series([20], index=pd.Index(["c"], name="candid"), name="ra"))
            assert_series_equal(err, pd.Series([4 / 3600], index=pd.Index(["c"], name="candid"), name="e_ra"))


def test_calculate_coordinates_with_dec_uses_weighted_mean_and_weighted_mean_error_per_aid():
    detections = [
        {"aid": "AID1", "dec": 10, "e_dec": 2, "candid": "a"},
        {"aid": "AID2", "dec": 20, "e_dec": 4, "candid": "c"},
        {"aid": "AID1", "dec": 20, "e_dec": 4, "candid": "b"},
    ]
    calculator = ObjectStatistics(detections)

    calculator._weighted_mean = mock.Mock()
    calculator._weighted_mean.return_value = 1  # Dummy value for check
    calculator._weighted_mean_error = mock.Mock()  # DO NOT USE MagicMock!! Messes with some checks in pandas
    calculator._weighted_mean_error.return_value = 2  # Dummy value for check

    result = calculator._calculate_coordinates("dec")
    assert "meandec" in result and "sigmadec" in result
    assert (result["meandec"] == 1).all()
    assert (result["sigmadec"] == 2 * 3600).all()

    for call in calculator._weighted_mean.call_args_list:
        val, err = call.args
        assert call.kwargs == {}
        if len(val) == 2:  # This is AID1, the order cannot be assured
            assert_series_equal(val, pd.Series([10, 20], index=pd.Index(["a", "b"], name="candid"), name="dec"))
            assert_series_equal(err, pd.Series([2 / 3600, 4 / 3600], index=pd.Index(["a", "b"], name="candid"), name="e_dec"))
        else:  # Should be AID2
            assert_series_equal(val, pd.Series([20], index=pd.Index(["c"], name="candid"), name="dec"))
            assert_series_equal(err, pd.Series([4 / 3600], index=pd.Index(["c"], name="candid"), name="e_dec"))


def test_calculate_ra_uses_calculate_coordinates():
    detections = [{"candid": "a"}]
    calculator = ObjectStatistics(detections)

    calculator._calculate_coordinates = mock.Mock()
    calculator.calculate_ra()

    calculator._calculate_coordinates.assert_called_once_with("ra")


def test_calculate_dec_uses_calculate_coordinates():
    detections = [{"candid": "a"}]
    calculator = ObjectStatistics(detections)

    calculator._calculate_coordinates = mock.Mock()
    calculator.calculate_dec()

    calculator._calculate_coordinates.assert_called_once_with("dec")


def test_calculate_firstmjd_gives_the_first_mjd_per_aid():
    detections = [
        {"aid": "AID1", "mjd": 1, "candid": "a"},
        {"aid": "AID2", "mjd": 2, "candid": "c"},
        {"aid": "AID1", "mjd": 3, "candid": "b"},
        {"aid": "AID1", "mjd": 2, "candid": "d"},
    ]
    calculator = ObjectStatistics(detections)
    result = calculator.calculate_firstmjd()

    assert "firstmjd" in result
    assert_series_equal(result["firstmjd"], pd.Series([1, 2], index=pd.Index(["AID1", "AID2"], name="aid"), name="firstmjd"))


def test_calculate_lastmjd_gives_the_last_mjd_per_aid():
    detections = [
        {"aid": "AID1", "mjd": 1, "candid": "a"},
        {"aid": "AID2", "mjd": 2, "candid": "c"},
        {"aid": "AID1", "mjd": 3, "candid": "b"},
        {"aid": "AID1", "mjd": 2, "candid": "d"},
    ]
    calculator = ObjectStatistics(detections)
    result = calculator.calculate_lastmjd()

    assert "lastmjd" in result
    assert_series_equal(result["lastmjd"], pd.Series([3, 2], index=pd.Index(["AID1", "AID2"], name="aid"), name="lastmjd"))


def test_calculate_ndet_gives_number_of_detections_per_aid():
    calculator = ObjectStatistics(data[0]["detections"])
    result = calculator.calculate_ndet()

    sums = {}
    for det in data[0]["detections"]:
        sums[det["aid"]] = 1 if det["aid"] not in sums else sums[det["aid"]] + 1

    assert "ndet" in result
    assert (result["ndet"] == list(sums.values())).all()
