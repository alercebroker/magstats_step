import warnings
from functools import reduce
from methodtools import lru_cache
from typing import Literal, Union

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy

Which = Literal["first", "last"]


class MagnitudeStatistics:
    MAGNITUDE_THRESHOLD = 13.2

    def __init__(self, detections: pd.DataFrame, non_detections: pd.DataFrame, exclude: set):
        self._detections = detections
        self._non_detections = non_detections
        self._exclude = exclude

    @lru_cache(1)
    def _corrected(self):
        return self._detections[self._detections["corrected"]]

    @lru_cache(4)
    def _grouped_index(self, which: Which, corrected: bool = False) -> pd.Series:
        if which == "first":
            function = "idxmin"
        elif which == "last":
            function = "idxmax"
        else:
            raise ValueError(f"Unrecognized value for 'which': {which}")
        return self._grouped_detections(corrected)["mjd"].agg(function)

    @lru_cache(20)
    def _grouped_value(self, source: str, which: Which, corrected: bool = False) -> pd.Series:
        idx = self._grouped_index(which, corrected)
        df = self._corrected() if corrected else self._detections
        return df[source][idx].set_axis(idx.index)

    @lru_cache(2)
    def _grouped_detections(self, corrected: bool = False) -> DataFrameGroupBy:
        return self._group(self._corrected()) if corrected else self._group(self._detections)

    @staticmethod
    def _group(df: Union[pd.DataFrame, pd.Series]) -> Union[DataFrameGroupBy, SeriesGroupBy]:
        return df.groupby("fid")

    def _calculate_stats(self, corrected: bool = False) -> pd.DataFrame:
        suffix = "_corr" if corrected else ""

        grouped = self._grouped_detections(corrected)
        functions = {"mean": "mean", "median": "median", "max": "max", "min": "min", "std": "sigma"}

        aggregated = grouped[f"mag{suffix}"].agg(list(functions.keys()))
        if "std" in functions:  # pandas std gives NaN if only one sample
            aggregated["std"].fillna(0, inplace=True)
        return aggregated.rename(columns={k: f"mag{v}{suffix}" for k, v in functions.items()})

    def _calculate_stats_over_time(self, corrected: bool = False):
        suffix = "_corr" if corrected else ""
        first_mag = self._grouped_value(f"mag{suffix}", which="first", corrected=corrected)
        last_mag = self._grouped_value(f"mag{suffix}", which="last", corrected=corrected)
        return pd.DataFrame({f"magfirst{suffix}": first_mag, f"maglast{suffix}": last_mag})

    def calculate_stats(self) -> pd.DataFrame:
        stats = self._calculate_stats(corrected=False)
        stats = stats.join(self._calculate_stats_over_time(corrected=False))
        stats = stats.join(self._calculate_stats(corrected=True))
        return stats.join(self._calculate_stats_over_time(corrected=True))

    def calculate_mjd(self) -> pd.DataFrame:
        first_mjd = self._grouped_value("mjd", which="first")
        last_mjd = self._grouped_value("mjd", which="last")
        return pd.DataFrame({"firstmjd": first_mjd, "lastmjd": last_mjd})

    def calculate_corrected(self) -> pd.DataFrame:
        return pd.DataFrame({"corrected": self._grouped_value("corrected", which="first")})

    def calculate_stellar(self) -> pd.DataFrame:
        return pd.DataFrame({"stellar": self._grouped_value("stellar", which="first")})

    def calculate_ndet(self) -> pd.DataFrame:
        # The column selected for ndet is irrelevant as long as it has no NaN values
        return pd.DataFrame({"ndet": self._grouped_detections()["oid"].count()})

    def calculate_ndubious(self) -> pd.DataFrame:
        return pd.DataFrame({"ndubious": self._grouped_detections()["dubious"].sum()})

    def calculate_saturation_rate(self) -> pd.DataFrame:
        mask = self._detections["mag_corr"] < self.MAGNITUDE_THRESHOLD
        saturated = self._group(self._detections[mask])["mag_corr"].count()
        total = self._grouped_detections()["mag_corr"].count()  # Count also excludes NaNs
        with warnings.catch_warnings():
            # possible 0 divided by 0; this is expected and returned NaN is correct value
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            return pd.DataFrame({"saturation_rate": saturated / total})

    def calculate_dmdt(self) -> pd.DataFrame:
        dt_min = 0.5

        if self._non_detections.size == 0:  # Handle no non-detection case
            return pd.DataFrame(columns=["dt_first", "dm_first", "sigmadm_first", "dmdt_first"])
        first_mag = self._grouped_value("mag", which="first")
        first_e_mag = self._grouped_value("e_mag", which="first")
        first_mjd = self._grouped_value("mjd", which="first")

        nd = self._non_detections.set_index("fid")  # Index by fid to compute based on it

        dt = first_mjd - nd["mjd"]
        dm = first_mag - nd["diffmaglim"]
        sigmadm = first_e_mag - nd["diffmaglim"]
        dmdt = (first_mag + first_e_mag - nd["diffmaglim"]) / dt

        # Include back fid for grouping and unique identification
        results = pd.DataFrame({"dt": dt, "dm": dm, "sigmadm": sigmadm, "dmdt": dmdt}).reset_index()
        # Only include non-detections before dt_min
        idx = self._group(results[results["dt"] > dt_min])["dmdt"].idxmin().dropna()

        # Drop NaN, since they result from no non-detection before first detection
        results = results.dropna().loc[idx].set_index("fid")
        return results.rename(columns={c: f"{c}_first" for c in results.columns})

    def generate_magstats(self):
        methods = [m for m in MagnitudeStatistics.__dict__ if m.startswith("calculate_") and m not in self._exclude]
        magstats = [getattr(self, method)() for method in methods]
        return reduce(lambda left, right: left.join(right, how="outer"), magstats).reset_index().to_dict("records")
