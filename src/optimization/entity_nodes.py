class School:
    
    __nces_id = None
    __total_sudents = None
    __total_funding = None
    __neighbors = None
    
    def __init__(self, nces_id, total_students, total_funding):
        self.__nces_id = nces_id
        self.__total_students = total_students
        self.__total_funding = total_funding
        self.__neighbors = set([])
        
    def get_id(self):
        return self.__nces_id
    
    def get_total_students(self):
        return self.__total_students
    
    def get_total_funding(self):
        return self.__total_funding
    
    def get_neighbors(self):
        return self.__neighbors
        
    def add_neighbor(self, school):
        self.__neighbors.add(school)
        
    def __str__(self):
        return "< ID: '{}' | Neigh.: {} | Students: {} | Funding: {:.02f} >".format(
            self.get_id(),
            len(self.get_neighbors()),
            self.get_total_students(),
            self.get_total_funding()
        )
    
    def __repr__(self):
        return str(self)
    
    def __copy__(self):
        copy = School(self._nces__id, self.__total_sudents, self.__total_funding)
        for neighbor in self.__neighbors:
            copy.add_neighbor(neighbor)
        return copy
    
    def __deepcopy__(self):
        copy = School(self._nces__id, self.__total_sudents, self.__total_funding)
        for neighbor in self.__neighbors:
            copy.add_neighbor(copy.copy(neighbor))
        return copy
    
class District:
    
    __nces_id = None
    __total_students = None
    __total_funding = None
    __schools = None
    
    def __init__(self, nces_id):
        self.__nces_id = nces_id
        self.__total_students = 0
        self.__total_funding = 0
        self.__schools = set([])
        
    def get_id(self):
        return self.__nces_id
    
    def get_total_students(self):
        return self.__total_students
    
    def get_total_funding(self):
        return self.__total_funding
    
    def get_schools(self):
        return self.__schools
    
    def add_school(self, school):
        # TODO avoid error propagation
        self.__total_students += school.get_total_students()
        self.__total_funding += school.get_total_funding()
        self.__schools.add(school)
    
    def remove_school(self, school):
        # TODO avoid error propagation
        self.__total_students -= school.get_total_students()
        self.__total_funding -= school.get_total_funding()
        self.__schools.discard(school)
        
    def __str__(self):
        return "< ID: '{}' | Schools: {} | Students: {} | Funding: {:.01f} >".format(
            self.get_id(),
            len(self.get_schools()),
            self.get_total_students(),
            self.get_total_funding()
        )
    
    def __repr__(self):
        return str(self)
    
    def __copy__(self):
        copy = District(self.__nces_id)
        for school in self.__schools:
            copy.add_school(school)
        return copy
    
    def __deepcopy__(self):
        copy = District(self.__nces_id)
        for school in self.__schools:
            copy.add_school(copy.copy(school))
        return copy