"""
This file implements high-level computations on top of standardized public
schools' data (e.g., extracting a school's neighbors). Simple unit tests can be
found at the bottom, automatically ran when (directly) running the script.

NOTE: For all implemented functions in this script, the
return statements also include an (often redundant) explicit
type-casting statement. This is to prevent test failure due
to pandas' implicit usage of numpy types, which do not typecheck
with native python types (e.g. utilizing 'isinstance' on a
'numpy.int64' object will yield 'False' when checking against a
regular 'int').
"""
import numpy as np
import pandas as pd

def get_schools_in_state(state_name, school_assignment):
    """
    Gets all schools currently assigned to a state. 
  
    Args:
        state_name (str): Full name of target state (e.g. 'Alabama').
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        list: All NCES IDs for corresponding schools (returns an empty
            list in case there are none).
    """
    return list(school_assignment[school_assignment["state_name"] == state_name.title()].index.unique().tolist())

def get_districts_in_state(state_name, school_assignment):
    """
    Gets all districts currently assigned to a state. 
  
    Args:
        state_name (str): Full name of target state (e.g. 'Alabama').
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        list: All NCES IDs for corresponding districts (returns an empty
            list in case there are none).
    """
    return list(school_assignment[school_assignment["state_name"] == state_name.title()]["district_id"].unique().tolist())

def get_schools_in_district(district_id, school_assignment):
    """
    Gets all schools currently assigned to a district. 
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        list: All NCES IDs for corresponding schools (returns an empty list in
            case there are none).
    """
    return list(school_assignment[school_assignment["district_id"] == district_id].index.unique().tolist())

def get_neighbouring_schools(school_id, school_info):
    """
    Gets all schools currently in the neighbourhood of a school
    (not including the school itself). 
  
    Args:
        school_id (str): NCES ID of target school (e.g. '010000500889').
        school_info (pandas.DataFrame): Target school information (as formatted
        by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        list: All NCES IDs for corresponding schools (returns an empty list in
            case there are none).
    """
    parse_neighbours = lambda x: x.split(",") if len(x) > 0 else []
    try:
        neighbours_string = school_info.loc[school_id]["neighbour_ids"]
        return list(parse_neighbours(neighbours_string))
    except KeyError:
        return list([])
    

def get_neighbouring_districts(district_id, school_info, school_assignment):
    """
    Gets all districts currently in the neighbourhood of a district
    (not including the district itself). 
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        school_info (pandas.DataFrame): Target school information (as formatted
            by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        list: All NCES IDs for corresponding districts (returns an empty list in
            case there are none).
    """
    flatten = lambda l: [item for sublist in l for item in sublist]
    schools_in_district = get_schools_in_district(district_id, school_assignment)
    all_neighbouring_schools = flatten(map(
        lambda school_id: get_neighbouring_schools(school_id, school_info),
        schools_in_district
    ))
    neighbouring_districts = school_assignment[school_assignment.index.isin(all_neighbouring_schools)]["district_id"].unique().tolist()
    if district_id in neighbouring_districts:
        neighbouring_districts.remove(district_id)
    return list(neighbouring_districts)

def get_school_total_funding(school_id, aug_school_info):
    """
    Gets (total) funding associated with a school.
  
    Args:
        district_id (str): NCES ID of target school (e.g. '010000500889').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        float: Single number comprising school-level data.
    """
    return float(aug_school_info.loc[school_id]["adjusted_total_revenue_per_student"] * aug_school_info.loc[school_id]["total_students"])

def get_district_total_funding(district_id, aug_school_info, school_assignment):
    """
    Gets (total) funding associated with a district, based on
    provided school district assignment.
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school
            assignment (as formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        float: Single number comprising district-level data.
    """
    schools_in_district = get_schools_in_district(district_id, school_assignment)
    district_school_info = aug_school_info[aug_school_info.index.isin(schools_in_district)]
    return float((district_school_info["adjusted_total_revenue_per_student"] * district_school_info["total_students"]).sum())

