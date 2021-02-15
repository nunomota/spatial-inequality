import pandas as pd

def fix_ncesid(ncesid, mode):
    padding = {
        "school": 12,
        "district": 7
    }.get(mode, 0)
    return str(ncesid).zfill(padding)

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

class DataHandler:
    
    __data_path = None
    
    def __init__(self, data_path="../data"):
        self.__data_path = data_path
        
    def __read_file(self, filename, compression="gzip", encoding="utf-8"):
         return pd.read_csv(
            f"{self.__data_path}/{filename}",
            compression=compression,
            encoding=encoding
        )
    
    def __format_cols(self, df, type_dict):
        formatted_df = df.copy()
        for col_name, dtype in type_dict.items():
            formatted_df[col_name] = formatted_df[col_name].astype(dtype)
        return formatted_df
    
    def get_augmented_school_info(self):
        # Read data
        school_info = self.get_school_info()
        district_info = self.get_district_info()
        school_assignment = self.get_school_assignment()
        # Add 'per student revenue' to each school's attributes
        school_info = pd.merge(school_info, school_assignment[["district_id"]], left_index=True, right_index=True)
        school_info = pd.merge(school_info, district_info, left_on="district_id", right_index=True)
        return school_info.drop(["district_id"], axis=1)
    
    def get_school_info(self):
        # Read data
        filename = "school_info.csv"
        df = self.__read_file(filename)
        # Fix NCESID
        df["school_id"] = df["school_id"].apply(lambda x: fix_ncesid(x, mode="school"))
        # Remove invalid schools (schools that have NaN values and do
        # not show up in 'https://nces.ed.gov/ccd/schoolsearch/').
        df = df.dropna()
        # Assign type to each column
        df = self.__format_cols(df, type_dict={
                "school_id": str,
                "neighbour_ids": str,
                "total_students": int
            }
        )
        # Return final dataframe
        return df.set_index("school_id", drop=True)
    
    def get_district_info(self):
        # Read data
        filename = "district_info.csv"
        df = self.__read_file(filename)
        # Fix NCESID
        df["district_id"] = df["district_id"].apply(lambda x: fix_ncesid(x, mode="district"))
        # Assign type to each column
        df = self.__format_cols(df, type_dict={
                "district_id": str,
                "adjusted_local_revenue_per_student": float,
                "adjusted_state_revenue_per_student": float,
                "adjusted_federal_revenue_per_student": float,
                "adjusted_total_revenue_per_student": float,
            }
        )
        # Return final dataframe
        return df.set_index("district_id", drop=True)
    
    def get_school_assignment(self):
        # Read data
        filename = "school_assignment.csv"
        df = self.__read_file(filename)
        # Fix NCESID
        df["school_id"] = df["school_id"].apply(lambda x: fix_ncesid(x, mode="school"))
        df["district_id"] = df["district_id"].apply(lambda x: fix_ncesid(x, mode="district"))
        # Assign type to each column
        df = self.__format_cols(df, type_dict={
                "school_id": str,
                "district_id": str,
                "state_name": str
            }
        )
        # Return final dataframe
        return df.set_index("school_id", drop=True)