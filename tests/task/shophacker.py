'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace
'''

from multiprocessing import Process
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.optimize import minimize
from task.genetix.genetics import Jobshop
from task.genetix.memberinit import Memberinit 
from task.genetix.operatory import Krizeni, Mutace, Deduplikace
import sys
import glob
import os
import datetime
from pymongo import MongoClient
import math
import credentials
#import datetime


'''
Proces, ktery se stara o zalozeni instance problemu a algoritmu (pymoo).
'''
class ShophackerProcess(Process):

    
    def __init__(self, id, **kwargs):
        super(ShophackerProcess, self).__init__()
        self.id = id  # id ulohy
  
              
    '''
    funkce, ktera odpovida za vytvoreni a start minimalizacni ulohy
    '''
    def run(self):
        
        #print(datetime.datetime.now())
        
        # smaz obsah slozky
        img = glob.glob('images/*')
        for i in img:
            os.remove(i)

        # pripoj se k db. multiprocessing = novy klient
        db = MongoClient(credentials.cred['db_string'], tls=True)
        db = db['database1']
        # zjisti zakladni konfiguracni parametry GA
        konfig = db['konfig'].find_one({"_default": True})   

        # tohle je sice duplikat toho co je v genetics, ale je to lepsi nez posilat do te tridy deset ruznych parametru        
        zaznam = db['historie'].find_one({'_id': self.id})
        produkty = list(db['produkty'].find({'_id': {'$in': [i['id'] for i in zaznam['produkty']]}}))   
        slovnik_produktu = {}
        for p in produkty:
            if p['_id'] not in slovnik_produktu:
                slovnik_produktu[p['_id']] = p
        
        # vypocitej pocet clenu populace
        faktorial_top = 0
        faktorial_down = 1
        for p in zaznam['produkty']:
            # pricti k celkovemu poctu prvku v chromozomu
            for _ in range(p['pocet']):
                faktorial_top += len(slovnik_produktu[p['id']]['kroky'])
                faktorial_down *= math.factorial(len(slovnik_produktu[p['id']]['kroky']))   
        
        # vygeneruj instanci GA
        # dochazi k overeni zda pocet chromozomu vubec dosahuje mocnosti zadane populace
        # asi se nemuze stat ze by vyslo necele cislo, ale nechce se mi nad tim ted premyslet
        algorithm = NSGA2(pop_size=min(konfig['populace'], int(math.factorial(faktorial_top) / faktorial_down)), sampling=Memberinit(), crossover=Krizeni(), mutation=Mutace(), eliminate_duplicates=Deduplikace())
        
        # instance problemu jobshop
        problem = Jobshop(id=self.id, cores=konfig['cores'])
        
        # zacni resit problem
        minimize(problem, algorithm, ('n_gen', sys.maxsize if konfig['nekonecno'] else konfig['generace']), seed=1, verbose=True)
        
        #print(datetime.datetime.now())
        
        # zrus multiprocessing pool = vznika pri zalozeni instance problemu
        problem.pool.close()
        
        # proces skoncil, nastav cas ukonceni
        db['historie'].update_one({'_id': self.id}, {'$set': {'end': datetime.datetime.now()}})
