'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import functools
import time
import logging


'''
Pomocna funkce pri debugu.
'''
def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        logging.debug(f"{func.__name__}\t{elapsed_time:0.8f}")
        return value
    return wrapper_timer
