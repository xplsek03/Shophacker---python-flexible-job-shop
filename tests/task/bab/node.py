'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from task.sbh.graph import Graph
import copy
#from task.output.timer import timer


'''
Reprezentace uzlu stromu metody branch and bound.
'''
class Node(object):

    
    def __init__(self, *args, **kwargs):
        
        self.lmax = float("inf")  # hodnota Lmax tohoto uzlu
        self.is_ok = kwargs.get('is_ok', True)  # jestli ma byt uzel odriznut nebo ne
        self.planned = kwargs.get('planned', [])  # tohle je seznam operaci ktere jsou na tomto uzlu uz naplanovane
        self.poddani = []  # seznam poddanych uzlu
        self.father = kwargs.get('father', None)  # odkaz na otcovsky uzel
        self.kriterium_A = True  # zda uzel splnuje nepreempci (kriterium A)

 
    '''
    Vypocet pj u operace
    @param slovnik_van
    @param slovnik_jerabu
    @param item - instance Namaceni/Transport
    @param is_namaceni - zda se jedna o planovani operaci namaceni nebo transportu
    @return pj
    '''
    def calculate_pj(self, slovnik_van, slovnik_jerabu, item, is_namaceni):
        
        # pokud se jedna o vanu je vsude stejne
        if is_namaceni:
            pj = slovnik_van[item.id_stroj]['exp_max']
        else:
            # pj na transportni operaci pocitas pomoci toho jak daleko ten jerab pojede - od vany co je pred prvkem do vany co je za prvkem
            nxt_vana = slovnik_van[item.next.id_stroj]
            prv_vana = slovnik_van[item.prev.id_stroj]
            jerab = slovnik_jerabu[item.id_stroj]
            pj = jerab['raise_low'] + prv_vana['drain'] + jerab['raise_high'] + jerab['move'] * abs(prv_vana['position'] - nxt_vana['position']) + nxt_vana['dive']
        return pj
        
        
    '''
    Odpovida za planovani operaci na jednom stroji, aplikaci preemptivniho pravidla.
    @param graf - G nebo G'
    @param cmax
    @param slovnik_van
    @param slovnik_jerabu
    @param plan_input - seznam operaci, ktere maji byt provedeny na tomto stroji. Seznam instanci Namaceni/Transport
    @param is_namaceni - zda se jedna o operaci namaceni nebo transportu
    '''
    def single_machine_planning(self, graf, cmax, slovnik_van, slovnik_jerabu, plan_input, is_namaceni=True):
        
        # data pro EDD jednoho seznamu operaci na konkretnim stroji
        self.m_edd = []
        
        # pridej rj, dj, pj data kazde operace pro EDD
        for item in plan_input:
            
            # vypocitej pj
            pj = self.calculate_pj(slovnik_van, slovnik_jerabu, item, is_namaceni)
            # vypocitej rj, dj
            rj, pozitivni_cyklus = Graph.bellman(graf, node_from="start", node_to=item.graphid)
            
            # mezikrok pro vypocet dj
            dj_pre, _ = Graph.bellman(graf, node_from=item.graphid, node_to="end")
            dj = cmax - (dj_pre - pj)
            
            # pokud je i v seznamu planned, pridej jako order jeho index, jinak vysoke cislo
            order = len(plan_input)
            if item.graphid in self.planned:
                order = self.planned.index(item.graphid)            
            
            # uloz do seznamu EDD vlastnosti
            self.m_edd.append({'rj': rj, 'dj': dj, 'pj': pj, 'order': order, 'stroj': item})               
        
        # serad seznam podle order a prvky o stejne dulezitosti podle dj
        self.m_edd = sorted(sorted(self.m_edd, key=lambda x: x['dj']), key=lambda x: x['order'])
        m_edd_original = copy.deepcopy(self.m_edd)  # kopie pro zaverecne overeni

        # diskretni simulace s casovymi posuny, kde se analyzuje pouze situace kde muze nastat k nejake zmene, aby se nemusela analyzovat kazda sekunda
        # tohle je seznam vyslednych casovych useku
        self.casove_useky = []    

        # aktualni cas T
        edd_time = 0
        
        # pokud jsou nejake zarazene, tak ber cas te prvni a vyhod ty naplanovane
        if self.m_edd[0]['order'] == 0:

            # ids co budes vyhazovat ven
            ids_ven = []
            
            # nejprve naplanuj co uz je prirazeno jako order
            for index, u in enumerate(self.m_edd):
                
                # pokud uz je zarazena, pridej casovy usek
                if u['order'] != len(plan_input):
                    
                    # vyber start z max, budto startuje z casu nebo az pote co je splnen jeho rj
                    start = max(edd_time, self.m_edd[index]['rj'])
                    end = start + self.m_edd[index]['pj']
                    self.casove_useky.append({'start': start, 'end': end, 'stroj': self.m_edd[index]['stroj']})
                    # posun cas o zpracovani pridane naplanovane operace
                    edd_time = end

                    ids_ven.append(index)
                    
            # vyhod ven zarazene prvky
            for i in sorted(ids_ven, reverse=True):
                self.m_edd.pop(i)

        # serad prvky dle dj, rj
        self.m_edd = sorted(sorted(self.m_edd, key=lambda x: x['rj']), key=lambda x: x['dj'])       

        # otestuj kriterium C
        # tyka se to pripadu kdy v m_edd zbyva k naplanovani vice nez jedna polozka
        if len(self.m_edd) > 1:
            if not self.node_test_c(edd_time):
                return
        
        # postupne prochazej seznam a vybirej polozky ke spusteni
        while len(self.m_edd):
            # proved funkci a update casu
            edd_time = self.find_next(edd_time)
        
        # jdi podle puvodnich polozek v harmonogramu namaceni
        self.lmax = float("-inf")
        for item in plan_input:
            # najdi posledni zaznam v casove_useky s timto id a urci cas ukonceni operace, z toho vypocitej Lx
            lx = [c for c in self.casove_useky if c['stroj'].graphid == item.graphid][-1]['end'] - next((i for i in m_edd_original if i['stroj'].graphid == item.graphid), False)['dj']
            if lx > self.lmax:
                self.lmax = lx
                                    
        # otestuj preempci - kriterium A
        if len(self.casove_useky) != len(m_edd_original):                
            self.kriterium_A = False

    '''
    Odpovida za naplanovani operace na stroji.
    @param edd_time - aktualni cas v ramci prubehu planovani
    @return aktualizovany cas
    '''
    def find_next(self, edd_time):

        # nejblizsi nalezeny cas rj, kterym se da zacit
        rj_next = float("inf")

        # projdi prvky od zacatku
        for index, m in enumerate(self.m_edd):
            
            # pokud prvek muze zacit, vrat jeho index
            if m['rj'] <= edd_time:
                
                # pokud je to prvni prvek, tj vloz ho rovnou
                if not index:
                    self.casove_useky.append( {'start': edd_time, 'end': edd_time + self.m_edd[index]['pj'], 'stroj': self.m_edd[index]['stroj']} )
                    # nastav cas na konec zpracovani, nemusis hledat dalsi prvek
                    rj_next = edd_time + self.m_edd[index]['pj']
                    
                    # oddelej ze seznamu
                    self.m_edd.pop(index)
                    
                    break
                    
                # pokud ten prvek neni s nejnizsim dj, tak usekni z jeho pj a vloz casovy usek
                else:
                    
                    # najdi v listu odshora az sem index prvku ktery bude dalsi, a podle rj tohoto prvku usekni pj z prvku ktery ted zpracovavas
                    # protoze je zaroven serazeny podle dj, tak vrati nejnizsi rj u toho co ma nizsi dj zaroven                        
                    next_it = min(self.m_edd[:index], key=lambda x: x['rj'])
                    
                    # tohle je doba po kterou muzes zpracovavat tenhle produkt [index]
                    delta = next_it['rj'] - edd_time
                    
                    # pokud je delta vetsi nez cas zpracovani, tj vejde se do ni cely produkt
                    if delta >= self.m_edd[index]['pj']:
                        self.casove_useky.append( {'start': edd_time, 'end': edd_time + self.m_edd[index]['pj'], 'stroj': self.m_edd[index]['stroj']} )
                        
                        # tenhle produkt uz muzes vyhodit ven ze seznamu
                        self.m_edd.pop(index)
                    
                    # pripoj casovy usek do vysledku a usekni pj podle dalsi polozky ktera bude v poradi
                    else:    
                        self.casove_useky.append( {'start': edd_time, 'end': edd_time + delta, 'stroj': self.m_edd[index]['stroj']} )
                
                        # usekni z polozky co uz jsi zpracoval
                        self.m_edd[index]['pj'] -= delta

                    # preskoc na dalsi produkt co ma byt v poradi
                    rj_next = next_it['rj']

                    # konec, budes prechazet na dalsi produkt
                    break
                
            # pokud nemuze zacit, alespon otestuj jeho rj a pripadne jim muzes zacit priste
            elif m['rj'] < rj_next:
                rj_next = m['rj']
                
        # nenasel, takze nastav cas na rj_next       
        return rj_next
    
        
    '''
    Otestuj uzel na kriterium C.
    @param t - cas dokonceni vsech naplanovanych operaci na stroji (cas t).
    @return False pokud porusi kriterium
    '''
    def node_test_c(self, t):
        
        # rjk = min_from_jobs_J(max(t, rl) + pl)
        
        mins = set()
        # vezmi nenaplanovane operace
        for op in self.m_edd[1:]:
            mins.add(max(t, op['rj']) + op['pj'])
        
        # pokud splnuje kriterium C
        if self.m_edd[0]['rj'] < min(mins):
            return True
        # nesplnuje, urizni ho
        else:
            # nastav uzel k rezani
            self.is_ok = False
            return False
        
