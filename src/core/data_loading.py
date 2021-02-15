import numpy as np

from auxiliary.data_handler import DataHandler

def remove_cross_state_neighbors(aug_school_info, school_assignment):
    # Copy data handler references
    aug_school_info = aug_school_info.copy()

    # Filter out cross-state neighbors
    get_state = lambda school_id: school_assignment.loc[school_id]["state_name"]
    from_same_state = lambda id_l, id_r: get_state(id_l) == get_state(id_r)

    def filter_cross_state_neighbors(row):
        if len(row["neighbour_ids"]) == 0:
            return row
        neighbor_ids_set = set(row["neighbour_ids"].split(","))
        valid_neighbor_ids_set = set(filter(
            lambda neighbor_id: from_same_state(row.name, neighbor_id),
            neighbor_ids_set
        ))
        row["neighbour_ids"] = ",".join(list(valid_neighbor_ids_set))
        return row
        
    aug_school_info = aug_school_info.apply(
        filter_cross_state_neighbors,
        axis=1
    )

    return aug_school_info

def remove_invalid_entries(aug_school_info, school_assignment):
    # Copy data handler references
    aug_school_info = aug_school_info.copy()
    school_assignment = school_assignment.copy()

    # Remove schools without funding or students
    replace_zero_with_nan = lambda x: x.replace(0, np.nan, inplace=True)
    replace_zero_with_nan(aug_school_info["adjusted_total_revenue_per_student"])
    replace_zero_with_nan(aug_school_info["total_students"])
    aug_school_info = aug_school_info.dropna(subset=[
        "adjusted_total_revenue_per_student",
        "total_students"
    ])

    # Set of all schools w/ available info
    valid_school_ids_set = set(aug_school_info.index)

    # Filter out neighbors wo/ info
    def filter_unavailable_neighbors(neighbor_ids_str, valid_school_ids_set):
        if len(neighbor_ids_str) == 0:
            return []
        neighbor_ids_set = set(neighbor_ids_str.split(","))
        valid_neighbor_ids_set = neighbor_ids_set.intersection(valid_school_ids_set)
        return ",".join(list(valid_neighbor_ids_set))

    aug_school_info["neighbour_ids"] = aug_school_info["neighbour_ids"].apply(
        lambda neighbor_ids_str: filter_unavailable_neighbors(neighbor_ids_str, valid_school_ids_set)
    )

    # Filter out school assignments wo/ info
    school_assignment = school_assignment[school_assignment.index.isin(aug_school_info.index)]

    return aug_school_info, school_assignment

def load_data():
    # Create DataHandler object
    dh = DataHandler()
    aug_school_info = dh.get_augmented_school_info()
    school_assignment = dh.get_school_assignment()

    aug_school_info, school_assignment = remove_invalid_entries(aug_school_info, school_assignment)
    aug_school_info = remove_cross_state_neighbors(aug_school_info, school_assignment)
    return aug_school_info, school_assignment