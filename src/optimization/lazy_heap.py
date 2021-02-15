import copy

from heapq import heappush, heappop, heapify

class _LazyHeapNode:
    
    __lt = None
    __data = None
    __is_deleted = None
    
    def __init__(self, data, lt):
        self.__lt = lt
        self.__data = data
        self.__is_deleted = False
    
    def get_data(self):
        return self.__data
    
    def delete(self, freeze_mode="shallow"):
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
        return self.__is_deleted
    
    def __lt__(self, other):
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
        # Lazy evaluation of max heap
        while True:
            node = heappop(self.__data)
            if node.is_deleted():
                continue
            item = node.get_data()
            self.__lazy_eval_map.pop(self.__item_id(item), None)
            return item
    
    def update(self, item):
        # Lazy delete of pre-existing item
        self.__lazy_eval_map[self.__item_id(item)].delete()
        # Re-push item into heap
        self.push(item)
    
    def __prune_heap(self):
        # Reset data and heapify
        self.__data = list(filter(lambda x: not x.is_deleted(), self.__data))
        heapify(self.__data)