def get_school_total_students(school_id, aug_school_info):
    """
    Gets total number of students associated with a school.
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        int: Single number comprising school-level data.
    """
    return int(aug_school_info.loc[school_id]["total_students"])

def get_district_total_students(district_id, aug_school_info, school_assignment):
    """
    Gets total number of students associated with a district, based on
    provided school district assignment.
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        int: Single number comprising district-level data.
    """
    schools_in_district = get_schools_in_district(district_id, school_assignment)
    district_school_info = aug_school_info[aug_school_info.index.isin(schools_in_district)]
    return int(district_school_info["total_students"].sum())

def get_per_student_funding(district_id, aug_school_info, school_assignment):
    """
    Gets per-student (total) funding associated with a district, based on
    provided school district assignment.
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        float: Single number comprising district-level data.
    """
    total_funding = get_district_total_funding(district_id, aug_school_info, school_assignment)
    total_students = get_district_total_students(district_id, aug_school_info, school_assignment)
    return float(total_funding / total_students)

def get_possible_school_transitions(district_id, school_info, school_assignment):
    """
    Gets all possible school transitions between a given district and
    its neighbouring districts (i.e. if a school has neighbouring
    schools that belong to a neighbouring district, it is at the border
    and can easily be assigned to the neighbouring district - while
    maintaining contiguous district assignments). School transitions
    can either happen 'from' or 'to' the provided district.
  
    NOTE: The contiguous assumption stated before, although generally
    true, may not be so in all instances. It can be that by assigning
    one school to another district, we isolate another school from the
    district where it originated from. These cases may need to be handled.
  
    Args:
        district_id (str): NCES ID of target district (e.g. '0100005').
        school_info (pandas.DataFrame): Target school information (as formatted
            by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school assignment (as
        formatted by `auxiliary.data_handler.DataHandler`).
    
    Returns:
        list: List of triplets containing (i) the ID of a school to be
            transitioned, (ii) the ID of the provenance district, and (iii) the
            ID of th destination district.
    """
    school_transitions = []
    schools_in_district = get_schools_in_district(district_id, school_assignment)
    for school_id in schools_in_district:
        school_neighbourhood = get_neighbouring_schools(school_id, school_info)
        school_neighbourhood_districts = school_assignment[school_assignment.index.isin(school_neighbourhood)]["district_id"].values
        for neighbour_school_id, neighbour_district_id in zip(school_neighbourhood, school_neighbourhood_districts):
            # If neighbouring school is within the same district ignore
            if district_id == neighbour_district_id: continue
            # Otherwise, either school could be transitioned
            school_transitions.append((school_id, district_id, neighbour_district_id))
            school_transitions.append((neighbour_school_id, neighbour_district_id, district_id))
    return list(school_transitions)

