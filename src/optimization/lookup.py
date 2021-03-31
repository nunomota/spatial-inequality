import numpy as np

from collections import Counter

class Lookup:
    """
    This class provides several fast lookup methods for both
    optimization.entity_nodes.District and optimization.entity_nodes.School
    instances. The underlying data structures are also updated dynamically to
    minimize computational complexity of certain operations (e.g., extracting
    districts' neighborhoods from schools' neighborhoods).

    Attributes:
    __school_dict (dict of str: optimization.entity_nodes.School): Mapping
        between standardized school NCES IDs and their respective School
        instances
    __district_dict (dict of str: optimization.entity_nodes.District): Mapping
        between standardized district NCES IDs and their respective District
        instances
    __assignment_dict (dict of str: optimization.entity_nodes.District): Mapping
        between standardized school NCES IDs and the District instance they are
        assigned to
    __bordering_dict (dict of str: optimization.entity_nodes.School): Mapping
        between standardized district NCES IDs and School instances at their
        border (i.e., schools that neighbor other districts)
    __edge_tracker_matrix (numpy.ndarray): Square matrix (2-dimensional array),
        of 'districts x districts' dimensions, that contains the amount of
        existing edges between any pair of districts
    __district_id_to_edge_tracker_idx_dict (dict of str: int): Mapping between
        standardized district NCES IDs and their corresponding index in the
        __edge_tracker_matrix
    __edge_tracker_idx_to_district_id_dict (dict of int: str): Mapping between
        a district's index in the __edge_tracker_matrix and their respective
        standardized NCES ID
    __neighborhood_change_counter_dict (dict of str: int): Mapping between
        standardized district NCES IDs and the number of cumulative changes made
        in their neihborhood (i.e., number of schools redistricted)
    __all_schools_assigned (bool): Initialization flag to signal whether all
        schools have an assigned district

    Methods:
    get_school_by_id(school_id): Gets a optimization.entity_nodes.School
        instance through its standardized NCES ID.
    get_district_by_id(district_id): Gets a optimization.entity_nodes.District
        instance through its standardized NCES ID.
    get_district_by_school_id(school_id): Gets a
        optimization.entity_nodes.District instance to which a given school's
        standardized NCES ID is assigned to.
    get_bordering_schools_by_district_id(district_id): Gets the set of
        optimization.entity_nodes.School instances that belong to a district's
        border (i.e., that neighbor other districts) through its standardized
        NCES ID.
    get_neighboor_districts_by_district_id(district_id): Gets the set of
        optimization.entity_nodes.District instances that neighbor a specified
        district, through its standardized NCES ID.
    get_neighboorhood_changes_by_district_id(district_id): Gets the number of
        cumulative changes made to a district's neighborhood (i.e., number of
        schools redistricted) through its standardized NCES ID.
    assign_school_to_district_by_id(school_id, new_district_id): Assigns a
        school to a district, through their respective standardized NCES IDs. If
        there exists a previous district assignment, the school is reassigned to
        the new district.
    __handle_incomplete_district_assignment(): Checks whether all schools are
        assigned to a district and updates __all_schools_assigned accordingly.
        The first time this flag is set to 'true', this method iterates over all
        schools and districts to initialize all necessary attributes for lookup
        speedup (i.e., __edge_tracker_matrix,
        __district_id_to_edge_tracker_idx_dict,
        __edge_tracker_idx_to_district_id_dict, and
        __neighborhood_change_counter_dict).
    __is_school_in_district_border(school_id, with_district_id=None): Checks
        whether a school is at its assigned district's border. Beyond this first
        condition, this method can also check if a school is bordering a
        specific (neighboring) district.
    __update_bordering_schools_by_district_id(moved_school_id, from_district_id,
        to_district_id): Updates the set of bordering schools for two districts
        involved in a school's district reassignment.
    __update_district_neighborhoods_by_district_id(moved_school_id,
        from_district_id, to_district_id): Updates the set of neighboring
        districts for two districts involved in a school's district
        reassignment. It also updates the number of existing edges between
        involved pairs of neighbors.
    __update_neighboorhood_change_counter(from_district_id, to_district_id):
        Updates the number of cumulative changes (i.e., schools redistricted)
        for two districts involved in a school's district reassignment and their
        respective neighborhoods.
    """
    __school_dict = None
    __district_dict = None
    __assignment_dict = None
    __bordering_dict = None
    __edge_tracker_matrix = None
    __district_id_to_edge_tracker_idx_dict = None
    __edge_tracker_idx_to_district_id_dict = None
    __neighborhood_change_counter_dict = None
    __all_schools_assigned = False
    
    def __init__(self, all_schools, all_districts):
        # Schools by ID
        self.__school_dict = {
            school.get_id(): school for school in all_schools
        }
        # Districts by ID
        self.__district_dict = {
            district.get_id(): district for district in all_districts
        }
        # District by School ID
        self.__assignment_dict = {}
        # Bordering Schools by District ID
        self.__bordering_dict = {}
        # Number of edges between Districts by District idxs
        self.__edge_tracker_matrix = None
        self.__district_id_to_edge_tracker_idx_dict = {}
        self.__edge_tracker_idx_to_district_id_dict = {}
        # Number of changes made to districts or their neighborhoods
        self.__neighborhood_change_counter_dict = {}
        
    def get_school_by_id(self, school_id):
        """
        Gets a optimization.entity_nodes.School instance through its
        standardized NCES ID.

        Parameters:
        school_id (str): Standardized school NCES ID

        Returns:
        optimization.entity_nodes.School: School object instance
        """
        return self.__school_dict.get(school_id, None)
    
    def get_district_by_id(self, district_id):
        """
        Gets a optimization.entity_nodes.District instance through its
        standardized NCES ID.

        Parameters:
        district_id (str): Standardized district NCES ID

        Returns:
        optimization.entity_nodes.District: District object instance
        """
        return self.__district_dict.get(district_id, None)
    
    def get_district_by_school_id(self, school_id):
        """
        Gets a optimization.entity_nodes.District instance to which a given
        school's standardized NCES ID is assigned to.

        Parameters:
        school_id (str): Standardized school NCES ID

        Returns:
        optimization.entity_nodes.District: District object instance
        """
        return self.__assignment_dict.get(school_id, None)
    
    def get_bordering_schools_by_district_id(self, district_id):
        """
        Gets the set of optimization.entity_nodes.School instances that belong
        to a district's border (i.e., that neighbor other districts) through its
        standardized NCES ID.

        Parameters:
        district_id (str): Standardized district NCES ID

        Returns:
        set of optimization.entity_nodes.School: Set of School instances at the
            district's border

        Raises:
        ValueError: Whenever this method is called prior to finalizing school to
            district assignment
        """
        if not self.__all_schools_assigned:
            raise ValueError("Attempting to retrieve bordering schools wo/ complete district assignment...")
        return self.__bordering_dict.get(district_id, set([]))
    
    def get_neighboor_districts_by_district_id(self, district_id):
        """
        Gets the set of optimization.entity_nodes.District instances that
        neighbor a specified district, through its standardized NCES ID.

        Parameters:
        district_id (str): Standardized district NCES ID

        Returns:
        set of optimization.entity_nodes.District: Set of neighboring District
            instances

        Raises:
        ValueError: Whenever this method is called prior to finalizing school to
            district assignment
        """
        if not self.__all_schools_assigned:
            raise ValueError("Attempting to retrieve neighbor districts wo/ complete district assignment...")
        district_idx = self.__district_id_to_edge_tracker_idx_dict[district_id]
        neighbor_idxs = np.nonzero(self.__edge_tracker_matrix[district_idx])[0].tolist()
        neighbor_ids = set(map(lambda x: self.__edge_tracker_idx_to_district_id_dict[x], neighbor_idxs))
        return set(map(lambda x: self.get_district_by_id(x), neighbor_ids))
    
    def get_neighboorhood_changes_by_district_id(self, district_id):
        """
        Gets the number of cumulative changes made to a district's neighborhood
        (i.e., number of schools redistricted) through its standardized NCES ID.

        Parameters:
        district_id (str): Standardized district NCES ID

        Returns:
        int: Number of schools redistricted in District's neighborhood

        Raises:
        ValueError: Whenever this method is called prior to finalizing school to
            district assignment
        """
        if not self.__all_schools_assigned:
            raise ValueError("Attempting to retrieve neighborhood changes wo/ complete district assignment...")
        return self.__neighborhood_change_counter_dict.get(district_id, 0)
    
    def assign_school_to_district_by_id(self, school_id, new_district_id):
        """
        Assigns a school to a district, through their respective standardized
        NCES IDs. If there exists a previous district assignment, the school is
        reassigned to the new district.

        Upon a school's reassignment to a new district, intermediate results are
        computed to speedup future lookups on the involved districts: (i)
        bordering schools are adjusted; (ii) neighboring edge count is adjusted;
        (iii) cumulative changes to both neighborhoods are incremented. At this 
        stage, knowing the reassigned school's neighbors trivializes all these
        operations and ammortizes computational complexity of the overall
        algorithm.

        Parameters:
        school_id (str): Standardized target school NCES ID
        new_district_id (str): Standardized assignment district NCES ID

        Raises:
        AssertionError: Whenever a school is reassigned to a different district,
            but isn't at its current district's border
        """
        old_district = self.get_district_by_school_id(school_id)
        new_district = self.get_district_by_id(new_district_id)
        
        if self.__all_schools_assigned:
            # Change district assignment
            assert(self.__is_school_in_district_border(school_id, new_district_id))
            self.__assignment_dict[school_id] = new_district
            # Update both district's bordering schools
            self.__update_bordering_schools_by_district_id(
                school_id,
                old_district.get_id(),
                new_district.get_id()
            )
            # Update both districts' neighbor edge counts
            self.__update_district_neighborhoods_by_district_id(
                school_id,
                old_district.get_id(),
                new_district.get_id()
            )
            # Update neighboorhoods' change counter
            self.__update_neighboorhood_change_counter(
                old_district.get_id(),
                new_district.get_id()
            )
        else:
            # Make new district assignment
            self.__assignment_dict[school_id] = new_district
            self.__handle_incomplete_district_assignment()
    
    def __handle_incomplete_district_assignment(self):
        """
        Checks whether all schools are assigned to a district and updates
        __all_schools_assigned accordingly. The first time this flag is set to
        'true', this method iterates over all schools and districts to
        initialize all necessary attributes for lookup speedup (i.e.,
        __edge_tracker_matrix, __district_id_to_edge_tracker_idx_dict,
        __edge_tracker_idx_to_district_id_dict, and
        __neighborhood_change_counter_dict).
        """
        self.__all_schools_assigned = len(self.__school_dict) == len(self.__assignment_dict)
        if self.__all_schools_assigned:
            # Initialize edge tracking array (& mapping function)
            self.__district_id_to_edge_tracker_idx_dict = dict(map(
                lambda x:(x[1],x[0]),
                enumerate(self.__district_dict.keys())
            ))
            reverse_dict = lambda x: {v:k for k,v in x.items()}
            self.__edge_tracker_idx_to_district_id_dict = reverse_dict(
                self.__district_id_to_edge_tracker_idx_dict
            )
            n_districts = len(self.__district_dict)
            self.__edge_tracker_matrix = np.zeros((n_districts,n_districts))
            # Initialize bordering dict & district neighborhoods
            for district_id, district in self.__district_dict.items():
                for school in district.get_schools():
                    if self.__is_school_in_district_border(school.get_id()):
                        # Initialize bordering dict
                        cur_district_bordering = self.__bordering_dict.get(district_id, set([]))
                        cur_district_bordering.add(school)
                        self.__bordering_dict[district_id] = cur_district_bordering
            # Initialize district neighborhoods
            flatten = lambda l: [item for sublist in l for item in sublist]
            for district_id, district in self.__district_dict.items():
                all_school_neighbors = flatten(list(map(
                    lambda x: list(x.get_neighbors()),
                    district.get_schools()
                )))
                edge_count_by_district_id = Counter(map(
                    lambda x: self.get_district_by_school_id(x.get_id()).get_id(),
                    all_school_neighbors
                ))
                district_idx = self.__district_id_to_edge_tracker_idx_dict[district_id]
                for neighbor_district_id, edge_count in edge_count_by_district_id.items():
                    if district_id == neighbor_district_id:
                        continue
                    neighbor_district_idx = self.__district_id_to_edge_tracker_idx_dict[neighbor_district_id]
                    self.__edge_tracker_matrix[district_idx,neighbor_district_idx] = edge_count
                    self.__edge_tracker_matrix[neighbor_district_idx,district_idx] = edge_count
    
    def __is_school_in_district_border(self, school_id, with_district_id=None):
        """
        Checks whether a school is at its assigned district's border. Beyond
        this first condition, this method can also check if a school is
        bordering a specific (neighboring) district.

        Parameters:
        school_id (str): Standardized target school NCES ID
        with_district_id (str): Standardized neighboring district NCES ID, or
            None

        Returns:
        bool: 'true' if the school is at its assigned district's border (and,
        optionally, if it neighbors a specific district), 'false' otherwise
        """
        school = self.get_school_by_id(school_id)
        district = self.get_district_by_school_id(school_id)
        for neighbor in school.get_neighbors():
            neighbor_district = self.get_district_by_school_id(neighbor.get_id())
            if neighbor_district.get_id() != district.get_id():
                if with_district_id is None:
                    return True
                elif with_district_id == neighbor_district.get_id():
                    return True
                else:
                    continue
        return False

    def __update_bordering_schools_by_district_id(self, moved_school_id, from_district_id, to_district_id):
        """
        Updates the set of bordering schools for two districts involved in a
        school's district reassignment.

        Parameters:
        moved_school_id (str): Standardized target school NCES ID
        from_district_id (str): Standardized source district NCES ID
        to_district_id (str): Standardized destination district NCES ID
        """
        moved_school = self.get_school_by_id(moved_school_id)
        from_district = self.get_district_by_id(from_district_id)
        to_district = self.get_district_by_id(to_district_id)
        
        # Remove moved school from the "bordering schools set" of its previous district
        from_district_brodering_schools = self.__bordering_dict.get(from_district_id, set([]))
        from_district_brodering_schools.discard(moved_school)
        self.__bordering_dict[from_district_id] = from_district_brodering_schools
        # Update all moved schools' neighbors (includig itself)
        for neighbor in [*moved_school.get_neighbors(), moved_school]:
            neighbor_district_id = self.get_district_by_school_id(neighbor.get_id()).get_id()
            neighbor_is_from_relevant_district = (
                (neighbor_district_id == from_district_id) or 
                (neighbor_district_id == to_district_id)
            )
            if neighbor_is_from_relevant_district:
                current_bordering_schools = self.__bordering_dict.get(neighbor_district_id, set([]))
                if self.__is_school_in_district_border(neighbor.get_id()):
                    current_bordering_schools.add(neighbor)
                else:
                    current_bordering_schools.discard(neighbor)
                self.__bordering_dict[neighbor_district_id] = current_bordering_schools
                
    def __update_district_neighborhoods_by_district_id(self, moved_school_id, from_district_id, to_district_id):
        """
        Updates the set of neighboring districts for two districts involved in a
        school's district reassignment. It also updates the number of existing
        edges between involved pairs of neighbors.

        Parameters:
        moved_school_id (str): Standardized target school NCES ID
        from_district_id (str): Standardized source district NCES ID
        to_district_id (str): Standardized destination district NCES ID
        """
        # Get number of edges between moved school and its neighbors' districts
        moved_school = self.get_school_by_id(moved_school_id)
        neighbor_district_ids = list(map(
            lambda x: self.get_district_by_school_id(x.get_id()).get_id(),
            moved_school.get_neighbors()
        ))
        # Get matrix idxs for all district ids
        from_district_idx = self.__district_id_to_edge_tracker_idx_dict[from_district_id]
        to_district_idx = self.__district_id_to_edge_tracker_idx_dict[to_district_id]
        # Update edge tracker matrix
        for neighbor_district_id, edge_count in Counter(neighbor_district_ids).items():
            neighbor_district_idx = self.__district_id_to_edge_tracker_idx_dict[neighbor_district_id]
            # Update edges existing between "from" and "to"
            if neighbor_district_id == from_district_id:
                self.__edge_tracker_matrix[from_district_idx,to_district_idx] += edge_count
                self.__edge_tracker_matrix[to_district_idx,from_district_idx] += edge_count
            elif neighbor_district_id == to_district_id:
                self.__edge_tracker_matrix[from_district_idx,to_district_idx] -= edge_count
                self.__edge_tracker_matrix[to_district_idx,from_district_idx] -= edge_count
            # Update edges existing between "to" and other districts
            else:
                # Remove edges that existed between "from" and neighbor
                self.__edge_tracker_matrix[from_district_idx,neighbor_district_idx] -= edge_count
                self.__edge_tracker_matrix[neighbor_district_idx,from_district_idx] -= edge_count
                # Add new edges created between "to" and neighbor
                self.__edge_tracker_matrix[to_district_idx,neighbor_district_idx] += edge_count
                self.__edge_tracker_matrix[neighbor_district_idx,to_district_idx] += edge_count
                
    def __update_neighboorhood_change_counter(self, from_district_id, to_district_id):
        """
        Updates the number of cumulative changes (i.e., schools redistricted)
        for two districts involved in a school's district reassignment and their
        respective neighborhoods.

        Parameters:
        from_district_id (str): Standardized source district NCES ID
        to_district_id (str): Standardized destination district NCES ID
        """
        # Auxiliary method for single counter increments
        def inc_counter(district_id):
            cur_counter = self.__neighborhood_change_counter_dict.get(district_id, 0)
            self.__neighborhood_change_counter_dict[district_id] = cur_counter + 1
        # Get immediate neighbor districts for "from" and "to" districts
        from_district_neighborhood = self.get_neighboor_districts_by_district_id(from_district_id)
        to_district_neighborhood = self.get_neighboor_districts_by_district_id(to_district_id)
        immediate_neighborhood = set([from_district_id, to_district_id]).union(
            from_district_neighborhood,
            to_district_neighborhood
        )
        # Update change counter for "from" and "to" districts directly
        for district_id in immediate_neighborhood:
            inc_counter(district_id)