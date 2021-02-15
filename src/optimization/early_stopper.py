import numpy as np

class EarlyStopper:
    
    __n_iterations = None
    __tolerance = None
    
    __absolute_min = None
    __n_iterations_wo_improvement = None
    
    def __init__(self, n_iterations, tolerance=0.1):
        self.__n_iterations = n_iterations
        self.__tolerance = tolerance

        self.__absolute_min = None
        self.__n_iterations_wo_improvement = 0
        
    def update(self, value):
        if self.__absolute_min is None:
            self.__absolute_min = value
        else:
            is_close = np.isclose(value, self.__absolute_min, atol=self.__tolerance)
            is_greater = value > self.__absolute_min
            if is_close or is_greater:
                # No detected improvement
                self.__n_iterations_wo_improvement += 1
            else:
                # Improvement detected
                self.__absolute_min = value
                self.__n_iterations_wo_improvement = 0
        if self.__n_iterations_wo_improvement >= self.__n_iterations:
            raise StopIteration