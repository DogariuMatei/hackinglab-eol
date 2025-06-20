import threading

CHILD_PROCESSES_LOCK = threading.Lock()
CHILD_PROCESSES = []
