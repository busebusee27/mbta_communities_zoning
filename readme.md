# What this does
Given a community of interest, it will create zonings out of it,
process each of the zonings, pass the output into the 
compliance model, and save the result of whether or not each
zoning was good or not.

# Code Layout
### `src`
The meat of the code
* `zoner.r`: uses `alarm-redist` to generate zonings
* `shapefile_processor.py`: follows the compliance model 
    user guide for processing the input to the model
* `excel_model.py`: the whole of the compliance model as
    a Python class

### `utils`
Helpers
* `shapefile_utils.py`: utils for shapefile processing
* `calc_layers.py`: provides files needed for the model
* `compliance_utils.py`: utils for the model

### `resources`
Things needed to run the model
* `community_info.csv`: info that the compliance model loads
    for the community it's being run on.
    This file comes from one of the sheets in the original model
* `half_mile.zip`: shapefile containing half-mile radius bubbles
    around all MBTA stations/stops.
    This file is provided by the state
* `GDDD.zip`: another shapefile (less sure of what it's about)
    This file is provided by the state

### `out`
All the outputs from running the code

### `/`
* `parameters.py`: where you add some parameters for the model
* `interface.py`: where you should run the code from
* `*.zip`: a user-provided shapefile for the community to run on

# How to run
* Run `pip install -r requirements.txt` to install the packages needed.
This should hopefully be fine, but you may need to install more manually.

* Provide a shapefile.
Ideally the shapefile should be from 
[the state website (the basic one)](https://www.mass.gov/info-details/mbta-communities-compliance-model-components)
Despite the 'basic' name, the compliance model is only supposed to be
run on these ones (from the compliance user guide)

* Enter your parameters into `parameters.py`. If you only need 3 
districts, you can ignore disctricts 4 and 5.

* Setup the bottom of `interface.py` with
what you need, and then just run that file.

# Additional settings
You can go into `zoner.r` and change how `alarm-redist` is run.
Right now it's set up to give 100 zonings in total... from what I've
found, a lower number doesn't get it to go faster.

For the full Cambridge file, it took me a few hours to run.
For debugging, you may want to pass in a small file

# What to add
* The `GDDD.zip` shapefile is provided by the state. It is used in
    processing for one of the compliance model's sheets. The code
    does not have it right now. I was unable to open the file both in
    Python, and with ArcGis (at least online). If that's fixed, changes
    only need to be made in `shapefile_utils.py` and `calc_layers.py`.
    The rest is setup to work with it.
* Cleaner paramter configuration.
* More options for running in `interface.py`.
* There are tests for the compliance model not included here. May
    want to add them, and add more tests for the rest. For this, I 
    verified the code against ArcGis