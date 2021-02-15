from itertools import combinations

def gini_index(benefit_vector):
    """
    Calculate the gini index for a benefit distribution
    with N elements, according to the (latex) definition:
    
    \frac{
        \sum_{j=1}^{N} \sum_{i=1}^{N} \left| y_i - y_j \right|
    }{
        2 N \sum_{i=1}^{N} y_i
    }
    
    Parameters:
    benefit_vector (list): List of float values, containing
        a benefit (or wealth) for multiple parties in a
        population
        
    Returns:
    float: Gini index associated with a given benefit vector
    """
    assert(isinstance(benefit_vector, list))
    N = len(benefit_vector)
    abs_diff = lambda pair: abs(benefit_vector[pair[0]] - benefit_vector[pair[1]])
    numerator = sum(map(abs_diff, combinations(range(N), r=2)))
    denominator = 2 * N * sum(benefit_vector)
    return numerator / denominator
    
def spatial_index(benefit_vector, get_neighbours):
    """
    Calculate spatial inequality for a benefit distribution
    with N elements, according to the (latex) definition:
    
    \frac{
        \sum_{i=1}^{N} \frac{1}{N_i} \sum_{j=1}^{N_i} \left| y_i - y_j \right|
    }{
        \sum_{i=1}^{N} y_i
    }
    
    As opposed to the Gini Index, this definition only iterates
    over elements that are considered 'neighbours' (and not
    every possible pair).
    
    Parameters:
    benefit_vector (list): List of float values, containing
        a benefit (or wealth) for multiple parties in a
        population
    get_neighbours (func): Function that receives a
        single district's index as a parameter (from
        0 to N-1) and returns a list of indices of its
        neighbouring districts (each from 0 to N-1)
        
    Returns:
    float: Spatial inequality associated with a given benefit
        vector
    """
    assert(isinstance(benefit_vector, list) and callable(get_neighbours))
    N = len(benefit_vector)
    abs_diff = lambda pair: abs(benefit_vector[pair[0]] - benefit_vector[pair[1]])
    numerator = 0
    individual_ineqs = []
    for i in range(N):
        neighbours = get_neighbours(i)
        Ni = len(neighbours)
        individual_ineq = sum([abs_diff((i, j)) for j in neighbours]) / Ni
        individual_ineqs.append(individual_ineq)
    overall_ineq = sum(individual_ineqs) / sum(benefit_vector)
    return overall_ineq, individual_ineqs