if __name__ == "__main__":
    
    ###################
    # Dummy DataFrames
    ###################
    
    dummy_school_info = pd.DataFrame({
        "school_id": ["010000500889", "010000500890", "010000500891"],
        "neighbour_ids": ["010000500890", "010000500889,010000500891", "010000500890"],
        "school_name": ["School A", "School B", "School C"],
        "total_students": [100, 200, 150]
    }).set_index("school_id")
    
    dummy_aug_school_info = pd.DataFrame({
        "school_id": ["010000500889", "010000500890", "010000500891"],
        "neighbour_ids": ["010000500890", "010000500889,010000500891", "010000500890"],
        "school_name": ["School A", "School B", "School C"],
        "total_students": [100, 200, 150],
        "adjusted_local_revenue_per_student": [20.0, 30.0, 40.0]
    }).set_index("school_id")
    
    dummy_school_assignment = pd.DataFrame({
        "school_id": ["010000500889", "010000500890", "010000500891"],
        "district_id": ["0100005", "0100005", "0100006"],
        "state_name": ["State A", "State A", "State B"]
    }).set_index("school_id")
    
    ###################
    # Utility Functions
    ###################
    
    # Utility functions for descriptive assertions
    def assert_type(dtype, var):
        assert isinstance(var, dtype), f"Wrong type. Expected '{dtype}', got '{type(var)}'."
        return True
        
    def assert_result(cond, actual, target):
        assert cond, f"Wrong result. Expected '{target}', got '{actual}'."
        return True
    
    # Utility functions for variables' comparison
    def equal_ints(actual, target):
        assert_type(int, actual)
        assert_type(int, target)
        return assert_result(actual == target, actual, target)
        
    def equal_floats(actual, target):
        assert_type(float, actual)
        assert_type(float, target)
        return assert_result(np.isclose(actual, target), actual, target)
        
    def equal_lists(actual, target, comp=lambda x,y: x==y):
        assert_type(list, actual)
        assert_type(list, target)
        return assert_result(len(actual) == len(target) and all([comp(a,t) for a,t in zip(actual, target)]), actual, target)
        
    def equal_tuples(actual, target, comp=lambda x,y: x==y):
        assert_type(tuple, actual)
        assert_type(tuple, target)
        return assert_result(len(actual) == len(target) and all([comp(a,t) for a,t in zip(actual, target)]), actual, target)
    
    ###################
    # Unit Tests
    ###################
    
    # Initial testing print
    print("Testing all functions:")
    
    # Test 'get_schools_in_state'
    actual_result = get_schools_in_state("State A", dummy_school_assignment)
    target_result = ["010000500889", "010000500890"]
    equal_lists(actual_result, target_result)
    print("\t'get_schools_in_state': OK")
    
    # Test 'get_districts_in_state'
    actual_result = get_districts_in_state("State A", dummy_school_assignment)
    target_result = ["0100005"]
    equal_lists(actual_result, target_result)
    print("\t'get_districts_in_state': OK")
    
    # Test 'get_schools_in_district'
    actual_result = get_schools_in_district("0100005", dummy_school_assignment)
    target_result = ["010000500889", "010000500890"]
    equal_lists(actual_result, target_result)
    print("\t'get_schools_in_district': OK")
    
    # Test 'get_neighbouring_schools'
    actual_result = get_neighbouring_schools("010000500889", dummy_school_info)
    target_result = ["010000500890"]
    equal_lists(actual_result, target_result)
    print("\t'get_neighbouring_schools': OK")
    
    # Test 'get_neighbouring_districts'
    actual_result = get_neighbouring_districts("0100005", dummy_school_info, dummy_school_assignment)
    target_result = ["0100006"]
    equal_lists(actual_result, target_result)
    print("\t'get_neighbouring_districts': OK")
    
    # Test 'get_school_total_funding'
    actual_result = get_school_total_funding("010000500889", dummy_aug_school_info)
    target_result = 20.0
    equal_floats(actual_result, target_result)
    print("\t'get_school_total_funding': OK")
    
    # Test 'get_district_total_funding'
    actual_result = get_district_total_funding("0100005", dummy_aug_school_info, dummy_school_assignment)
    target_result = 8000.0
    equal_floats(actual_result, target_result)
    print("\t'get_district_total_funding': OK")
    
    # Test 'get_school_total_students'
    actual_result = get_school_total_students("010000500889", dummy_aug_school_info)
    target_result = 100
    equal_ints(actual_result, target_result)
    print("\t'get_school_total_students': OK")
    
    # Test 'get_district_total_students'
    actual_result = get_district_total_students("0100005", dummy_aug_school_info, dummy_school_assignment)
    target_result = 300
    equal_ints(actual_result, target_result)
    print("\t'get_district_total_students': OK")
    
    # Test 'get_per_student_funding'
    actual_result = get_per_student_funding("0100005", dummy_aug_school_info, dummy_school_assignment)
    target_result = 8000.0 / 300
    equal_floats(actual_result, target_result)
    print("\t'get_per_student_funding': OK")
    
    # Test 'get_possible_school_transitions'
    actual_result = get_possible_school_transitions("0100005", dummy_school_info, dummy_school_assignment)
    target_result = [("010000500890", "0100005", "0100006"), ("010000500891", "0100006", "0100005")]
    equal_lists(actual_result, target_result, equal_tuples)
    print("\t'get_possible_school_transitions': OK")
    
    # Final success print
    print("All tests passed!")