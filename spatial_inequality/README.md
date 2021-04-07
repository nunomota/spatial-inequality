# Temporal complexity

In this page we detail the public schools' redistricting algorithm, and take a look at its temporal complexity. Moreover, we specifically detail and discuss some of the optimizations made during development. An important thing to note before proceeding, however, is that this repository will be continuously worked on and improved. This may entail some differences between our latest implementation and [our initial publication](https://nunomota.github.io/assets/papers/www2021.pdf). This page also assumes the reader to have a prior understanding of the Spatial Inequality Index's formalization.

## Optimal algorithm

As explained [in our publication](https://nunomota.github.io/assets/papers/www2021.pdf), the school redistricting problem can analogously be understood as a graph partitioning problem. By imagining schools throughout a state as nodes and their neighborhoods as edges, then it is easy to interpret a district as some partition of the overall school graph. Since our goal is to minimize spatial inequality, we have to find the optimal partition for that result. As we found, however, this is an [NP-Complete](https://en.wikipedia.org/wiki/NP-completeness) problem (i.e., an optimal algorithm would easily become computationally intractable).

## Greedy algorithm ([spatial_inequality.core](https://nunomota.github.io/spatial-inequality/docs/core/index.html))

A promising alternative to an exhaustive search over all possible partitions (i.e., to find the optimal solution) is to develop a heuristics-based algorithm. As such, we developed `GreedyPartitioining` that, starting from an initial partitioning scheme (i.e., school/district assignment), uses a greedy heuristic to redistrict schools. Its modus operandi is as follows:

1. Select a district that heavily contributes towards spatial inequality
2. Extract all the schools currently assigned to that district
3. Iterate (arbitrarily) over all schools extracted in (2) and:
    - If a school neighbors another district AND redistricting it would bring both districts' per-student funding closer, then the school is redistricted;
    - Do nothing otherwise.
4. Repeat steps 1-3 until no more improvement can be made to spatial inequality

Three clear initial design choices include (i) schools will only be redistricted *from* a selected district, (ii) only schools at a district's border can be redistricted, and (iii) our only measure of interest is "per-student funding" across all districts. Although fairly straightforward, used data structures will make (or break) our implementation. Below we detail all the choices made.

### Lazy Heap ([spatial_inequality.optimization.lazy_heap](https://nunomota.github.io/spatial-inequality/docs/optimization/lazy_heap.html))

From the start, we know that spatial inequality will only be minimal if all districts share the same per-student funding. Although differences *within* neighborhoods will have a higher emphasis in our calculations, as neighborhoods overlap we also implicitly account for observed differences *between* neighborhoods. This being the case, we know that minimal spatial inequality will be achieved when/if each district's per-student funding equals that of the whole state's. Naively, if at each iteration of the algorithm we sorted all districts by their own funding's absolute difference to the whole state's, and then extract the top-most result, we complete step (1) of `GreedyPartitioning` (i.e., we select the district that mostly deviates from our goal).

To prevent needless calculations at each iteration, we can simply implement a max heap tree. Here each node contains a district, sorted based on its per-student funding's absolute difference from the sate it belongs to. As such, we need only to `pop` from the heap at each iteration, make our changes to the district, and then `push` it back in. Our implementation deviates from a standard max heap tree because we also need to quickly update nodes that contain districts involved in redistricting decisions, during the previous stage of computation. Insertions are cheap, but node updates - by removing a previous instance of the node and then pushing its new instance - are not. The "lazy" evaluation comes in play because for every popped district, we may have to update up to *D* other districts. Our `LazyHeap` then keeps a map to the newest instance of every district, and upon insertion of a new instance it simply marks the old instance as "deleted" and pushes the new instance in. Only when a node is popped will it be checked for validity (and discarded if flagged as "deleted"). To avoid saturating the heap with lazily deleted instances of nodes, from time to time it flushes itself to just retain valid nodes.

| Operation | Average-case | Worst-case |
| --- | --- | --- |
| `LazyHeap.push` | O(1) | O(log n) |
| `LazyHeap.pop` | O(1) | O(n) |
| `LazyHeap.update` | O(1) | O(log n) |
| `LazyHeap.flush` | O(n) | O(n) |

### School & District ([spatial_inequality.optimization.entity_nodes](https://nunomota.github.io/spatial-inequality/docs/optimization/entity_nodes.html))

We also created data structures to dynamically hold school/district assignments, where each `District` contains a set of assigned `Schools` and each `School` contains a set of neighboring `Schools`. They also contain updated information on their respective number of students and funding. These classes are used by all sub-modules inside `spatial_inequality.optimization`. They also trivialise step (2) of `GreedyPartitioning`.

| Operation | Average-case | Worst-case |
| --- | --- | --- |
| `District.add_school` | O(1) | O(n) |
| `District.remove_school` | O(1) | O(n) |
| `District.get_schools` | O(1) | O(1) |
| `School.add_neighbor` | O(1) | O(n) |
| `School.get_neighbors` | O(1) | O(1) |

### Lookup ([spatial_inequality.optimization.lookup](https://nunomota.github.io/spatial-inequality/docs/optimization/lookup.html))

There are several high-level operations we may like to perform - on top of `District` and `School` instances - to further increase the performance of our algorithm. For instance, extracting schools at the border of a district immediately, as opposed to iterating over all schools of a district and checking each one for validity, would immediately benefit stage (3) of `GreedyPartitioning`. For this purpose, `Lookup` contains a series of underlying maps that can be updated dynamically as schools are redistricted. Since not a lot of redistricting operations are executed - when compared to the amount of general informational lookups, - it's preferable to update all underlying data structures whenever this happens. Generally this can be done very quickly, the worst case scenario only happening essentially when all schools neighbor all other schools and each is their own independent district.

| Operation | Average-case | Worst-case |
| --- | --- | --- |
| `Lookup.get_bordering_schools_by_district_id` | O(1) | O(1) |
| `Lookup.get_district_by_id` | O(1) | O(1) |
| `Lookup.get_district_by_school_id` | O(1) | O(1) |
| `Lookup.get_neighboor_districts_by_district_id` | O(1) | O(1) |
| `Lookup.get_neighboorhood_changes_by_district_id` | O(1) | O(1) |
| `Lookup.get_school_by_id` | O(1) | O(1) |
| `Lookup.assign_school_to_district_by_id` | O(1) | O(n<sup>2</sup>) |

### Holdout Queue ([spatial_inequality.optimization.holdout](https://nunomota.github.io/spatial-inequality/docs/optimization/holdout.html))

One of the main problems with the initial greedy heuristic implementation, by always popping the top element from `LazyHeap`, is that the algorithm might get stuck attempting to redistrict schools from the same district over and over again without success. As such, we may want to hold districts out of the `LazyHeap` until further moves are possible, and `enqueue` them into the `HoldoutQueue` instead. This data structure acts much like a standard FIFO queue, but allows for conditional `dequeue` (i.e., only the first item that validates a given condition will be returned). When the `LazyHeap` becomes empty, it will be refilled with all districts from the `HoldoutQueue` that have had at least one school redistricted in their immediate neighborhood after being `enqueued`. If this condition is not met, it means still no moves will be available for the district and it will remain in the `HoldoutQueue`.

| Operation | Average-case | Worst-case |
| --- | --- | --- |
| `HoldoutQueue.enqueue` | O(1) | O(1) |
| `HoldoutQueue.dequeue` | O(1) | O(n) |

### Early Stopper ([spatial_inequality.optimization.early_stopper](https://nunomota.github.io/spatial-inequality/docs/optimization/early_stopper.html))

Finally, if the `LazyHeap` becomes empty and no district can be dequeued from the `HoldoutQueue`, our algorithm will terminate. But it may occur that, after a given point, the algorithm simply iterates over all districts for marginal improvements (if any) on spatial inequality. To prevent this, `EarlyStopper` keeps track of spatial inequality at every iteration of the algorithm and preemptively stops its execution if more than a set amount of iterations have gone by without any noticeable improvement.

| Operation | Average-case | Worst-case |
| --- | --- | --- |
| `EarlyStopper.update` | O(1) | O(1) |