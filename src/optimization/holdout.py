from queue import Queue

class _HoldoutQueueItemWrapper:
    """
    Wrapper class for any item to be added onto HoldoutQueue. All instances of
    this class allow storage of both an actual item and an associated (static)
    tag.

    Attributes:
    __item (Object): Stored item
    __tag (Object): Stored tag

    Methods:
    get_data(): Getter method for the stored (unmodified) item.
    get_tag(): Getter method for the stored item's tag.
    """
    __item = None
    __tag = None
    
    def __init__(self, item, tag):
        self.__item = item
        self.__tag = tag
        
    def get_data(self):
        """
        Getter method for the stored (unmodified) item.

        Returns:
        Object: Unmodified stored item
        """
        return self.__item
    
    def get_tag(self):
        """
        Getter method for the stored item's tag.

        Returns:
        Object: Unmodified stored tag
        """
        return self.__tag
        
class HoldoutQueue:
    """
    This class implements a holdout queue that, in addition to the functionality
    of a standard (FIFO) queue, allows for filtering on items upon dequeue. More
    specifically, instead of returning the first-most item in the queue, only
    the first item that validates a specified filtering condition will be
    dequeued. All other items will be held out as if the queue were empty,
    preserving their initial order.

    Internally, this class operates on top of two independent (FIFO) queues. The
    first (i.e., primary queue) is where all items are either enqueued to or
    dequeued from. The second queue (i.e., leftover queue) is where all items
    dequeued from the former queue get enqueued in case they do not validate the
    specified condition. When the primary queue becomes empty, then instances of
    this class can be 'recycled', swapping the primary and leftover queues.

    Attributes:
    __primary_queue (Queue): Underlying primary queue
    __leftover_queue (Queue): Unerlying leftover queue
    __get_item_tag (function): Function to calculate an item's tag
    __is_valid (function): Function to validate an item (based on its tag)

    Methods:
    recycle(): Recycles the holdout queue, swapping the primary and leftover
        queues.
    enqueue(item): Wraps a new item with _HoldoutQueueItemWrapper and adds it at
        the end of the holdout queue.
    dequeue(item): Retrieves the first valid _HoldoutQueueItemWrapper from the
        beginning of the holdout queue.
    get_primary_queue(): Getter method for the holdout queue's primary queue.
    __is_empty(): Checks whether the primary queue is empty.

    Example:
    >>> def is_even(n):
    ...     return n%2 == 0
    >>> holdout_queue = HoldoutQueue(is_valid=is_even)
    >>> for i in range(5):
    ...     holdout_queue.enqueue(i)
    >>> print(holdout_queue.dequeue())
    2
    >>> print(holdout_queue.dequeue())
    4
    """
    __primary_queue = None
    __leftover_queue = None
    __get_item_tag = None
    __is_valid = None
    
    def __init__(self, get_item_tag=lambda x:x, is_valid=lambda x:True):
        self.__primary_queue = Queue()
        self.__leftover_queue = Queue()
        self.__get_item_tag = get_item_tag
        self.__is_valid = is_valid
    
    def recycle(self):
        """
        Recycles the holdout queue, swapping the primary and leftover queues.
        """
        self.__primary_queue, self.__leftover_queue = self.__leftover_queue, self.__primary_queue
    
    def enqueue(self, item):
        """
        Wraps a new item with _HoldoutQueueItemWrapper and adds it at the end of
        the holdout queue.

        Parameters:
        item (Object): Item to be added
        """
        item_wrapper = _HoldoutQueueItemWrapper(
            item,
            self.__get_item_tag(item)
        )
        self.__primary_queue.put(item_wrapper)
        
    def get_primary_queue(self):
        """
        Getter method for the holdout queue's primary queue.

        Returns:
        Queue: Primary queue
        """
        return self.__primary_queue
        
    def dequeue(self):
        """
        Retrieves the first valid _HoldoutQueueItemWrapper from the beginning of
        the holdout queue.

        Returns:
        Object: First valid item from the primary queue, or None if primary
            queue is empty
        """
        while True:
            if self.__is_empty():
                return None
            item_wrapper = self.__primary_queue.get()
            if self.__is_valid(item_wrapper):
                return item_wrapper.get_data()
            self.__leftover_queue.put(item_wrapper)
            
    def __is_empty(self):
        """
        Checks whether the primary queue is empty.

        Returns:
        bool: 'true' if primary queue is empty, 'false' otherwise
        """
        return self.__primary_queue.empty()