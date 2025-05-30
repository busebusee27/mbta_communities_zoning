"""
Provides utils that the compliance model needs
(mainly the functions used in each of the district pages)
"""

import pandas as pd
import numpy as np

_community_info_df = pd.DataFrame(pd.read_csv("./resources/community_info.csv"))


def get_community_info(community_name):
    """
    Given `community_name`, returns all the basic information
    that the compliance model needs for that community

    Fails if `community_name` is not one of the MBTA communities
    (naming is case sensitive)
    """
    row = _community_info_df.query("Community == @community_name")
    cell_map = {}
    for i in range(1, 7):
        cell_map[f"I{3+i}"] = row.iloc[0, i]
    return cell_map


def apply_district_funcs(
    df,
    min_lot_size,
    min_required_open_space,
    water_included,
    parking_spaces_per_unit,
    building_height,
    max_dwelling_units_per_acre,
    max_lot_coverage,
    base_min_lot_size,
    additional_lot_SF,
    max_units_per_lot,
    FAR,
    lot_area_per_dwelling_unit,
):
    """
    Applies many functions and appends each result as a
    column in `df`. Each column directly corresponds with the
    column of the same name in the `District {i}` sheets in Excel
    """
    if "O" not in df.columns:
        df["O"] = pd.NA

    def apply_N_func():
        df["N"] = np.where(
            df["I"] < min_lot_size,
            0,
            np.where((df["I"] - df["L"]) < 0, 0, df["I"] - df["L"]),
        )

    apply_N_func()

    def apply_Q_func():
        df["Q"] = np.where(pd.isna(df["O"]), df["N"], df["O"])

    apply_Q_func()

    def apply_R_func():
        df["R"] = df["L"] / df["I"]

    apply_R_func()

    def apply_S_func():
        df["S"] = (
            max(0.2, min_required_open_space) if min_required_open_space < 1 else 0.2
        )

    apply_S_func()

    def apply_T_func():
        df["T"] = np.where(
            pd.isna(df["O"]),
            np.where(
                water_included == "Y",
                np.maximum(df["R"], df["S"]) * df["I"],
                (df["R"] + df["S"]) * df["I"],
            ),
            np.where(df["O"] > 0, df["Q"] * df["S"], 0),
        )

    apply_T_func()

    def apply_U_func():
        def _parking_factor():
            return np.select(
                [
                    parking_spaces_per_unit == 0,
                    (0.01 <= parking_spaces_per_unit)
                    & (parking_spaces_per_unit <= 0.5),
                    (0.5 < parking_spaces_per_unit) & (parking_spaces_per_unit <= 1),
                    (1 < parking_spaces_per_unit) & (parking_spaces_per_unit <= 1.25),
                    (1.25 < parking_spaces_per_unit) & (parking_spaces_per_unit <= 1.5),
                ],
                [0, 0.3, 0.45, 0.55, 0.6],
                default=0.65,
            )

        df["U"] = np.where(
            (df["Q"].notna()) & (df["Q"] > 0),
            (df["I"] - df["T"]) * _parking_factor(),
            0,
        )

    apply_U_func()

    def apply_V_func():
        df["V"] = np.where(
            (df["Q"].notna()) & (df["Q"].ne(0)), df["I"] - df["T"] - df["U"], 0
        )

    apply_V_func()

    def apply_W_func():
        df["W"] = np.where(df["V"] > 0, df["V"] * building_height, 0)

    apply_W_func()

    def apply_X_func():
        df["X"] = np.floor(
            np.select(
                [df["W"] > 3000, (df["W"] > 2500) & (df["W"] <= 3000)],
                [np.floor(df["W"]), 3],
                default=0,
            )
            / 1000
        )

    apply_X_func()

    def apply_Y_func():
        df["Y"] = np.where(
            max_dwelling_units_per_acre,
            (df["I"] / 43560) * max_dwelling_units_per_acre,
            np.nan,
        )

    apply_Y_func()

    def apply_Z_func():
        df["Z"] = np.where(
            max_lot_coverage,
            (df["I"] * max_lot_coverage * building_height) / 1000,
            float("inf"),
        )

    apply_Z_func()

    def apply_AA_func():
        df["AA"] = np.where(
            lot_area_per_dwelling_unit, df["I"] / lot_area_per_dwelling_unit, np.nan
        )

    apply_AA_func()

    def apply_AB_func():
        df["AB"] = np.where(FAR, (df["I"] * FAR) / 1000, np.nan)

    apply_AB_func()

    def apply_AC_func():
        df["AC"] = np.floor(
            np.select(
                [
                    (max_units_per_lot >= 3) & (max_units_per_lot < df["X"]),
                    (max_units_per_lot < df["X"]) & (max_units_per_lot < 3),
                ],
                [max_units_per_lot, 0],
                default=df["X"],
            )
        )

    apply_AC_func()

    def apply_AD_func():
        df["AD"] = np.where((df["I"] > 0) & (df["I"] < min_lot_size), "Y", "")

    apply_AD_func()

    def apply_AE_func():
        df["AE"] = np.where(
            df["AD"] == "Y",
            0,
            np.where(
                additional_lot_SF == "",
                float("inf"),  # Python equivalent for "<no limit>"
                np.floor(((df["I"] - base_min_lot_size) / additional_lot_SF) + 1),
            ),
        )

    apply_AE_func()

    def apply_AF_func():
        cols = ["X", "Y", "Z", "AA", "AB", "AC", "AE"]
        expr = np.fmin.reduce([df[col].fillna(np.inf) for col in cols])
        df["AF"] = np.select(
            [expr < 2.5, (expr >= 2.5) & (expr < 3)], [0, 3], default=np.round(expr)
        )

    apply_AF_func()

    def apply_AG_func():
        df["AG"] = (43560 / df["I"]) * df["AF"]

    apply_AG_func()
