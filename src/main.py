import os
import json
import numpy as np
import pandas as pd

from pathlib import Path

from core.greedy_algorithm import *
from auxiliary.data_handler import load_data

if __name__ == "__main__":
	# Load data
	aug_school_info, school_assignment = load_data()

	# Initialize greedy parameters
	GREEDY_PARAMS = {
	    "min_schools_per_district": 1,
	    "max_schools_per_district": 500
	}
	# Initialize EarlyStopper params
	EARLY_STOPPER_PARAMS = {
	    "early_stopper_it": 1000,
	    "early_stopper_tol": 0.1
	}

	# Checkpoint variables
	SAVE_METRICS = True
	N_RUNS_PER_STATE = 20

	# All existing states
	ALL_STATES = [
		'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
    	'Colorado', 'Connecticut', 'Delaware',
    	'Florida', 'Georgia', 'Idaho', 'Illinois', 'Indiana',
    	'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    	'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
    	'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico',
    	'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma',
    	'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
    	'South Dakota', 'Texas', 'Utah', 'Vermont', 'Virginia',
   		'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
    ]

	overall_metrics = {}
	if os.path.isfile("./metrics.json"):
	    # Load previous metrics from file
	    with open("./metrics.json", "r") as file:
	        overall_metrics = json.load(file)
	else:
	    # Run and save new metrics
	    for state in ALL_STATES:
	        # Get average run for algorithm
	        mean, std, metrics = get_expectable_run_for_state(
	            state,
	            aug_school_info,
	            school_assignment,
	            N_RUNS_PER_STATE,
	            GREEDY_PARAMS,
	            EARLY_STOPPER_PARAMS
	        )
	        metrics = metrics.as_dict()
	        # Store results
	        overall_metrics[state] = {
	            "mean_inequality": mean,
	            "std_inequality": std,
	            "metrics": metrics
	        }

	    # Save metrics in file
	    if SAVE_METRICS is True:
	        with open("./metrics.json", "w") as file:
	            json.dump(overall_metrics, file)