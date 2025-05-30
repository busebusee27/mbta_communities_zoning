"""
this file is supposed to do the final wiring from start to finish:
    * calling R zoning script on a given community
    * passing the zones into the python shp file dealer
    * passing the result from there into the compliance model
    * saving everything needed, including the final result
"""

import os
import json
import zipfile
import pyper
from src.shapefile_processor import process_shapefile
from src.excel_model import ComplianceModel
from parameters import PARAMETERS

INTRODUCTION = "Introduction"
CHECKLIST_DISTRICT_ID = "Checklist District ID"
CHECKLIST_PARAMETERS = "Checklist Parameters"
DISTRICT_1 = "District 1"
DISTRICT_2 = "District 2"
DISTRICT_3 = "District 3"
DISTRICT_4 = "District 4"
DISTRICT_5 = "District 5"
SUMMARY = "Summary"

INITIALIZATIONS = {
    INTRODUCTION: {},
    CHECKLIST_PARAMETERS: PARAMETERS
}


def zone_and_analyze(city_name, path_to_shp, use_cache=False, run_once=False):
    """
    Does what's described above. Returns a list `results`, where
    `results[i]` is True iff `zoning[i]` from the generated zonings
    is accepted by the compliance model

    Use `use_cache` to run on an older set of zonings. Helpful for debugging.
    Will fail if cache does not exist from a previous run

    Use `run_once` to only run for one zoning, save the output, and stop
    """

    def extract_and_rename_shapefiles(zip_path, extract_dir):
        """
        Extract .shp, .shx, and .dbf files from the zip archive and rename them to
        community.shp, community.shx, community.dbf
        """
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Filter files with extensions .shp, .shx, .dbf
            files_to_extract = [
                f for f in zip_ref.namelist() if f.endswith((".shp", ".shx", ".dbf"))
            ]

            for file in files_to_extract:
                # Extract the file
                zip_ref.extract(file, extract_dir)

                # Get the file extension
                _, ext = os.path.splitext(file)
                new_filename = f"community{ext}"

                # Construct file paths
                old_path = os.path.join(extract_dir, file)
                new_path = os.path.join(extract_dir, new_filename)

                # Rename/move the file to the extract directory root
                os.rename(old_path, new_path)
                print(f"Extracted and renamed: {file} -> {new_filename}")

    def fill_model(data_in):
        all_data = data_in.copy()

        model = ComplianceModel()

        model.fill_sheet(INTRODUCTION, all_data[INTRODUCTION])
        model.populate_sheet(INTRODUCTION)

        model.fill_sheet(CHECKLIST_DISTRICT_ID, all_data[CHECKLIST_DISTRICT_ID])
        model.populate_sheet(CHECKLIST_DISTRICT_ID)

        model.fill_sheet(CHECKLIST_PARAMETERS, all_data[CHECKLIST_PARAMETERS])
        model.populate_sheet(CHECKLIST_PARAMETERS)

        model.fill_sheet(DISTRICT_1, all_data[DISTRICT_1])
        model.populate_sheet(DISTRICT_1, df=all_data[DISTRICT_1])
        model.fill_sheet(DISTRICT_2, all_data[DISTRICT_2])
        model.populate_sheet(DISTRICT_2, df=all_data[DISTRICT_2])
        model.fill_sheet(DISTRICT_3, all_data[DISTRICT_3])
        model.populate_sheet(DISTRICT_3, df=all_data[DISTRICT_3])
        model.fill_sheet(DISTRICT_4, all_data[DISTRICT_4])
        model.populate_sheet(DISTRICT_4, df=all_data[DISTRICT_4])
        model.fill_sheet(DISTRICT_5, all_data[DISTRICT_5])
        model.populate_sheet(DISTRICT_5, df=all_data[DISTRICT_5])

        model.populate_sheet(SUMMARY)

        return model

    # use existing zoning if requested, otherwise load a new one
    if use_cache:
        with open("cached.json", "r") as f:
            zonings = json.load(f)
    else:
        # this is needed for R... can't figure out how to
        # open the shp file from just `"./"`
        abs_path_to_dir = os.path.abspath("./")
        extract_and_rename_shapefiles(path_to_shp, ".")

        r = pyper.R(use_pandas=True)
        r("source('./src/zoner.r')")
        r(f"zonings <- zone('{abs_path_to_dir}', 3)")
        zonings = r.get("zonings")

    results = [False] * len(zonings)  # initialize result array

    for idx, zoning in enumerate(zonings):
        all_data = INITIALIZATIONS.copy()
        all_data[INTRODUCTION]["I3"] = city_name

        (checklist_district_stuff, sheets) = process_shapefile(
            path_to_shp, zoning, f"out/{city_name}_{idx}"
        )

        all_data.update(checklist_district_stuff)
        all_data[CHECKLIST_DISTRICT_ID][
            "C43"
        ] = "N"  # TODO: make it so that the update doesn't overwrite C43 from initializer
        all_data.update(sheets)

        model = fill_model(all_data)
        print(model.is_good_zoning())
        results[idx] = model.is_good_zoning()

        if run_once:
            model.save_zoning_stats(f"out/{city_name}_result_{idx}.txt")
            model.save_all_data("out/all_data.json")
            break

    # clean up
    os.remove("community.shp")
    os.remove("community.shx")
    os.remove("community.dbf")

    return zonings, results


if __name__ == "__main__":
    community = "Cambridge"

    zonings, results = zone_and_analyze(community, "./community.zip")

    # save the zonings
    with open(f"out/{community}_zonings.json", "w") as f:
        json.dump(zonings, f)

    # save the result
    with open(f"out/{community}_results.json", "w") as f:
        json.dump(results, f)
