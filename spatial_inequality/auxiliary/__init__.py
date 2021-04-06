"""
Auxiliary functions and classes to easily parse, filter and explore all of our
data through simple import statements.

Example:
    ```python
    from spatial_inequality.auxiliary.functions import *
    from spatial_inequality.auxiliary.inequality import *
    from spatial_inequality.auxiliary.data_handler import *
    
    # Load all data for public schools
    aug_school_info, school_assignment = load_data()
    
    # Get all schools in a given state
    schools_in_alabama = sorted(get_schools_in_state("Alabama", school_assignment))

    # Get per-student funding for all selected schools
    def get_funding_per_student(school_id):
        total_students = get_school_total_students(x, aug_school_info)
        total_funding = get_school_total_funding(x, aug_school_info)
        return total_funding / total_students
    school_funding_per_student = [
        get_school_per_student_funding(id) for id in schools_in_alabama
    ]

    # Define a mapping between a school's id and its idx in the benefit vector
    school_id_to_idx = {id:idx for idx, id in enumerate(schools_in_alabama)}
    school_idx_to_id = {idx:id for id, idx in school_id_to_idx.items()}
    def get_school_neighbours_from_idx(school_idx):
        school_id = school_idx_to_id[school_idx]
        neighbour_ids = get_neighbouring_schools(school_id, aug_school_info)
        return list(map(lambda x: school_id_to_idx[x], neighbour_ids))

    # Calculate inequalities
    gini = gini_index(school_funding_per_student)
    spatial = spatial_index(
        benefit_vector=school_funding_per_student,
        get_neighbours=get_school_neighbours_from_idx
    )
    ```
"""