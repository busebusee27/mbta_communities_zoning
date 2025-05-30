"""
Once zoned, this file is used to pre-process stuff and
get information to use in the compliance model
"""

import os
import zipfile
import pandas as pd
import geopandas as gpd
from utils import shapefile_utils
from utils.calc_layers import HALF_MILE_GDF, GDDD_GDF

EMPTY_DF = pd.DataFrame(
    columns=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]
)

column_name_mapper = {
    "index": "A",
    "LOC_ID": "B",
    "Address": "C",
    "Owner": "D",
    "UseCodes": "E",
    "UseDesc": "F",
    "TRANSIT": "G",
    "ACRES": "H",
    "SQFT": "I",
    "PublicInst": "J",
    "NonPubExc": "K",
    "Tot_Exclud": "L",
    "Tot_Sensit": "M",
}


def process_shapefile(city_shp_file_path, zoning, output_filename):
    """
    `city_shp_file_path` is the path to the zipfile containing all the
    shapefile stuff needed

    `zoning` should be provided as a list, where `zoning[i]` gives the
    district number that is assigned to parcel `i`

    Creates a shapefile named `output_filename` at `output_path`

    Returns
        * a dict which can be used with the Excel Compliance Model
        object
        * info needed in `Checklist District ID`, and the `District <x>`
        sheets

    Fails if the number of parcels in the shapefile don't match the
    number of entries in the zoning list
    """

    def _divide_into_zones(gdf, zoning):
        """
        Given a geo dataframe, this thing will return a new geo dataframe
        that uses `seed` to make some combination of the polygons in `gdf`
        into zones made up of those polygons

        The resulting object has only the `geometry` and `area` attributes.

        Area will be in acres, and according to the NAD83 MA projection thing
        """
        gdf["zone_id"] = zoning

        zoned_gdf = gdf.dissolve(by="zone_id")
        zoned_gdf = zoned_gdf.reset_index(drop=True)

        zoned_gdf = shapefile_utils.area_projection(zoned_gdf)

        return zoned_gdf

    def _return_district_sheets(zoning_gdf, land_map_gdf):
        district_sheets = {f"District {i}": EMPTY_DF.copy() for i in range(1, 6)}

        for idx, district in zoning_gdf.iterrows():
            district_gdf = gpd.GeoDataFrame([district])
            overlap = gpd.overlay(land_map_gdf, district_gdf, how="intersection")

            overlap_no_geometry = (
                overlap.drop(columns=["geometry", "area", "stn_area", "ddd"])
                .reset_index()
                .rename(columns=column_name_mapper)
            )

            sheet_name = f"District {idx+1}"
            district_sheets[sheet_name] = overlap_no_geometry.copy()

        return district_sheets

    def _return_district_summaries(final_zoning_gdf):
        final_zoning_gdf = shapefile_utils.area_projection(
            final_zoning_gdf.copy(), drop=False
        )

        sheet_name = "Checklist District ID"
        ret = {sheet_name: {}}
        for idx, row in final_zoning_gdf.iterrows():
            ret[sheet_name][
                f"B{54+idx}"
            ] = idx  # this is the district's name -- we don't care about it
            ret[sheet_name][f"C{54+idx}"] = row["area"]
            ret[sheet_name][f"D{54+idx}"] = row["stn_area"]
            ret[sheet_name][f"E{54+idx}"] = row["ddd"]

        return ret

    def _save_result_shp_file(final_zoning_gdf, name=output_filename):
        temp_dir = "temp_shapefiles"  # Separate temporary directory
        os.makedirs(temp_dir, exist_ok=True)

        # Create shapefiles in temp_dir
        output_shapefile = f"{temp_dir}/zoned.shp"
        final_zoning_gdf.to_file(output_shapefile)

        # Create ZIP in final output location (not in temp_dir)
        zip_output_path = f"{name}.zip"  # Not inside temp_dir
        with zipfile.ZipFile(zip_output_path, "w") as zipf:
            for file in os.listdir(temp_dir):
                zipf.write(os.path.join(temp_dir, file), arcname=file)

        # Cleanup temp directory
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

    ## ACTUAL CODE STARTS
    land_map_gdf = gpd.read_file(city_shp_file_path)
    # land_map_gdf = land_map_gdf.query("Owner == 'MASSACHUSETTS INSTITUTE OF TECHNOLOGY'")

    gdf = land_map_gdf.copy()
    final_zoning_gdf = shapefile_utils.gross_ddd_thing(
        shapefile_utils.area_intersection(
            _divide_into_zones(gdf, zoning), HALF_MILE_GDF
        )
    )

    _save_result_shp_file(final_zoning_gdf)

    return (
        _return_district_summaries(final_zoning_gdf),
        _return_district_sheets(final_zoning_gdf, land_map_gdf),
    )
