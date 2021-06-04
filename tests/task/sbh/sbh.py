'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from task.sbh.graph import Graph
from task.bab.edd import Edd
import logging
#from task.output.timer import timer


'''
Funkce pro provadeni Shifting bottleneck heuristiky.
'''
class Sbh:
    
    
    '''
    Inicializace harmonogramu nad jeraby a vanami.
    @param vany - seznam van
    @param jeraby - seznam jerabu
    @param clen - jedinec populace
    @return tuple se slovniky harmonogramu
    '''
    def init_harmonogramy(vany, jeraby, clen):
        
        # harmogram zpracovani na vanach: {id_vany: [operace zpracovavane na teto vane], .. }
        harmonogram_vany = {}
        
        for vana in vany:
            # filtruj podle konkretniho id vany: seznam operaci, ktere se provadi na jedne vane
            filtered = list(filter(lambda x: (x.id_stroj == vana['_id']), clen['namaceni']))
            
            # pridej do seznamu harmonogramu, pokud se ve vane bude neco namacet. DEBUG: promenna, self vany je overkill?
            if len(filtered):
                harmonogram_vany[vana['_id']] = filtered
            
        # harmogram zpracovani na jerabech: {id_stroj: [operace zpracovavane na tomto jerabu], .. }
        harmonogram_jeraby = {}
        # sestav plan na jednotlivych jerabech
        for jerab in jeraby:
            filtered = list(filter(lambda x: (x.id_stroj == jerab), clen['transporty']))
            # pridej do seznamu harmonogramu pokud na jerabu bude neco prepravovaneho. DEBUG: mozna pouzit jinou promennou, overkill
            if len(filtered):
                harmonogram_jeraby[jerab] = filtered
            
        return (harmonogram_jeraby, harmonogram_vany)


    '''
    SBH - shifting bottleneck heuristika.
    @param graf - graf nad kterym se ma provadet, jednoduchy G nebo uplny G'
    @param slovnik_van
    @param slovnik_produktu
    @param harmonogram - slovnik, klic: stroj hodnota: seznam operaci na stroji
    @param clen - jedinec populace
    @param simple - G = True, G' = False
    @param slovnik_jerabu
    @return cmax nebo None
    '''
    def sbh(graf, slovnik_van, slovnik_produktu, harmonogram, clen, simple=True, slovnik_jerabu=None):
        
        # pro simple poprve uz mas pridanou jednu vanu v m0, tedy prvni prvek harmonogramu zahod pro simple
        first = True
        
        # postupne planuj cleny harmonogramu, v jednom harmonogramu je seznam namaceni ruznych jobu v jedne vane nebo seynam transportu
        for m_id, m in harmonogram.items():
            
            # pouze simple, skipni EDD u 1. vany - pridas jak to je
            if first and simple:
                # proved vypocet fake EDD
                useky = Sbh.fake_edd(m, m_id, slovnik_van, graf)
                # nahrej do grafu disjunktivni spojnice prvni vany, id vem z harmonogram (harmonogram_vany)
                Graph.add_disjunctive(graf, useky, slovnik_van, slovnik_jerabu, simple)
                first = False             
                continue
            
            # v kazde iteraci pocitas vlastni cmax
            cmax, pozitivni_cyklus = Graph.bellman(graf, node_from="start", node_to="end")
            if pozitivni_cyklus:
                return None
            
            # proved branch and bound pro konkretni stroj. best = Node() | None pokud to nenajde reseni
            node = Edd.branch_and_bound(slovnik_van, slovnik_jerabu, graf, m, cmax, is_namaceni=simple)
            
            # BaB nenasel vysledek - chyba aproximace
            if not node:
                logging.debug('CHYBA BAB')
                return None
        
            # vloz do grafu ziskane spojnice - o hodnote exp_max te vany nebo LT + ET u uplneho grafu
            Graph.add_disjunctive(graf, node.casove_useky, slovnik_van, slovnik_jerabu, simple)
            
            # over na pozitivni cyklus
            cmax, pozitivni_cyklus = Graph.bellman(graf, node_from="start", node_to="end")
            if pozitivni_cyklus:
                # odted vime ze obsahuje pozitivni cyklus
                # odeber pridane disjunktivni hrany
                Graph.remove_disjunctive(graf, node.casove_useky)
                # vytvor LB a UB pro kazdy prvek, rozmezi v jakem muze swapovat s dalsim prvkem
                Sbh.init_lb_ub(node.casove_useky)
                # postupne prehazuj dva prvky dokud nenajdes odpovidajici harmonogram na stroji, co netvori pozitivni cyklus
                cmax = Graph.sbh_reparation(graf, node.casove_useky, slovnik_van, slovnik_jerabu, simple)
                if not cmax:
                    return None
            
            # updatuj - serad podle noveho - zaznam harmonogramu, kvuli velkemu grafu - aby vedel ktere disjunktivni aktualni spojnice ma vytvaret
            mapa = [i['stroj'].graphid for i in node.casove_useky]
            m.sort(key=lambda x: mapa.index(x.graphid))
        
        # vrat vypocitany cmax
        return cmax  
        

    '''
    Pomocna funkce pro generovani poradi upper a lower bounds, ktere budou respektovany
    pri prehazovani kombinace prvku v pripade opravy sekvence v SBH v kroku 4.
    @param useky - casove useky vracene z Node()
    '''
    def init_lb_ub(useky):
        
       for j in range(len(useky)):
            # jdi doleva, defaultne nastav 0
            useky[j]['lb'] = 0
            it = 0
            for l in reversed(useky[:j]):
                if l['stroj'].id_produkt == useky[j]['stroj'].id_produkt:
                    useky[j]['lb'] = j - it
                    break
                it += 1
            # jdi doprava
            useky[j]['ub'] = len(useky) - 1
            for i, r in enumerate(useky[j:]):
                if r['stroj'].id_produkt == useky[j]['stroj'].id_produkt:
                    useky[j]['ub'] = j + i
            
   
    '''
    Pridani operaci prvniho stroje bez provadeni EDD. Pouze u jednoducheho grafu.
    @param m - seznam operaci provadenych na stroji
    @param id - id stroje
    @param slovnik_van
    @param graf - jednoduchy graf G'
    @return vygenerovany seznam casovych useku
    '''
    def fake_edd(m, id, slovnik_van, graf):
        
        # finalni useky
        useky = []
        # projdi seznam polozek
        for item in m:
            rj, pozitivni_cyklus = Graph.bellman(graf, node_from="start", node_to=item.graphid) 
            if pozitivni_cyklus:
                return None
            pj = slovnik_van[id]['exp_max']
            
            useky.append({'start': rj, 'end': rj + pj, 'stroj': item})
            
            # je potreba useky projit a nastavit precedence v ramci produktu, aby nektere - pokud jsou - nebezely zaraz na stejne vane
            m_index = 0  # index v ramci m, pokud te zajima prava polozka tak je to m_index+1
            for left,right in zip(useky[:-1], useky[1:]):
                
                # pokud ten co ma nasledovat za nim prekryva cas, posun ho
                if right['start'] < left['end']:
                    delta = left['end'] - right['start']
                    right['start'] += delta
                    right['end'] += delta
                   
                try:
                    # predchazejici uzel, muze byt v jine vane
                    prev = m[m_index+1].prev.prev                   
                    # pokud by se ta operace nevesla do mezery mezi temi co jsi posunul, musis zvetsit mezeru
                    if slovnik_van[prev.id_stroj]['exp_max'] > right['start'] - left['end']:
                        delta = left['end'] + slovnik_van[prev.id_stroj]['exp_max'] - right['start']
                        right['start'] += delta
                        right['end'] += delta
                
                except AttributeError:
                    pass                
                
                m_index += 1
            
        return useky  
