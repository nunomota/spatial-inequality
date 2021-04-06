"""
Greedy implementation of our school redistricting algorithm (i.e.,
`Greedy Partitioning`).
"""
import os
import logging
import numpy as np

from time import time
from datetime import datetime, timedelta

from auxiliary.functions import *

from optimization.early_stopper import EarlyStopper
from optimization.entity_nodes import District, School
from optimization.holdout import HoldoutQueue
from optimization.lazy_heap import LazyHeap
from optimization.lookup import Lookup
from optimization.run_metrics import RunMetrics

# Initialize logger
if not os.path.exists('../logs'):
    os.makedirs('../logs')
logging.basicConfig(filename='../logs/debug.log', level=logging.INFO)

def greedily_pick_redistricting_moves(district, lookup, min_schools_per_district, max_schools_per_district):
    """
    Greedily calculates all schools that should be redistricted from a selected
    district to one of its neighbors, such that the whole neighborhood's
    inequality is reduced.

    To do this, this function arbitrarily iterates over all schools at the
    selected district's border (with its neighboring districts) and evaluates
    whether a given move would be a good (local) move or not. It does this by:
    (i) 'virtually' redistricting the school to another potential district; and
    (ii) comparing both districts' per-student funding after this move was made.
    If funding is closer between the districts, the move is registered and the
    overall iteration process proceeds. Otherwise, the move is reverted before
    proceeding.

    Args:
        district (optimization.entity_nodes.District): Target District to redistrict
            schools from.
        lookup (optimization.lookup.Lookup): Lookup instance for fast information
            querying.
        min_schools_per_district (int): Minimum number of schools to preserve in
            each district, upon redistricting. A number equal to (or lesser than)
            zero will allow districts to merge.
        max_schools_per_district (int): Maximum number of schools to be preserved in
            each district, upon redistricting.

    Returns:
        list of tuple: List of all greedy School redistricting moves that would
            reduce the selected District neighborhood's inequality (i.e., tuples
            comprised of a redistricted school's standardized NCES ID, its source
            district's standardized NCES ID and its destination district's
            standardized NCES ID).
    """
    # Auxiliary functions to make/revert virtual moves
    def make_move(school, from_district, to_district):
        from_district["total_funding"] -= school.get_total_funding()
        from_district["total_students"] -= school.get_total_students()
        from_district["n_schools"] -= 1
        to_district["total_funding"] += school.get_total_funding()
        to_district["total_students"] += school.get_total_students()
        to_district["n_schools"] += 1
    def revert_move(school, from_district, to_district):
        make_move(school, to_district, from_district)
    # Auxiliary function to test if move is good
    def is_good_greedy_move(school, from_district, to_district):
        # Auxiliary functions
        funding_per_student = lambda x: x["total_funding"] / x["total_students"]
        funding_per_student_abs_diff = lambda x,y: abs(funding_per_student(x) - funding_per_student(y))
        # Check if number of schools is allowed
        if from_district["n_schools"] <= min_schools_per_district or to_district["n_schools"] >= max_schools_per_district:
            return False
        # Handle case where no schools would remain in district
        if from_district["n_schools"] == 1:
            return True
        # Calculate stats before/after move
        abs_funding_diff_before = funding_per_student_abs_diff(from_district, to_district)
        make_move(school, from_district, to_district)
        abs_funding_diff_after = funding_per_student_abs_diff(from_district, to_district)
        revert_move(school, from_district, to_district)
        # Return result
        return abs_funding_diff_after < abs_funding_diff_before

    # Create auxiliary data structures for (fast) move simulation
    neighboring_districts = lookup.get_neighboor_districts_by_district_id(district.get_id())
    acc_local_values = {
        district.get_id(): {
            "n_schools": len(district.get_schools()),
            "total_students": district.get_total_students(),
            "total_funding": district.get_total_funding()
        } for district in [*neighboring_districts, district]
    }
    # Calculate greedy moves
    greedy_moves = []
    bordering_schools = lookup.get_bordering_schools_by_district_id(district.get_id())
    for school in bordering_schools:
        for neighbor in school.get_neighbors():
            connected_district = lookup.get_district_by_school_id(neighbor.get_id())
            if connected_district.get_id() == district.get_id():
                continue
            elif not is_good_greedy_move(
                    school,
                    acc_local_values[district.get_id()],
                    acc_local_values[connected_district.get_id()]):
                continue
            else:
                # Register move in local accumulators
                make_move(
                    school,
                    acc_local_values[district.get_id()],
                    acc_local_values[connected_district.get_id()]
                )
                # Add new move to move list
                greedy_moves.append((
                    school.get_id(),
                    district.get_id(),
                    connected_district.get_id()
                ))
                # Prevent school multiple assignment
                break
    return greedy_moves

