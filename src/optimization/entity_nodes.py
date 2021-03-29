class School:
    """
    Class to represent and single public school in the US and all of its
    necessary properties.

    Attributes:
    __nces_id (str): Standardized NCES ID
    __total_students (int): Total number of students
    __total_funding (float): Total funding available
    __neighbors (set): Set of all neighboring Schools

    Methods:
    get_id(): Getter method for school's NCES ID.
    get_total_students(): Getter method for school's total number of students.
    get_total_funding(): Getter method for school's total funding.
    get_neighbors(): Getter method for school's neighbors.
    add_neighbor(): Adds new neighboring school to currently registered
        neighbors.
    """
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
        """
        Getter method for school's NCES ID.

        Returns:
        str: Standardized NCES ID (should never be nullable)
        """
        return self.__nces_id
    
    def get_total_students(self):
        """
        Getter method for school's total number of students.

        Returns:
        int: Total number of students (should never be nullable)
        """
        return self.__total_students
    
    def get_total_funding(self):
        """
        Getter method for school's total funding.

        Returns:
        float: Total funding available (should never be nullable)
        """
        return self.__total_funding
    
    def get_neighbors(self):
        """
        Getter method for school's neighbors.

        Returns:
        set: All NCES IDs for neighboring schools (returns an empty set in case
            there are none)
        """
        return self.__neighbors
        
    def add_neighbor(self, school):
        """
        Adds new neighboring school to currently registered neighbors.

        Parameters:
        school(School): New neighboring school
        """
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
        """
        Performs a shallow copy of the School object (i.e., references to
        neighboring schools are kept).

        Returns:
        School: Shallow copy of School object
        """
        copy = School(self._nces__id, self.__total_sudents, self.__total_funding)
        for neighbor in self.__neighbors:
            copy.add_neighbor(neighbor)
        return copy
    
    def __deepcopy__(self):
        """
        Performs a deep copy of the School object (i.e., all neighbors'
        references are resolved and their shallow copies are added to the new
        neighborhood instead).

        Returns:
        School: Deep copy of School object
        """
        copy = School(self._nces__id, self.__total_sudents, self.__total_funding)
        for neighbor in self.__neighbors:
            copy.add_neighbor(copy.copy(neighbor))
        return copy
    
class District:
    """
    Class to represent and single public school in the US and all of its
    necessary properties.

    Attributes:
    __nces_id (str): Standardized NCES ID
    __total_students (int): Total number of students
    __total_funding (float): Total funding available
    __schools (set): Set of all assigned Schools

    Methods:
    get_id(): Getter method for district's NCES ID.
    get_total_students(): Getter method for district's total number of students.
    get_total_funding(): Getter method for district's total funding.
    get_schools(): Getter method for district's assigned schools.
    add_school(): Adds a new School to the district and updates district's total
        students and funding.
    remove_school(): Removes a School assigned to the district and updates
        district's total students and funding.
    """
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
        """
        Getter method for district's NCES ID.

        Returns:
        str: Standardized NCES ID (should never be nullable)
        """
        return self.__nces_id
    
    def get_total_students(self):
        """
        Getter method for district's total number of students.

        Returns:
        int: Total number of students (should never be nullable)
        """
        return self.__total_students
    
    def get_total_funding(self):
        """
        Getter method for district's total funding.

        Returns:
        float: Total funding available (should never be nullable)
        """
        return self.__total_funding
    
    def get_schools(self):
        """
        Getter method for all Schools in the district.

        Returns:
        set: Set of unique School objects assigned to the district
        """
        return self.__schools
    
    def add_school(self, school):
        """
        Adds a new School to the district and updates district's total students
        and funding.

        Parameters:
        school (School): New school to add
        """
        # TODO avoid error propagation
        self.__total_students += school.get_total_students()
        self.__total_funding += school.get_total_funding()
        self.__schools.add(school)
    
    def remove_school(self, school):
        """
        Removes a School assigned to the district and updates district's total
        students and funding.

        Parameters:
        school (School): Old school to remove
        """
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
        """
        Performs a shallow copy of the District object (i.e., references to
        assigned schools are kept).

        Returns:
        District: Shallow copy of District object
        """
        copy = District(self.__nces_id)
        for school in self.__schools:
            copy.add_school(school)
        return copy
    
    def __deepcopy__(self):
        """
        Performs a deep copy of the District object (i.e., all schools'
        references are resolved and their shallow copies are added to the new
        neighborhood instead).

        Returns:
        District: Deep copy of District object
        """
        copy = District(self.__nces_id)
        for school in self.__schools:
            copy.add_school(copy.copy(school))
        return copy