'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import gc


# pomocne testovani GC
def dump_garbage():
        
    # force collection
    gc.collect()

    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:80]
        print (type(x),"\n  ", s)
