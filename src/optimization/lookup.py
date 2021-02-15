import numpy as np

from collections import Counter

class Lookup:
    
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
        return self.__school_dict.get(school_id, None)
    
    def get_district_by_id(self, district_id):
        return self.__district_dict.get(district_id, None)
    
    def get_district_by_school_id(self, school_id):
        return self.__assignment_dict.get(school_id, None)
    
    def get_bordering_schools_by_district_id(self, district_id):
        if not self.__all_schools_assigned:
            raise ValueError("Attempting to retrieve bordering schools wo/ complete district assignment...")
        return self.__bordering_dict.get(district_id, set([]))
    
    def get_neighboor_districts_by_district_id(self, district_id):
        if not self.__all_schools_assigned:
            raise ValueError("Attempting to retrieve neighbor districts wo/ complete district assignment...")
        district_idx = self.__district_id_to_edge_tracker_idx_dict[district_id]
        neighbor_idxs = np.nonzero(self.__edge_tracker_matrix[district_idx])[0].tolist()
        neighbor_ids = set(map(lambda x: self.__edge_tracker_idx_to_district_id_dict[x], neighbor_idxs))
        return set(map(lambda x: self.get_district_by_id(x), neighbor_ids))
    
    def get_neighboorhood_changes_by_district_id(self, district_id):
        if not self.__all_schools_assigned:
            raise ValueError("Attempting to retrieve neighborhood changes wo/ complete district assignment...")
        return self.__neighborhood_change_counter_dict.get(district_id, 0)
    
    def assign_school_to_district_by_id(self, school_id, new_district_id):
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