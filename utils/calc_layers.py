"""
Provides the 'Key Calculation Layers' from 
https://www.mass.gov/info-details/mbta-communities-compliance-model-components

These are used in the pre-processing for the compliance model
"""

import geopandas as gpd
import utils.shapefile_utils

_gdf = gpd.read_file("./resources/half_mile.zip")
HALF_MILE_GDF = utils.shapefile_utils.area_projection(_gdf)

# TODO: figure why python can't load this one...
GDDD_GDF = None
