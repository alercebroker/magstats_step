import warnings
from typing import List

import pandas as pd

from ._base import BaseStatistics


class MagnitudeStatistics(BaseStatistics):
    _JOIN = ["aid", "fid"]
    # Saturation threshold for each filter
    _THRESHOLD = pd.Series([13.2, 13.2, 13.2], index=pd.Index([1, 2, 3], name="fid"))

    def __init__(self, detections: List[dict], non_detections: List[dict] = None):
        super().__init__(detections)
        if non_detections:
            self._non_detections = pd.DataFrame.from_records(
                non_detections
            ).drop_duplicates(["oid", "fid", "mjd"])
        else:
            self._non_detections = pd.DataFrame()

    def _calculate_stats(self, corrected: bool = False) -> pd.DataFrame:
        suffix = "_corr" if corrected else ""
        in_label, out_label = f"mag{suffix}", f"mag{{}}{suffix}"

        grouped = self._grouped_detections(corrected=corrected)
        functions = {"mean", "median", "max", "min"}
        functions = {out_label.format(func): func for func in functions}

        stats = grouped[in_label].agg(**functions)
        # Pandas std requires additional kwarg, that's why it needs to be added apart
        return stats.join(
            grouped[in_label].agg("std", ddof=0).rename(out_label.format("sigma")),
            how="outer",
        )

    def _calculate_stats_over_time(self, corrected: bool = False) -> pd.DataFrame:
        suffix = "_corr" if corrected else ""
        in_label, out_label = f"mag{suffix}", f"mag{{}}{suffix}"

        first = self._grouped_value(in_label, which="first", corrected=corrected)
        last = self._grouped_value(in_label, which="last", corrected=corrected)
        return pd.DataFrame(
            {out_label.format("first"): first, out_label.format("last"): last}
        )

    def calculate_statistics(self) -> pd.DataFrame:
        stats = self._calculate_stats(corrected=False)
        stats = stats.join(
            self._calculate_stats_over_time(corrected=False), how="outer"
        )
        stats = stats.join(self._calculate_stats(corrected=True), how="outer")
        return stats.join(self._calculate_stats_over_time(corrected=True), how="outer")

    def calculate_firstmjd(self) -> pd.DataFrame:
        return pd.DataFrame({"firstmjd": self._grouped_value("mjd", which="first")})

    def calculate_lastmjd(self) -> pd.DataFrame:
        return pd.DataFrame({"lastmjd": self._grouped_value("mjd", which="last")})

    def calculate_corrected(self) -> pd.DataFrame:
        return pd.DataFrame(
            {"corrected": self._grouped_value("corrected", which="first")}
        )

    def calculate_stellar(self) -> pd.DataFrame:
        return pd.DataFrame({"stellar": self._grouped_value("stellar", which="first")})

    def calculate_ndubious(self) -> pd.DataFrame:
        return pd.DataFrame({"ndubious": self._grouped_detections()["dubious"].sum()})

    def calculate_saturation_rate(self) -> pd.DataFrame:
        total = self._grouped_detections()[
            "mag_corr"
        ].count()  # Count will exclude NaNs
        saturated = (
            self._detections.set_index("fid")
            .query("mag_corr < @self._THRESHOLD.reindex(fid)")
            .reset_index()
        )
        saturated = (
            self._group(saturated)["mag_corr"]
            .count()
            .reindex(total.index, fill_value=0)
        )
        with warnings.catch_warnings():
            # possible 0 divided by 0; this is expected and returned NaN is correct value
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            return pd.DataFrame({"saturation_rate": saturated / total})

    def calculate_dmdt(self) -> pd.DataFrame:
        dt_min = 0.5

        if self._non_detections.size == 0:  # Handle no non-detection case
            return pd.DataFrame(
                columns=["dt_first", "dm_first", "sigmadm_first", "dmdt_first"]
            )

        first_mag = self._grouped_value("mag", which="first")
        first_e_mag = self._grouped_value("e_mag", which="first")
        first_mjd = self._grouped_value("mjd", which="first")

        nd = self._non_detections.set_index(
            self._JOIN
        )  # Index by join to compute based on it

        dt = first_mjd - nd["mjd"]
        dm = first_mag - nd["diffmaglim"]
        sigmadm = first_e_mag - nd["diffmaglim"]
        dmdt = (first_mag + first_e_mag - nd["diffmaglim"]) / dt

        # Include back fid for grouping and unique identification
        results = pd.DataFrame(
            {"dt": dt, "dm": dm, "sigmadm": sigmadm, "dmdt": dmdt}
        ).reset_index()
        # Only include non-detections before dt_min
        idx = self._group(results[results["dt"] > dt_min])["dmdt"].idxmin().dropna()

        # Drop NaN, since they result from no non-detection before first detection
        results = results.dropna().loc[idx].set_index(self._JOIN)
        return results.rename(columns={c: f"{c}_first" for c in results.columns})
