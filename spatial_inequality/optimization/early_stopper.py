"""
Implements an "early stopping" termination criterion for our algorithm,
preventing unnecesary computations when improvements are no longer observed.
"""
import numpy as np

class EarlyStopper:
    """
    Class to handle preemptive stopping of an algorithm when no measurable
    improvement has been registered for a given amount of iterations.

    Attributes:
        __n_iterations (int): Number of allowed iterations without improvement.
        __tolerance (float): Tolerance for floating point measurement
            comparison.
        __absolute_min (float): Minimum value registered over all iterations.
        __n_iterations_wo_improvement (int): Current number of iterations with
            no observed improvement.
    """
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
        """
        Records a new value for the tracked metric and updates all variables
        accordingly.

        Args:
            value (float): Updated value for tracked metric.

        Raises:
            StopIteration: Whenever more than the specified maximum amount of
                iterations has elapsed wihtout a measurable improvement to the
                tracked metric.
        """
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