def apply_redistricting_moves(moves, lookup, heap):
    """
    Performs all registered greedy moves and updates both
    optimization.lookup.Lookup and otimization.lazy_heap.LazyHeap instances
    according to the new school/district assignments.

    NOTE: Since some of the districts involved in the registered moves may have
    been moved to the holdout queue, updating the lazy heap may raise a KeyError
    exception. In this case, it's safe to skip this step as it will not
    interfere with the heap's order.

    Args:
        moves (list of tuple): Greedy moves to apply.
        lookup (optimization.lookup.Lookup): Lookup instance for fast
            information querying.
        heap (otimization.lazy_heap.LazyHeap): LazyHeap of districts to update.
    """
    for move in moves:
        # Get all necessary instances
        school = lookup.get_school_by_id(move[0])
        from_district = lookup.get_district_by_id(move[1])
        to_district = lookup.get_district_by_id(move[2])
        # Update "from" and "to" districts (& update lookup)
        logging.debug(f"Moving school '{school.get_id()}': '{from_district.get_id()}' > '{to_district.get_id()}'")
        from_district.remove_school(school)
        to_district.add_school(school)
        lookup.assign_school_to_district_by_id(school.get_id(), to_district.get_id())
        # Try to update heap (elements may be in holdout queue)
        def attempt_heap_update(district):
            try:
                heap.update(district)
            except KeyError:
                pass
        attempt_heap_update(from_district)
        attempt_heap_update(to_district)

