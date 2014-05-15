import threading


class ThreadSafeQueue(object):
    """Makes a thread safe queue for implementing 
    the producer-consumer model.
    """
    def __init__(self):
        self.l = []
        self.l_sem = threading.Semaphore(0)
        self.l_mut = threading.Lock()
    
    def add(self, item):
        self.l_mut.acquire()
        self.l.append(item)
        self.l_mut.release()
        self.l_sem.release()
    
    def remove(self):
        self.l_sem.acquire()
        self.l_mut.acquire()
        result = self.l.pop(0)
        self.l_mut.release()
        return result
    
    def __len__(self):
        return len(self.l)


