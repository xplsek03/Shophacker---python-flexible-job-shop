'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import numpy as np
from pymoo.model.problem import Problem
import secrets
from task.sbh.sbh import Sbh
from task.sbh.graph import Graph
from task.genetix.rating import calculate_simple_storage, calculate_full_storage, full_windowing, simple_windowing
import random
from pymongo import MongoClient
import copy
from pathos.multiprocessing import ProcessingPool as Pool
import logging
import credentials
#from task.output.timer import timer


'''
pymoo subclass - optimalizacni problem
'''
class Jobshop(Problem):
    
    
    def __init__(self, *args, **kwargs):
        
        # n_var = pocet promennych v ramci jedince
        # n_obj = pocet objektivnich funkci (Storage, Cmax)
        # n_constr = omezovaci podminky, nepouzito
        super(Jobshop, self).__init__(n_var=1, n_obj=2, n_constr=0)

        # id prave resene ulohy
        self.id = kwargs.get('id', None)
        
        # nutne promenne
        self.slovnik_van = {}
        self.slovnik_produktu = {}
        self.slovnik_jerabu = {}

        # multiprocessing pool
        self.pool = Pool(kwargs.get('cores', None))

        # databaze
        db = MongoClient(credentials.cred['db_string'], tls=True)
        db = db['database1']

        # slovnik uklada udaje o kvalite jedince populace, pouzito u operatoru krizeni
        # { id_clena: hodnota }
        self.bads = {}

        # zacni stazenim db, pokracuj inicializaci populace
        zaznam = db['historie'].find_one({'_id': self.id})

        # projdi produkty a generuj
        produkty = list(db['produkty'].find({'_id': {'$in': [i['id'] for i in zaznam['produkty']]}}))
        
        # vytvor seznam van s parametry, podle toho jake produkty budeme delat
        id_van = set()
        for p in produkty:  # produkt
            for krok in p['kroky']:  # krok
                for vana in krok:
                    id_van.add(vana)
              
        # mas seznam van co potrebujes, vezmi je z db
        self.vany = list(db['vany'].find({'_id': {'$in': list(id_van)}}))
        random.shuffle(self.vany)
        
        # zaloz slovnik van, bude se hodit u budovani grafu pri ziskavani vlastnosti vany
        for v in self.vany:
            self.slovnik_van[v['_id']] = v
        
        # id pouzitelnych jerabu
        self.jeraby = zaznam['jeraby']
        random.shuffle(self.jeraby)
        
        # seznam jerabu co se da pouzit
        jeraby = db['jeraby'].find({'_id': {'$in': zaznam['jeraby']}})
        for j in jeraby:
            self.slovnik_jerabu[j['_id']] = j
        
        # vezmi konfiguraci z db, defaultni
        self.konfig = db['konfig'].find_one({'_default': True})
        
        # vytvor vychozi seznam produktu
        self.seznam_produktu = []
        for p in zaznam['produkty']:
            for i in range(p['pocet']):
                self.seznam_produktu.append({'id': p['id'], 'uid': secrets.token_hex(16)})
        
        # pretransformuj seznam produkty na slovnik, aby se v nem dalo snadneji vyhledavat
        for p in produkty:
            if p['_id'] not in self.slovnik_produktu:
                self.slovnik_produktu[p['_id']] = p
        

    '''
    metoda vyhodnocujici kvalitu populace
    
    @param X - jedinci jedne populace v numpy poli
    @param out - slovnik, do ktereho se uklada kvalita jedincu v populaci
    '''
    def _evaluate(self, X, out, *args, **kwargs):
        
        '''
        vnorena funkce pouzita pro paralelni ohodnocovani jedincu v populaci
        
        @ clen - paralelne hodnoceny clen populace
        '''
        def custom_eval(clen):
            
            # generuj harmonogramy clena na jerabech a vanach
            harmonogram_jeraby, harmonogram_vany = Sbh.init_harmonogramy(self.vany, self.jeraby, clen)
    
            # postav jednoduchy graf G
            simple_g = Graph.simple_graph(clen, self.slovnik_van)
    
            # na G aplikuj SBH a uvnitr rovnou proved pripadnou opravu; vraci makespan, pripadne None pri chybe
            makespan_simple = Sbh.sbh(simple_g, self.slovnik_van, self.slovnik_produktu, harmonogram_vany, clen, simple=True)
        
            # pokud budes dal provadet vypocet s uplnym grafem
            if makespan_simple:
                # postav uplny graf G'
                full_g = Graph.full_graph(clen, self.slovnik_van, self.slovnik_jerabu, simple_g)
                
                # nahrej do G' vsechny disjunktivni spojnice namaceni co jsi ziskal ze simple grafu. harmonogram_vany ted obsahuje poradi operaci namaceni dle EDD!
                Graph.add_disj_from_simple(full_g, harmonogram_vany, self.slovnik_van, self.slovnik_jerabu)
                
                # SBH nad G'
                makespan_full = Sbh.sbh(full_g, self.slovnik_van, self.slovnik_produktu, harmonogram_jeraby, clen, simple=False, slovnik_jerabu=self.slovnik_jerabu)
    
                # pokud to nevyjde s velkym grafem
                if not makespan_full:
                    
                    # proved update clena z G
                    Graph.update_clen_graf(simple_g)
                    
                    # vytvor casova okna u G - trvani transportu je relaxovano na 0!
                    simple_windowing(clen, self.slovnik_van)
                    
                    # vypocitej simple storage
                    storage = calculate_simple_storage(clen, self.slovnik_van)
                    
                    # vrat Cmax ze simple grafu
                    makespan = makespan_simple
                    failed = 5
    
                # doslo to az na konec - slo sestavit G i G'
                else:
                
                    # vypocitej start a end z grafu
                    Graph.update_clen_graf(full_g)
                    
                    # vytvor okna
                    full_windowing(clen, self.slovnik_van, self.slovnik_jerabu)
                    
                    # proved vypocet objektivu storage finalniho reseni
                    storage = calculate_full_storage(clen, self.slovnik_van)
                    
                    # Cmax
                    makespan = makespan_full
                    failed = 1
                    
                    # tady pak pokud ma storage 0 uloz jako vysledek do db, aby mohl byt poslan update ze to neco naslo
                    if storage == 0:
                        
                        logging.debug('GOTIT')
                        
                        # lokalni spojeni z procesu - protoze se jedna o multiprocessing
                        db = MongoClient("mongodb+srv://spider:EYfxBVzM7X37kOfY@cluster0.5mz8f.mongodb.net/database1?retryWrites=true&w=majority&authSource=admin")
                        db = db['database1']
                        
                        # stavajici vysledek
                        zaznam = db['historie'].find_one({'_id': self.id})
                        
                        # pokud vysledek neni lepsi nez stavajici, nedelej nic
                        if not 'vysledek' in zaznam or zaznam['vysledek']['cmax'] > makespan:
                            
                            # vloz vysledek do databaze
                            self.insert_to_db(clen, db, zaznam, makespan)
                
            # vratil chybu z G
            else:
                failed = 16
                # vysoke konstanty
                storage = 10000
                makespan = 1000000 

            '''
            for op in clen['namaceni']:
                print(op.id_produkt[-2:], end=" ")
            print(" || ", end=" ")
            for op in clen['transporty']:
                print(op.id_produkt[-2:], end=" ")
            print(" || " + str(makespan) + " " + str(storage) + " " + str(failed), end=" ")
            print("")
            '''
        
            # vrat hodnotu failed pro pozdejsi pouziti v krizeni a hodnoty objektivnich funkci, penalizovane tim jak daleko reseni doslo
            return (clen['id'], failed), [storage * failed, makespan * failed]
        
        
        # seznam jedincu pro zpracovani v poolu procesu
        exes = [X[a][0] for a in range(len(X))]
        
        try:
            
            # paralelni zpracovani
            bads, F = zip(*self.pool.map(custom_eval, exes))
            
            # ulozvracene hodnoty failed, pouzito v krizeni
            for k,v in bads:
                self.bads[k] = v
            
            # uloz hodnoty objektivnich funkci
            out["F"] = np.array(F)
            
        # CTRL+C
        except KeyboardInterrupt:
            self.pool.terminate()
            self.pool.join()
        
    
    '''
    multiplikace poctu produktu, pro ktere ma byt vytvoren casovy harmonogram
    
    @param result - slovnik s vysledkem ulohy, vytvoreny metodou insert_to_db
    @param multiplier - nasobitel poctu produktu v uloze
    '''
    def multiply(self, result, multiplier):
        
        # kopie vysledku pro opakovane kopirovani
        kopie_main = copy.deepcopy(result)

        # ids van
        v_ids = set()
        for v in result['namaceni']:
            v_ids.add(v['stroj'])

        # zaloz seznamy prvnich a poslednich polozek van
        kopie_starters = []
        finishers = []
        for id in v_ids:
            l = [i for i in result['namaceni'] if i['stroj'] == id]
            finishers.append( max(l, key=lambda x: x['end']) )
            kopie_starters.append( min(l, key=lambda x: x['start']) )
        
        # nejvyssi hodnota end ktera je mezi nimi
        cmax = max([i['end'] for i in finishers])

        # ted mas nastaveny posunuty casy prvnich polozek, tak najdi nejmensi deltu
        mindelta = min([s['start'] + cmax - f['end'] for f,s in zip(finishers, kopie_starters)]) 
    
        # res jednu kopii za druhou
        for m in range(1, multiplier):

            # lokalni kopie pro pridani
            kopie = copy.deepcopy(kopie_main)
            
            # vytvor string ktery pridas k id kopie
            randstr = secrets.token_hex(1)
                
            # zaloz nove productids v ramci kopie, taky nove ids a prolinkuj je pomoci prev/next
            for k in kopie['namaceni']:
                k['productid'] += randstr
                if k['next']:
                    k['next'] += randstr
                if k['prev']:
                    k['prev'] += randstr
                k['id'] += randstr
                k['start'] += (m * (cmax - mindelta))
                k['end'] += (m * (cmax - mindelta))
    
            for k in kopie['transporty']:
                if k['next']:
                    k['next'] += randstr
                if k['prev']:
                    k['prev'] += randstr
                k['id'] += randstr
                k['start'] += (m * (cmax - mindelta))
                k['end'] += (m * (cmax - mindelta))  
              
            result['namaceni'] += kopie['namaceni']
            result['transporty'] += kopie['transporty']
            
            # novy cmax
            result['cmax'] += (cmax - mindelta)


    '''
    vlozeni nalezeneho nejlepsiho vysledku do db
    
    @param clen - clen populace
    @param db
    @param zaznam - zaznam v db
    @param makespan - Cmax 
    '''
    def insert_to_db(self, clen, db, zaznam, makespan):
        
        # slovnik kterou budes ukladat do db jako vysledek
        result = {}
        # tohle je tam jen kvuli pohodli uzivatele pri prohlizeni ganttu - productid_slovnik
        result['namaceni'] = [{'stroj': i.id_stroj, 'productid': i.id_produkt, 'id_ve_slovniku': i.id_ve_slovniku, 'id': i.graphid, 'start': i.start, 'end': i.end, 'prev': i.prev.graphid if i.prev else None, 'next': i.next.graphid if i.next else None} for i in clen['namaceni']]
        result['transporty'] = [{'stroj': i.id_stroj, 'id': i.graphid, 'start': i.start, 'end': i.end, 'prev': i.prev.graphid, 'next': i.next.graphid} for i in clen['transporty']]
        result['cmax'] = makespan
        
        # pokud ma dojit k multiplikaci
        if zaznam['multiply'] > 1:
            self.multiply(result, zaznam['multiply'])
        
        # vloz vysledek do db a oznac jako dokonceno
        db['historie'].update_one({"_id": self.id}, {"$set": {'vysledek': result}})  
