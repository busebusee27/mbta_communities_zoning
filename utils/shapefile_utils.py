"""
Provides utils for pre-processing information from shapefiles
to use the compliance model
"""

import geopandas as gpd


def area_projection(gdf, drop=True):
    """
    Given `gdf` with polygons inside it, return a gdf that calculates
    area based on NAD83 projection thing

    If `drop`, drops everything but the geometry and area
    """

    gdf = gdf.to_crs(epsg=26986)
    gdf["area"] = gdf.geometry.area / 4046.8564224
    if drop:
        gdf = gdf[["geometry", "area"]]

    return gdf


def total_area(gdf, area_field="area"):
    """
    Given `gdf` and `area_field`, return the sum of areas. Reports
    area in the same units as in `gdf`.
    """
    return gdf[area_field].sum()


def area_intersection(gdf1, gdf2):
    """
    Given `gdf1` and `gdf2`, returns the NAD83 projection of where the two
    intersect, based on `gdf1`. The new station area is recorded into
    `stn_area`
    """
    intersection = gpd.overlay(gdf1, gdf2, how="intersection")
    intersection["intersection_area"] = intersection.geometry.area

    gdf1[["stn_area"]] = area_projection(intersection)[["area"]]

    return gdf1


def gross_ddd_thing(gdf):
    """
    Place holder function. Waiting to figure out how to use the
    gross density denominator deduction shapefile
    """
    gdf["ddd"] = 0
    return gdf