def calculate_inequality(districts, lookup):
    """
    Calculate spatial inequality based on a school/district assignment and
    defined districts' neighborhoods, following the (latex) definition:

    \\[
    \\frac{
        \\sum_{j=1}^{N} \\sum_{i=1}^{N} \\left| y_i - y_j \\right|
    }{
        2 N \\sum_{i=1}^{N} y_i
    }
    \\]

    Args:
        districts (list of optimization.entity_nodes.District): List of all
            District instances.
        lookup (optimization.lookup.Lookup): Lookup instance for fast
            information querying.

    Returns:
        float: Spatial inequality for a school/district assignment.
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

def refill_heap(heap, holdout_queue):
    """
    Refills `optimization.lazy_heap.LazyHeap` with any Districts successfully
    dequeued from `optimization.holdout.HoldoutQueue`.

    Args:
        heap (optimization.lazy_heap.LazyHeap): LazyHeap instance to refill
            using Districts from the holdout queue.
        holdout_queue (optimization.holdout.HoldoutQueue): HoldoutQueue instance
            containing all districts previously exhausted greedy moves.
    """
    # Pop all elements from holdout queue
    is_running = True
    while is_running is True:
        holdout_district = holdout_queue.dequeue()
        # Holdout queue is empty
        if holdout_district is None:
            logging.info("No more districts in holdout queue.")
            holdout_queue.recycle()
            logging.info("Recycling holdout queue.")
            is_running = False
        # Holdout queue had a valid district
        else:
            logging.info("Pushing district into heap.")
            heap.push(holdout_district)
            logging.debug(f"Pushed district '{holdout_district.get_id()}' into heap.")  

def greedy_algo(target_state, aug_school_info, school_assignment, min_schools_per_district, max_schools_per_district, early_stopper_it, early_stopper_tol, callbacks):
    """
    Applies the greedy partitioning algorithm to a given school/district
    assignment - for a specific state - and attempts to minimize its spatial
    inequality by redistricting schools.

    Args:
        target_state (str): Capitalized full state name (e.g., 'Alabama').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
        min_schools_per_district (int): Minimum number of schools to preserve in
            each district, upon redistricting. A number equal to (or lesser
            than) zero will allow districts to merge.
        max_schools_per_district (int): Maximum number of schools to be
            preserved in each district, upon redistricting.
        early_stopper_it (int): Number of allowed iterations without improvement
            for early stopping.
        early_stopper_tol (float): Tolerance for floating point inequality
            improvement measurement.
        callbacks (dict): Dictionary of (optional) callback functions that will
            be called - by key - at specific stages of the algorithm's
            execution. 'on_init' will be called once, right after variables'
            initialization and before any computation takes place. 'on_update'
            will be called at the beginning of every iteration of the algorithm.
            'on_end' will be called once, right before the algorithm terminates
            its execution and after all computations are done. 'on_move' will be
            called whenever greedy school redistricting moves are made, right
            after they are applied. Each callback will then be passed
            corresponding arguments, regarding the status of execution. More
            specifically, 'on_init', 'on_update', and 'on_end' will have access
            to (i) the list of all `optimization.entity_nodes.School` instances,
            (ii) the list of all `optimization.entity_nodes.District` instances,
            and (iii) an updated `optimization.lookup.Lookup` instance. On the
            other hand, 'on_move' will only be passed (i) the current
            iteration's index, and (ii) the list of all moves that were
            performed.

    Returns:
        float: Minimal spatial inequality index achieved for the specified
            state.
    """
    # Instantiate all schools
    school_ids_in_state = get_schools_in_state(target_state, school_assignment)
    schools = [School(
        school_id,
        get_school_total_students(school_id, aug_school_info),
        get_school_total_funding(school_id, aug_school_info)
    ) for school_id in school_ids_in_state]

    # Instantiate all districts
    district_ids_in_state = get_districts_in_state(target_state, school_assignment)
    districts = [District(
        district_id
    ) for district_id in district_ids_in_state]

    # Instantiate lookup
    lookup = Lookup(schools, districts)

    # Populate schools' neighbors
    for school in schools:
        school_id = school.get_id()
        neighbor_ids = get_neighbouring_schools(school_id, aug_school_info)
        for neighbor_id in neighbor_ids:
            neighbor = lookup.get_school_by_id(neighbor_id)
            school.add_neighbor(neighbor)

    # Populate school districts
    for district in districts:
        district_id = district.get_id()
        school_ids = get_schools_in_district(district_id, school_assignment)
        for school_id in school_ids:
            school = lookup.get_school_by_id(school_id)
            district.add_school(school)
            lookup.assign_school_to_district_by_id(school_id, district_id)

    # Calculate state-wide funding per student
    state_total_students = 0
    state_total_funding = 0
    for district in districts:
        state_total_students += district.get_total_students()
        try:
            int(district.get_total_funding())
        except Exception as exception:
            print(district)
        state_total_funding += district.get_total_funding()
    state_funding_per_student = state_total_funding / state_total_students

    # Auxiliary function for funding calculation
    def abs_diff_from_state(district):
        district_funding_per_student = district.get_total_funding() / district.get_total_students()
        return abs(district_funding_per_student - state_funding_per_student)

    # Initialize (max) heap to extract districts that deviate from state average
    heap = LazyHeap(
        item_id=lambda x: x.get_id(),
        gt=lambda x,y: abs_diff_from_state(x) > abs_diff_from_state(y),
        max_elems=2*len(districts)
    )

    # Populate heap with all districts
    for district in districts:
        heap.push(district)

    # Initalize holdout queue
    holdout_queue = HoldoutQueue(
        get_item_tag=lambda x: lookup.get_neighboorhood_changes_by_district_id(x.get_id()),
        is_valid=lambda x: lookup.get_neighboorhood_changes_by_district_id(x.get_data().get_id()) > x.get_tag()
    )
    
    # Auxiliary function to execute provided callbacks
    def execute_callback(label, **kwargs):
        callback = callbacks.get(label, None)
        if callback is None:
            pass
        else:
            callback(**kwargs)
    
    # Main algorithm
    is_running = True
    is_retrying = False
    iteration_idx = 0
    
    # Initialize EarlyStopper
    early_stopper = EarlyStopper(
        early_stopper_it,
        tolerance=early_stopper_tol
    )
    # Initialize greedy parameters
    greedy_params = {
        "min_schools_per_district": min_schools_per_district,
        "max_schools_per_district": max_schools_per_district
    }
    
    # Execute on_init callback
    execute_callback(
        "on_init",
        schools=schools,
        districts=districts,
        lookup=lookup
    )
    
    # Start greedy algorithm
    logging.info("Starting greedy algorithm.")
    while is_running is True:
        # To always execute at start of iteration
        logging.info("-"*30)
        iteration_idx += 1
        
        # Execute on_update callback
        execute_callback(
            "on_update",
            schools=schools,
            districts=districts,
            lookup=lookup
        )
        
        try:
            # Try to pop district from queue
            logging.info("Popping district from heap.")
            district = heap.pop()
            logging.debug(f"District popped: '{district.get_id()}'")
            # Reset retry flag
            is_retrying = False
            # Greedily select districts with which to equalize funding
            logging.info("Calculating greedy moves.")
            greedy_moves = greedily_pick_redistricting_moves(district, lookup, **greedy_params)
            logging.debug(f"Number of possible moves: {len(greedy_moves)}")
            logging.debug(f"Possible moves' list: {greedy_moves}")
            # Handle all existing greedy moves
            if len(greedy_moves) == 0:
                logging.info("No moves available.")
                # No moves are available, add district to holdout queue
                logging.info("Moving district to holdout queue.")
                holdout_queue.enqueue(district)
                logging.debug(f"Moved district '{district.get_id()}' to holdout queue.")
            else:
                logging.info("At least one available move.")
                # If some moves are available, perform all
                logging.info("Redistricting schools.")
                apply_redistricting_moves(greedy_moves, lookup, heap)
                execute_callback("on_move", iteration_idx=iteration_idx, moves=greedy_moves)
                # Push district back into heap (or eliminate it if it has no more schools)
                if len(district.get_schools()) > 0:
                    logging.info("Pushing district back into heap.")
                    heap.push(district)
                    logging.debug(f"Pushed district '{district.get_id()}' to heap.")
                else:
                    logging.info("Disposing of district.")
                    districts.remove(district)
                    logging.debug(f"Disposed of district '{district.get_id()}'")
                # Update inequality calculation
                current_inequality = calculate_inequality(districts, lookup)
                logging.info(f"Current inequality: {current_inequality}")
                early_stopper.update(current_inequality)
        except IndexError:
            logging.info("Could not pop district from heap.")
            # First time retrying, attempt to refill heap (and retry algorithm)
            if is_retrying is False:
                logging.info("Flushing holdout queue into heap.")
                refill_heap(heap, holdout_queue)
                logging.info("Retrying algorithm.")
                is_retrying = True
            # The heap has no elements even after refill, stop algorithm
            else:
                logging.info("No available districts after retry... Terminating.")
                is_running = False
        except StopIteration:
            # EarlyStopper has not detected any inequality improvement
            logging.info("No improvement detected for overall inequality.")
            is_running = False
    logging.info("Greedy algorithm done.") 
    # Execute on_end callback
    execute_callback(
        "on_end",
        schools=schools,
        districts=districts,
        lookup=lookup
    )
    # retun final inequality value
    return calculate_inequality(districts, lookup)

def get_expectable_run_for_state(target_state, aug_school_info, school_assignment, n_runs, greedy_params, early_stopper_params):
    """
    Performs multiple runs of the greedy partitioning algorithm for a given
    state, to get an 'expectation' of its performance and measure uncertainty
    associated with the spatial inequality index's minimization process. It then
    extracts a single 'expectable' run (alongside benchmarking statistics) and
    returns them.

    NOTE: Parallelizing iterations over the same state would be possible to
    speedup this benchmarking process.

    Args:
        target_state (str): Capitalized full state name (e.g., 'Alabama').
        aug_school_info (pandas.DataFrame): Target augmented school information
            (as formatted by `auxiliary.data_handler.DataHandler`).
        school_assignment (pandas.DataFrame): Target school assignment (as
            formatted by `auxiliary.data_handler.DataHandler`).
        n_runs (int): Number of runs to perform for the greedy partitioning
            algorithm.
        greedy_params (kwargs): Keyword arguments for the greedy partitioning
            algorithm's parameterization. Two values can be specified through
            this parameter, namely (i) 'min_schools_per_district' and (ii)
            'max_schools_per_district'. These respectively refer to the minimum
            and maximum number of schools to preserve in each district, upon
            redistricting.
        early_stopper_params (kwargs): Keyword arguments for the early stopper's
            parameterization. Two values can be specified through this
            parameter, namely (i) 'early_stopper_it' and (ii)
            'early_stopper_tol'. These respectively refer to the number of
            maximum iterations allowed without noticeable improvements to
            inequality and the tolerance for floating point comparisons on
            inequality.

    Returns:
        tuple: Triplet containing (i) the spatial inequality index's standard
            deviation, (ii) the spatial inequality index's mean, and (iii) an
            `optimization.run_metrics.RunMetrics` instance with all information
            on the algorithm's average run (i.e., the run whose spatial
            inequality index came closest to the average).
    """
    # Initialize container variables
    inequalities = []
    metrics = []
    # Progress-related
    start_time = datetime.now()
    start_timestamp = time()
    for i in range(n_runs):
        # Print progress
        try:
            total_time_estimate = lambda: n_runs * ((time() - start_timestamp) / i)
            eta = (start_time + timedelta(seconds=total_time_estimate())).strftime("%Y-%m-%d %H:%M:%S")
            print(f"State: {target_state}\nProgress: {i+1}/{n_runs}\nETA: {eta}")
        except Exception:
            print(f"State: {target_state}\nProgress: {i+1}/{n_runs}\nETA: ???")
        # Initialize metrics
        cur_metrics = RunMetrics()
        callbacks = {
            "on_init": cur_metrics.on_init,
            "on_update": cur_metrics.on_update,
            "on_move": cur_metrics.on_move,
            "on_end": cur_metrics.on_end
        }
        # Single algorithm run
        cur_inequality = greedy_algo(
            target_state,
            aug_school_info,
            school_assignment,
            **greedy_params,
            **early_stopper_params,
            callbacks=callbacks
        )
        # Add to lists & clear screen
        metrics.append(cur_metrics)
        inequalities.append(cur_inequality)
    # Clear print with status
    print(f"State: {target_state}\nProgress: Done!")
    # Select expectable run
    avg_inequality = np.mean(inequalities)
    average_metric_idx = next(
        idx for idx in np.argsort(inequalities) if inequalities[idx] >= avg_inequality
    )
    # Return mean, standard deviation and a representative metric
    return np.mean(inequalities), np.std(inequalities), metrics[average_metric_idx]