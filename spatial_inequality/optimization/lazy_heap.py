"""
Implements a "lazy heap" data structure, which provides a max-heap behavior but
uses lazy evaluation for optimized node update and removal.
"""
import copy

from heapq import heappush, heappop, heapify

class _LazyHeapNode:
    """
    Wrapper class for any item to be added onto the LazyHeap.

    Attributes:
        __lt (function): 'Less than' function to compare _LazyHeapNode
            instances.
        __data (Object): Stored item.
        __is_deleted (bool): Boolean flag to mark node for deletion.
    """
    __lt = None
    __data = None
    __is_deleted = None
    
    def __init__(self, data, lt):
        self.__lt = lt
        self.__data = data
        self.__is_deleted = False
    
    def get_data(self):
        """
        Getter method for the stored (unmodified) item.

        Returns:
            Object: Unmodified stored item.
        """
        return self.__data
    
    def delete(self, freeze_mode="shallow"):
        """
        Marks node for (lazy) deletion and freezes its current state by making a
        copy of its data.

        Args:
            freeze_mode (str): Should be "shallow", "deep" or None.

        Raises:
            AttributeError: Whenever an invalid freeze mode is specified.
        """
        # Freeze object reference
        if freeze_mode == "shallow":
            self.__data = copy.copy(self.__data)
        elif freeze_mode == "deep":
            self.__data = copy.deepcopy(self.__data)
        elif freeze_mode is None:
            pass
        else:
            raise AttributeError(f"Invalid freeze mode '{freeze_mode}'...")
        # Mark node as deleted
        self.__is_deleted = True
    
    def is_deleted(self):
        """
        Checks if a node is marked for (lazy) deletion.

        Returns:
            bool: 'true' if node is marked for deletion, 'false' otherwise
        """
        return self.__is_deleted
    
    def __lt__(self, other):
        """
        Checks whether node is 'less than' another node.

        Args:
            other (_LazyHeapNode): Node to compare against.

        Returns:
            bool: 'true' if node is lesser than its peer, 'false' otherwise.
        """
        return self.__lt(self.get_data(), other.get_data())
    
    def __str__(self):
        return " {}\n| Data: {}\n| Is deleted: {}\n {}".format(
            "-"*16,
            self.__data,
            self.__is_deleted,
            "-"*16
        )
    
    def __repr__(self):
        return str(self)

class LazyHeap:
    """
    This class implements a lazy max heap. In this implementation, lazy refers
    to how nodes are deleted. Instead of immediately removing a node from the
    heap and then fixing the underlying binary tree, each node is
    flagged as 'deleted' and discarded when popped.

    To prevent the heap from getting too large, if too many lazy deletions
    happen without nodes being popped, there is a maximum number of nodes
    allowed before the whole tree is pruned of deleted nodes and rebuilt.

    Attributes:
        __data (list): Heapified list of all items.
        __item_id (function): Function to extract a unique ID from an item.
        __gt (function): 'Greater than' function to compare items in the heap.
        __lazy_eval_map (dict): Mapping from a unique ID to all (non-deleted)
            _LazyHeapNode instances.
        __max_elems (int): Maximum number of elements allowed in the heap.

    Example:
        >>> class SoccerPlayer:
        ...     def __init__(self, name, goals):
        ...         self.name = name
        ...         self.goals = goals
        ...
        >>> # Create three distinct players
        >>> players = [
        ...     SoccerPlayer("A", 10),
        ...     SoccerPlayer("B", 7),
        ...     SoccerPlayer("C", 5)]
        >>> # Initialize max heap with all players
        >>> max_heap = LazyHeap(
        ...     item_id=lambda x: x.name,
        ...     gt=lambda x,y: x.goals > y.goals)
        >>> for player in players:
        ...     heap.push(player)
        >>> print(heap.pop().name)
        'A'
        >>> # Update heap entries
        >>> players[2].goals = 9
        >>> heap.update(players[2])
        >>> print(heap.pop().name)
        'C'
    """
    __data = None
    __item_id = None
    __gt = None
    __lazy_eval_map = None
    
    __max_elems = None
    
    def __init__(self, item_id=lambda x:x, gt=lambda x,y:x>y, max_elems=None):
        self.__data = []
        heapify(self.__data)
        self.__item_id = item_id
        self.__gt = gt
        self.__lazy_eval_map = {}
        self.__max_elems = max_elems
        self.__is_full = False
            
    def push(self, item):
        """
        Wraps a new item with _LazyHeapNode and adds it to the max heap.

        Args:
            item (Object): Item to be added.

        Raises:
            IndexError: Whenever the maximum number of nodes allowed in the heap
                has been reached.
        """
        new_node = _LazyHeapNode(item, self.__gt)
        # Check if heap size has not exceeded its maximum
        is_full = lambda: (self.__max_elems is not None) and (len(self.__data) >= self.__max_elems)
        if is_full():
            # Prune deleted nodes and re-check
            self.__prune_heap()
            if is_full(): raise IndexError("No more values can be added to the heap...")
        # Push item onto heap and update lazy evaluation map
        heappush(self.__data, new_node)
        self.__lazy_eval_map[self.__item_id(item)] = new_node

    def pop(self):
        """
        Retrieves the first non-deleted _LazyHeapNode from the max heap.

        Returns:
            _LazyHeapNode: First non-deleted item in the max heap, or None if
                heap is empty.
        """
        # Lazy evaluation of max heap
        while True:
            node = heappop(self.__data)
            if node.is_deleted():
                continue
            item = node.get_data()
            self.__lazy_eval_map.pop(self.__item_id(item), None)
            return item
    
    def update(self, item):
        """
        Updates an item that already exists in the heap, by marking its previous
        instance as deleted and then pushing a new one onto the heap.

        NOTE: For this method to work as intended, __item_id has to equally
        identify both the updated instance of the item and its previously
        existing one.

        Args:
            item (Object): Item to update.
        """
        # Lazy delete of pre-existing item
        self.__lazy_eval_map[self.__item_id(item)].delete()
        # Re-push item into heap
        self.push(item)
    
    def __prune_heap(self):
        """
        Removes all lazily deleted nodes from the heap and heapifies the
        remaining ones.
        """
        self.__data = list(filter(lambda x: not x.is_deleted(), self.__data))
        heapify(self.__data)