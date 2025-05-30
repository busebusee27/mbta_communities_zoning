"""
Provides the whole compliance model in Python
"""

import pandas as pd
import json
from utils import compliance_utils

INTRODUCTION = "Introduction"
DISTRICT_ID = "Checklist District ID"
PARAMETERS = "Checklist Parameters"
SUMMARY = "Summary"

EMPTY_DF = pd.DataFrame(
    columns=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]
)


class ComplianceModel:
    """
    This class corresponds to the MBTA Excel compliance model from
    https://www.mass.gov/info-details/mbta-communities-compliance-model-components
    """

    def __init__(self):
        self._big_dict = {
            "Introduction": {},
            "Checklist District ID": {},
            "Checklist Parameters": {},
            "District 1": {},
            "District 2": {},
            "District 3": {},
            "District 4": {},
            "District 5": {},
            "Zoning Input Summary": {},
            "Summary": {},
        }

    def fill_sheet(self, sheet_name, cell_map):
        """
        Fills in necessary information in the `sheet_name` sheet by modifying it
        with values given in `cell_map`. Any dependents of each of these cells are
        automatically updated and evaluated.

        Any additional cells beyond required or expected ones for
        the `sheet_name` sheet are ignored.

        Fails if:
            * `sheet_name` does not exist in the spreadsheet
            * required cells for the `sheet_name` sheet are missing
        """
        # TODO: ^ add checks to fail for extra cells (maybe the wrong sheet is
        #       being called somewhere)
        #       also add a failure condition if the data is the wrong type

        # TODO: add checks to make sure district info being filled out across
        #       different sheets matches up with districts defined

        _big_dict = self._big_dict

        def _fill_introduction(cell_map):
            """
            Requires `cell_map` to map `I3` to the community name.
            """
            _big_dict[INTRODUCTION]["I3"] = cell_map["I3"]

        def _fill_checklist_district_id(cell_map):
            """
            Requires `cell_map` to map `B54:E54` to values
            for the first district. Also requires `E64` to be `N` or `Y`

            Optionally, map `B55:E58` to
            values for up to four other districts as well.
            """
            # apparently the line below isn't even needed, which is pretty weird
            # if not "E64" in cell_map and cell_map["E64"] not in ["Y", "N"]:
            #     raise Exception("Expected `E64` to be `Y` or `N`")

            print("here", cell_map)
            if not "C43" in cell_map and cell_map["C43"] not in ["Y", "N"]:
                raise Exception("Expected `C43` to be `Y` or `N`")

            _big_dict[DISTRICT_ID]["C43"] = cell_map["C43"]

            for cell in [
                f"{x}{y}" for x in ["B", "C", "D", "E"] for y in [54, 55, 56, 57, 58]
            ]:
                if cell in cell_map:
                    _big_dict[DISTRICT_ID][cell] = cell_map[cell]
                else:
                    _big_dict[DISTRICT_ID][cell] = None

        def _fill_checklist_parameters(cell_map):
            """
            Requires `cell_map` to map, for districts on the `Checklist District ID` sheet,
            * For each (valid) `E`, `H`, `K`, `N`, `Q`, fill the following cells:
                * `16`
                * `22`
                * `24`
                * `25`
                * `35`
                * `43`
                * `58` <- ratio (0-1)
                * `60` <- ratio (0-1)
                * `86`
                * `101`
                * `102`
                * `103`
            """
            for row in [16, 22, 24, 25, 35, 43, 58, 60, 86, 101, 102, 103]:
                cell = f"E{row}"
                _big_dict[PARAMETERS][cell] = cell_map[cell]

            for col in "HKNQ":
                for row in [16, 22, 24, 25, 35, 43, 58, 60, 86, 101, 102, 103]:
                    cell = f"{col}{row}"
                    if cell in cell_map:
                        _big_dict[PARAMETERS][cell] = cell_map[cell]
                    else:
                        _big_dict[PARAMETERS][cell] = 0

        def _fill_district_i(i, df):
            """
            Fill in the 'District `i`' sheet based on the values in `df`.
            """
            return

        if sheet_name == "Introduction":
            _fill_introduction(cell_map)
        elif sheet_name == "Checklist District ID":
            _fill_checklist_district_id(cell_map)
        elif sheet_name == "Checklist Parameters":
            _fill_checklist_parameters(cell_map)
        elif sheet_name.split(" ")[0] == "District":
            _fill_district_i(int(sheet_name.split(" ")[1]), cell_map)
        else:
            raise Exception(f"Sheet `{sheet_name}` not found")

    def populate_sheet(self, sheet_name, df=EMPTY_DF.copy()):
        """
        this is for actually populating the whole sheet, including formulas once
        the user input is complete

        requires populate to be called in the order that the excel sheet
        is supposed to be filled out in. fails otherwise
        """

        _big_dict = self._big_dict

        def populate_introduction():
            _big_dict["Introduction"] |= compliance_utils.get_community_info(
                _big_dict["Introduction"]["I3"]
            )

        def populate_checklist_district_id():
            for col in "CDE":
                _big_dict["Checklist District ID"][f"{col}59"] = sum(
                    filter(
                        lambda x: x is not None,
                        [
                            _big_dict["Checklist District ID"][f"{col}{row}"]
                            for row in range(54, 59)
                        ],
                    )
                )

            _big_dict[DISTRICT_ID]["E70"] = (
                _big_dict[INTRODUCTION]["I7"] * _big_dict[INTRODUCTION]["I9"]
            )
            _big_dict[DISTRICT_ID]["E71"] = _big_dict[DISTRICT_ID]["D59"]
            _big_dict[DISTRICT_ID]["E72"] = (
                _big_dict[DISTRICT_ID]["E70"] - _big_dict[DISTRICT_ID]["D59"]
            )
            _big_dict[DISTRICT_ID]["E74"] = (
                _big_dict[INTRODUCTION]["I6"] * _big_dict[INTRODUCTION]["I9"]
            )

        def populate_checklist_parameters():
            return

        def populate_district_i(i, df):
            # TODO: check rounding for AC and X columns
            district = f"District {i}"
            parameter_col_map = {1: "E", 2: "H", 3: "K", 4: "N", 5: "Q"}
            parameter_sheet_col = parameter_col_map[i]

            compliance_utils.apply_district_funcs(
                df,
                water_included=_big_dict[DISTRICT_ID]["C43"],
                max_units_per_lot=_big_dict[PARAMETERS][f"{parameter_sheet_col}16"],
                min_lot_size=_big_dict[PARAMETERS][f"{parameter_sheet_col}22"],
                base_min_lot_size=_big_dict[PARAMETERS][f"{parameter_sheet_col}24"],
                additional_lot_SF=_big_dict[PARAMETERS][f"{parameter_sheet_col}25"],
                building_height=_big_dict[PARAMETERS][f"{parameter_sheet_col}35"],
                FAR=_big_dict[PARAMETERS][f"{parameter_sheet_col}43"],
                max_lot_coverage=_big_dict[PARAMETERS][f"{parameter_sheet_col}58"],
                min_required_open_space=_big_dict[PARAMETERS][
                    f"{parameter_sheet_col}60"
                ],
                parking_spaces_per_unit=_big_dict[PARAMETERS][
                    f"{parameter_sheet_col}86"
                ],
                lot_area_per_dwelling_unit=_big_dict[PARAMETERS][
                    f"{parameter_sheet_col}101"
                ],
                max_dwelling_units_per_acre=_big_dict[PARAMETERS][
                    f"{parameter_sheet_col}102"
                ],
            )

            _big_dict[district]["B9"] = _big_dict[DISTRICT_ID][f"E{54 + i-1}"]
            _big_dict[district]["B10"] = len(df)
            _big_dict[district]["B11"] = sum(df["H"])
            _big_dict[district]["B12"] = sum(df["W"])
            _big_dict[district]["B13"] = sum(df["AF"])
            _big_dict[district]["B14"] = (
                _big_dict[district]["B13"] / _big_dict[district]["B9"]
                if _big_dict[district]["B9"]
                else 0
            )
            _big_dict[district]["F9"] = len(df.query("AD == 'Y'"))
            _big_dict[district]["F10"] = sum(df.query("G == 'Y'")["AF"])
            _big_dict[district]["F11"] = sum(df["L"])
            _big_dict[district]["F12"] = sum(df["T"])
            _big_dict[district]["F13"] = sum(df.query("U > 0")["U"])
            _big_dict[district]["F14"] = sum(df["X"]) - sum(df["AC"])

            # additional stuff needed to populate the summary page T_T
            _big_dict[district]["X_sum"] = sum(df["X"])
            _big_dict[district]["Y_sum"] = sum(df["Y"])
            _big_dict[district]["Z_sum"] = sum(df["Z"])
            _big_dict[district]["AA_sum"] = sum(df["AA"])
            _big_dict[district]["AB_sum"] = sum(df["AB"])
            _big_dict[district]["AC_sum"] = sum(df["AC"])
            _big_dict[district]["AE_sum"] = sum(df["AE"])
            _big_dict[district]["AF_sum"] = sum(df["AF"])

        def populate_summary():
            col_map = {1: "C", 2: "D", 3: "E", 4: "F", 5: "G"}
            parameter_col_map = {1: "E", 2: "H", 3: "K", 4: "N", 5: "Q"}

            for i in range(1, 6):
                parameter_sheet_col = parameter_col_map[i]
                col = col_map[i]
                district = f"District {i}"

                _big_dict[SUMMARY][f"{col}5"] = _big_dict[DISTRICT_ID][f"B{54 + i-1}"]
                _big_dict[SUMMARY][f"{col}6"] = _big_dict[district]["X_sum"]
                _big_dict[SUMMARY][f"{col}7"] = _big_dict[district]["Y_sum"]
                _big_dict[SUMMARY][f"{col}8"] = _big_dict[PARAMETERS][
                    f"{parameter_sheet_col}103"
                ]
                _big_dict[SUMMARY][f"{col}9"] = _big_dict[district]["Z_sum"]
                _big_dict[SUMMARY][f"{col}10"] = _big_dict[district]["AA_sum"]
                _big_dict[SUMMARY][f"{col}11"] = _big_dict[district]["AC_sum"]
                _big_dict[SUMMARY][f"{col}12"] = _big_dict[district]["AB_sum"]
                _big_dict[SUMMARY][f"{col}13"] = min(
                    _big_dict[district]["B13"], _big_dict[SUMMARY][f"{col}8"]
                )

                _big_dict[SUMMARY][f"{col}18"] = _big_dict[DISTRICT_ID][f"B{54 + i-1}"]
                _big_dict[SUMMARY][f"{col}19"] = _big_dict[DISTRICT_ID][f"C{54 + i-1}"]
                _big_dict[SUMMARY][f"{col}20"] = _big_dict[DISTRICT_ID][f"E{54 + i-1}"]
                _big_dict[SUMMARY][f"{col}21"] = _big_dict[SUMMARY][f"{col}13"]
                _big_dict[SUMMARY][f"{col}22"] = (
                    _big_dict[SUMMARY][f"{col}21"] / _big_dict[SUMMARY][f"{col}20"]
                    if _big_dict[SUMMARY][f"{col}20"]
                    else 0
                )
                _big_dict[SUMMARY][f"{col}23"] = _big_dict[district]["B11"]
                _big_dict[SUMMARY][f"{col}24"] = _big_dict[district]["B12"]
                _big_dict[SUMMARY][f"{col}25"] = _big_dict[district]["F10"]
                _big_dict[SUMMARY][f"{col}26"] = _big_dict[district]["F9"]
                _big_dict[SUMMARY][f"{col}27"] = _big_dict[district]["F11"]
                _big_dict[SUMMARY][f"{col}28"] = _big_dict[district]["F12"]
                _big_dict[SUMMARY][f"{col}29"] = _big_dict[district]["F13"]
                _big_dict[SUMMARY][f"{col}30"] = _big_dict[district]["F14"]

            for row in range(6, 14):
                _big_dict[SUMMARY][f"H{row}"] = sum(
                    filter(
                        lambda x: x is not None,
                        [_big_dict[SUMMARY][f"{col_map[i]}{row}"] for i in range(1, 6)],
                    )
                )

            _big_dict[SUMMARY]["H19"] = sum(
                filter(
                    lambda x: x is not None,
                    [_big_dict[SUMMARY][f"{col_map[i]}19"] for i in range(1, 6)],
                )
            )
            _big_dict[SUMMARY]["H20"] = _big_dict[DISTRICT_ID]["E59"]
            _big_dict[SUMMARY]["H21"] = sum(
                filter(
                    lambda x: x is not None,
                    [_big_dict[SUMMARY][f"{col_map[i]}21"] for i in range(1, 6)],
                )
            )
            _big_dict[SUMMARY]["H22"] = (
                _big_dict[SUMMARY]["H21"] / _big_dict[SUMMARY]["H20"]
                if _big_dict[SUMMARY]["H20"]
                else 0
            )

            for row in range(23, 31):
                _big_dict[SUMMARY][f"H{row}"] = sum(
                    filter(
                        lambda x: x is not None,
                        [_big_dict[SUMMARY][f"{col_map[i]}{row}"] for i in range(1, 6)],
                    )
                )

        if sheet_name == "Introduction":
            populate_introduction()
        elif sheet_name == "Checklist District ID":
            populate_checklist_district_id()
        elif sheet_name == "Checklist Parameters":
            populate_checklist_parameters()
        elif sheet_name.split(" ")[0] == "District":
            populate_district_i(int(sheet_name.split(" ")[1]), df)
        elif sheet_name == "Summary":
            populate_summary()

    def save_all_data(self, path_to_file):
        with open(path_to_file, "w") as f:
            json.dump(self._big_dict, f, indent=4, default=str)

    # a method to output the metrics that show _why_ a zoning is good (if needed)
    # usually you wouldn't want to use this other than debugging
    # (saves files, so will be slow-ish)
    def save_zoning_stats(self, path_to_file):
        """
        Saves all the stats that the `is_good_zoning` function uses
        to `path_to_file`

        Does not format very well...
        """
        with open(f"{path_to_file}", "w") as f:
            f.write(
                f'Required: {self[INTRODUCTION]["I6"]}\t\t\t\t\tModeled: {self[SUMMARY]["H21"]}'
            )
            f.write("\n")
            f.write(
                f'Required: {self[INTRODUCTION]["I7"]}\t\t\t\t\tModeled: {self[SUMMARY]["H19"]}'
            )
            f.write("\n")
            f.write(
                f'Required: {self[INTRODUCTION]["I9"]}\t\t\t\t\tModeled: {self[SUMMARY]["H25"]/ (self[INTRODUCTION]["I6"] * self[INTRODUCTION]["I9"])}'
            )
            f.write("\n")
            f.write(
                f'Required: {self[INTRODUCTION]["I9"]}\t\t\t\t\tModeled: {self[DISTRICT_ID]["E71"]/ (self[INTRODUCTION]["I7"] * self[INTRODUCTION]["I9"])}'
            )

        with open(path_to_file, "w") as f:
            f.write(str(self[SUMMARY]))

    def is_good_zoning(self):
        """
        Once all relevant details are given to the model,
        this method outputs `True` iff
        compared to Guideline Requirements, the Model Results match or exceed:
        * # of housing units
        * Minimum multi-family unit capacity
        * Minimum land area
        * Developable station area
        * % unit capacity within transit station areas
        * % land area located in transit station areas
        """

        def comparator(left, right):
            """
            returns True iff self[INTRODUCTION][left] < self[SUMMARY][right])
            """
            return self[INTRODUCTION][left] < self[SUMMARY][right]

        try:
            # all of these are just defined as in the excel sheet
            min_multi_family_unit_capacity = comparator("I6", "H21")
            min_land_area = comparator("I7", "H19")
            developable_station_area = True

            # extra work unfortunately
            unit_capacity_ratio_within_station_area = self[INTRODUCTION]["I9"] < (
                self[SUMMARY]["H25"]
                / (self[INTRODUCTION]["I6"] * self[INTRODUCTION]["I9"])
            )
            land_area_ratio_within_station_area = self[INTRODUCTION]["I9"] < (
                self[DISTRICT_ID]["E71"]
                / (self[INTRODUCTION]["I7"] * self[INTRODUCTION]["I9"])
            )

            return bool(
                min_multi_family_unit_capacity
                and min_land_area
                and developable_station_area
                and unit_capacity_ratio_within_station_area
                and land_area_ratio_within_station_area
            )
        except:
            raise Exception("You haven't provided all relevant details to the model")

    def __getitem__(self, sheet_name):
        """
        Try to get a sheet from the model. Returns a copy

        Fails if the sheet doesn't exist
        """
        return self._big_dict[sheet_name].copy()
