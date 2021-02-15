import json
import copy

from time import time

class RunMetrics:
    
    # One time measurements
    __per_student_funding_whole_state = None
    
    # Lists of overtime measurements
    __spatial_inequality_values = None
    __percentage_of_schools_redistricted = None
    __number_of_districts = None
    __move_history = None
    
    # Before/after comparison measurements
    __district_assignment_by_school_id = None
    __per_student_funding_by_district_id = None
    
    # One time metrics
    __start_timestamp = None
    __end_timestamp = None
    
    def __init__(self):
        # Overtime measurement initialization
        self.__spatial_inequality_values = []
        self.__percentage_of_schools_redistricted = []
        self.__number_of_districts = []
        self.__move_history = []
        
        # Before/after measurement initialization
        self.__district_assignment_by_school_id = {}
        self.__per_student_funding_by_district_id = {}
        
    def on_init(self, schools, districts, lookup):
        # Claculate average funding per student
        total_funding_in_state = sum(map(lambda x: x.get_total_funding(), districts))
        total_students_in_state = sum(map(lambda x: x.get_total_students(), districts))
        # Update variables
        self.__per_student_funding_whole_state = total_funding_in_state / total_students_in_state
        self.__checkpoint_before_and_after_measurements(schools, districts, lookup, "before")
        self.__start_timestamp = time()
    
    def on_end(self, schools, districts, lookup):
        self.__checkpoint_before_and_after_measurements(schools, districts, lookup, "after")
        self.on_update(schools, districts, lookup)
        self.__end_timestamp = time()
    
    def on_update(self, schools, districts, lookup):
        # Calculate inequality
        cur_inequality = self.__calculate_inequality(districts, lookup)
        self.__spatial_inequality_values.append(cur_inequality)
        # Calculate percentage of redistricted schools
        cur_percentage = self.__calculate_percentage_of_schools_redistricted(schools, lookup)
        self.__percentage_of_schools_redistricted.append(cur_percentage)
        # Calculate number of districts
        self.__number_of_districts.append(len(districts))

    def on_move(self, iteration_idx, moves):
        for move in moves:
            # Get configuration
            school_id = move[0]
            from_district_id = move[1]
            to_district_id = move[2]
            # Add move to moves' history
            self.__move_history.append((
                iteration_idx,
                school_id,
                from_district_id,
                to_district_id
            ))
        
    def as_dict(self):
        return {
            # Overtime measurements
            "spatial_inequality": copy.copy(self.__spatial_inequality_values),
            "percentage_of_schools_redistricted": copy.copy(self.__percentage_of_schools_redistricted),
            "number_of_districts": copy.copy(self.__number_of_districts),
            "move_history": copy.copy(self.__move_history),
            # Before/after measurements
            "district_assignment_by_school_id": copy.copy(self.__district_assignment_by_school_id),
            "per_student_funding_by_district_id": copy.copy(self.__per_student_funding_by_district_id),
            # One time measurements
            "time_elapsed": self.__end_timestamp - self.__start_timestamp,
            "per_student_funding_whole_state": self.__per_student_funding_whole_state
        }
    
    def to_file(self, filepath):
        with open(filepath, "w") as file:
            json.dump(self.as_dict(), file)
    
    def __len__(self):
        return len(self.__spatial_inequality_values)
    
    def __checkpoint_before_and_after_measurements(self, schools, districts, lookup, label):
        assert(self.__district_assignment_by_school_id is not None)
        assert(self.__per_student_funding_by_district_id is not None)
        assert(label == "before" or label == "after")
        
        # Initialize school assignment
        get_district_id = lambda school: lookup.get_district_by_school_id(school.get_id()).get_id()
        self.__district_assignment_by_school_id[label] = dict(map(
            lambda school: (school.get_id(), get_district_id(school)),
            schools
        ))
        # Initialize district funding
        get_per_student_funding = lambda district: district.get_total_funding() / district.get_total_students()
        self.__per_student_funding_by_district_id[label] = dict(map(
            lambda district: (district.get_id(), get_per_student_funding(district)),
            districts
        ))
        
    def __calculate_inequality(self, districts, lookup):
        get_per_student_funding = lambda district: district.get_total_funding() / district.get_total_students()
        abs_funding_diff = lambda x,y: abs(get_per_student_funding(x) - get_per_student_funding(y))
        overall_inequality = 0
        normalization_factor = 0
        for district in districts:
            neighboring_districts = lookup.get_neighboor_districts_by_district_id(district.get_id())
            full_neighborhood = [*neighboring_districts, district]
            ineq_contribution = sum(map(
                lambda x: abs_funding_diff(district, x),
                full_neighborhood
            ))
            overall_inequality += ineq_contribution / len(full_neighborhood)
            normalization_factor += get_per_student_funding(district)
        return overall_inequality / normalization_factor
    
    def __calculate_percentage_of_schools_redistricted(self, schools, lookup):
        # Get initial assignment
        initial_district_assignment = self.__district_assignment_by_school_id["before"]
        # Extract current assignment
        get_district_id = lambda school: lookup.get_district_by_school_id(school.get_id()).get_id()
        cur_district_assignment = dict(map(
            lambda school: (school.get_id(), get_district_id(school)),
            schools
        ))
        # Filter schools that were redistricted
        is_redistricted = lambda school: initial_district_assignment[school.get_id()] != cur_district_assignment[school.get_id()]
        schools_redistricted = list(filter(
            is_redistricted,
            schools
        ))
        # Return final percentage
        return 100 * len(schools_redistricted) / len(schools)