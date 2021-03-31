import json
import copy

from time import time

class RunMetrics:
    """
    This class is used to track metrics over a single run of the redistricting
    algorithm (done over a single state). Most of its methods are intended to be
    used as callbacks at specific points of its iterations.

    Attributes:
    __per_student_funding_whole_state (float): Per-student funding across the
        state
    __spatial_inequality_values (list of float): List of inequality values,
        registered throughout the algorithm's run
    __percentage_of_schools_redistricted (list of float): List of percentages
        of schools redistricted at each iteration of the algorithm, compared to
        their initial assignment
    __number_of_districts (list of int): List of absolute number of existing
        district at each iteration
    __move_history (list of tuple): List of all redistricting moves performed
        throughout the algorithm's run, containing a school's standardized NCES
        ID, a source district's standardized NCES ID, and a destination
        district's standardized NCES ID
    __district_assignment_by_school_id (dict of str: dict): Mapping between a
        checkpoint label (i.e., 'before' or 'after') and the corresponding
        school/district assignment
    __per_student_funding_by_district_id (dict of str: dict): Mapping between a
        checkpoint label (i.e., 'before' or 'after') and the corresponding
        per-student funding

    Methods:
    on_init(schools, districts, lookup): Initializes necessary class' attributes
        and stores initial metrics' values (prior to the algorithm's
        iterations).
    on_end(schools, districts, lookup): Initializes necessary class' attributes
        and stores final metrics' values (after the algorithm concludes its
        run).
    on_update(schools, districts, lookup): Updates necessary class' attributes
        and calculates runtime metrics' values (during the algorithm's run).
    on_move(iteration_idx, moves): Registers all redistricting moves performed
        during one of the algorithm's iterations.
    as_dict(): Creates a dictionary containing all metrics tracked.
    to_file(filepath): Writes all tracked metrics to a JSON-formatted file.
    __checkpoint_before_and_after_measurements(schools, districts, lookup,
        label): Auxiliary method to handle class' attributes
        update/initialization upon the algorithm's start or end.
    __calculate_inequality(districts, lookup): Auxiliary method to calculate
        spatial inequality for current school/district assignment.
    __calculate_percentage_of_schools_redistricted(schools, lookup): Auxiliary
        method to calculate the percentage of schools that are currently
        redistricted (compared to their initial assignment).
    """
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
        """
        Initializes necessary class' attributes and stores initial metrics'
        values (prior to the algorithm's iterations).

        This method should be called immediately after school/district
        assignment is finalized.

        Parameters:
        schools (list of optimization.entity_nodes.School): List of all
            initialized School instances
        districts (list of optimization.entity_nodes.District): List of all
            initialized District instances
        lookup (optimization.lookup.Lookup): Lookup instance
        """
        # Calculate average funding per student
        total_funding_in_state = sum(map(lambda x: x.get_total_funding(), districts))
        total_students_in_state = sum(map(lambda x: x.get_total_students(), districts))
        # Update variables
        self.__per_student_funding_whole_state = total_funding_in_state / total_students_in_state
        self.__checkpoint_before_and_after_measurements(schools, districts, lookup, "before")
        self.__start_timestamp = time()
    
    def on_end(self, schools, districts, lookup):
        """
        Initializes necessary class' attributes and stores final metrics'
        values (after the algorithm concludes its run).

        This method should be called at the end of the algorithm's last
        iteration.

        Parameters:
        schools (list of optimization.entity_nodes.School): List of all
            initialized School instances
        districts (list of optimization.entity_nodes.District): List of all
            initialized District instances
        lookup (optimization.lookup.Lookup): Lookup instance
        """
        self.__checkpoint_before_and_after_measurements(schools, districts, lookup, "after")
        self.on_update(schools, districts, lookup)
        self.__end_timestamp = time()
    
    def on_update(self, schools, districts, lookup):
        """
        Updates necessary class' attributes and calculates runtime metrics'
        values (during the algorithm's run).

        This method should be called at the end of each of the algorithm's
        iterations.

        Parameters:
        schools (list of optimization.entity_nodes.School): List of all
            initialized School instances
        districts (list of optimization.entity_nodes.District): List of all
            initialized District instances
        lookup (optimization.lookup.Lookup): Lookup instance
        """
        # Calculate inequality
        cur_inequality = self.__calculate_inequality(districts, lookup)
        self.__spatial_inequality_values.append(cur_inequality)
        # Calculate percentage of redistricted schools
        cur_percentage = self.__calculate_percentage_of_schools_redistricted(schools, lookup)
        self.__percentage_of_schools_redistricted.append(cur_percentage)
        # Calculate number of districts
        self.__number_of_districts.append(len(districts))

    def on_move(self, iteration_idx, moves):
        """
        Registers all redistricting moves performed during one of the
        algorithm's iterations.

        This method should be called during any/all of the algorithm's
        iterations, immediately after schools are effectively redistricted. If
        schools are not redistricted, this method needs not be called.

        Parameters:
        iteration_idx (int): Current iteration's index (needs not be a
            continuous variable)
        moves (list of tuple): List of all moves performed during the current
            iteration of the algorithm (i.e., tuples comprised of a redistricted
            school standardized NCES ID, its source district standardized NCES
            ID and its destination district standardized NCES ID) 
        """
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
        """
        Creates a dictionary containing all metrics tracked.

        Returns:
        dict: Resulting dictionary with tracked metrics
        """
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
        """
        Writes all tracked metrics to a JSON-formatted file.

        Parameters:
        filepath (str): Full path for output file, including filename and
            extension
        """
        with open(filepath, "w") as file:
            json.dump(self.as_dict(), file)
    
    def __len__(self):
        return len(self.__spatial_inequality_values)
    
    def __checkpoint_before_and_after_measurements(self, schools, districts, lookup, label):
        """
        Auxiliary method to handle class' attributes update/initialization upon
        the algorithm's start or end.

        Parameters:
        schools (list of optimization.entity_nodes.School): List of all
            initialized School instances
        districts (list of optimization.entity_nodes.District): List of all
            initialized District instances
        lookup (optimization.lookup.Lookup): Lookup instance
        label (str): Should be 'before' or 'after'

        Raises:
        AssertionError: Whenever there is an invalid school/district assignment,
            missing information on number of students or overall funding, or
            when an invalid label is provided
        """
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
        """
        Auxiliary method to calculate spatial inequality for current
        school/district assignment.

        Parameters:
        districts (list of optimization.entity_nodes.District): List of all
            initialized District instances
        lookup (optimization.lookup.Lookup): Lookup instance

        Returns:
        float: Spatial inequality index
        """
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
        """
        Auxiliary method to calculate the percentage of schools that are
        currently redistricted (compared to their initial assignment).

        Parameters:
        districts (list of optimization.entity_nodes.School): List of all
            initialized School instances
        lookup (optimization.lookup.Lookup): Lookup instance

        Returns:
        float: Percentage of currently redistricted schools
        """
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