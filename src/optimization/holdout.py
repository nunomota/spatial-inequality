from queue import Queue

class _HoldoutQueueItemWrapper:
    
    __item = None
    __tag = None
    
    def __init__(self, item, tag):
        self.__item = item
        self.__tag = tag
        
    def get_data(self):
        return self.__item
    
    def get_tag(self):
        return self.__tag
        
class HoldoutQueue:
    
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
        self.__primary_queue, self.__leftover_queue = self.__leftover_queue, self.__primary_queue
    
    def enqueue(self, item):
        item_wrapper = _HoldoutQueueItemWrapper(
            item,
            self.__get_item_tag(item)
        )
        self.__primary_queue.put(item_wrapper)
        
    def get_primary_queue(self):
        return self.__primary_queue
        
    def dequeue(self):
        while True:
            if self.__is_empty():
                return None
            item_wrapper = self.__primary_queue.get()
            if self.__is_valid(item_wrapper):
                return item_wrapper.get_data()
            self.__leftover_queue.put(item_wrapper)
            
    def __is_empty(self):
        return self.__primary_queue.empty()