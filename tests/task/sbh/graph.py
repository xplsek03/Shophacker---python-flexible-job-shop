'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import networkx as nx
import bellmanford as bf
import copy
from task.output.timer import timer 


'''
Obsahuje funkce pro praci s disjunktivnim grafem G/G'.
'''
class Graph:
    
    
    '''
    Bellman-Forduv algoritmus pro kontrolu pozitivnich cyklu a nalezeni nejdelsi cesty.
    @param graf - G/G'
    @param node_from - vychozi pocatecni uzel odkud ma cesta vest
    @param node_to - vychozi koncovy uzel kam ma cesta vest
    @return (None, True) v pripade pozitivniho cyklu, (cmax, False) jinak
    '''
    def bellman(graf, node_from="start", node_to="end"):
        
        # nalezeni nejdelsi cesty
        delka, uzly, pozitivni_cyklus = bf.bellman_ford(graf, node_from, node_to, weight='weight')
            
        # pokud nalezen cyklus, vratit
        if pozitivni_cyklus:
            return (None, True)
        
        # vypocet cmax
        cmax = 0
        for left, right in zip(uzly[:-1], uzly[1:]):
            cmax += graf[left][right][0]['weight']
            
        return (-cmax, False)   

    '''
    Pridej do uplneho grafu disjunktivni spojnice naplanovanych stroju.
    @param graf
    @param harmonogram - slovnik harmonogramu ve formatu stroj: [seznam operaci]
    @param slovnik_van
    @param slovnik_jerabu
    '''
    def add_disj_from_simple(graf, harmonogram, slovnik_van, slovnik_jerabu):
        # projdi harmonogramy namaceni
        for m_id, m in harmonogram.items():
            # postupne pridej disjunktivni spojnice namaceni tak, aby vedly pres ten jeho nasledujici prvek (transport nebo fake node)
            for left,right in zip(m[:-1], m[1:]):
                if not left.next:
                    # V2 - pokud bude potreba zvetsit mezeru, tak sem dej slovnik_van[right.id_stroj]['dive']
                    hodnota = 0
                # V2 - ty spojnice maji hodnotu rl + drain toho produktu co tam je + rl toho produktu co tam bude
                else:
                    hodnota = slovnik_van[left.id_stroj]['drain'] + slovnik_jerabu[left.next.id_stroj]['raise_low'] + slovnik_van[right.id_stroj]['dive']
                graf.add_edge(left.next.graphid if left.next else 'fake' + left.graphid, right.graphid, weight=-hodnota)
    
    
    '''
    Update clena populace z dat odvozenych z disjunktivniho grafu.
    @param graf
    '''
    def update_clen_graf(graf):
        for n in list(graf.nodes(data=True)):
            if n[0] != 'end' and n[0] != 'start' and 'fake' not in n[0]:
                # vygeneruj z grafu rj
                rj,_ = Graph.bellman(graf, 'start', n[0])
                # nastav rj u operace
                n[1]['obj'].start = rj


    '''
    Pridani ziskanych disjunktivnich spojnic do grafu - ze seznamu useku.
    @param graf - G/G'
    @param useky - seznam casovych useku, vygenerovanych pomoci EDD
    @param slovnik_van
    @param slovnik_jerabu
    @param simple - True pokud G, False pokud G'
    '''
    def add_disjunctive(graf, useky, slovnik_van, slovnik_jerabu, simple):
        
        # vytvor seznam hran
        for left, right in zip(useky[:-1], useky[1:]):
            if simple:
                # davas exp_max
                graf.add_edge(left['stroj'].graphid, right['stroj'].graphid, weight=-slovnik_van[left['stroj'].id_stroj]['exp_max'])
            else:   
                
                # pridavas hodnotu transportu left T + empty travel z left.next N do right.prev N
                hodnota = slovnik_jerabu[left['stroj'].id_stroj]['raise_low'] + slovnik_van[left['stroj'].prev.id_stroj]['drain'] + slovnik_jerabu[left['stroj'].id_stroj]['raise_high'] + \
                        slovnik_jerabu[left['stroj'].id_stroj]['move'] * abs(slovnik_van[left['stroj'].prev.id_stroj]['position'] - slovnik_van[left['stroj'].next.id_stroj]['position']) + \
                        slovnik_van[left['stroj'].next.id_stroj]['dive'] + slovnik_jerabu[left['stroj'].id_stroj]['raise_high'] + \
                        slovnik_jerabu[left['stroj'].id_stroj]['empty_move'] * abs(slovnik_van[right['stroj'].prev.id_stroj]['position'] - \
                        slovnik_van[left['stroj'].next.id_stroj]['position']) + slovnik_van[right['stroj'].prev.id_stroj]['dive']
                        
                graf.add_edge(left['stroj'].graphid, right['stroj'].graphid, weight=-hodnota)
                
        
    '''
    Odstraneni ziskanych disjunktivnich spojnic do grafu - ze seznamu useku.
    @param graf
    @param useky - seznam casovych useku
    '''
    def remove_disjunctive(graf, useky):
        # vytvor seznam hran
        for left,right in zip(useky[:-1], useky[1:]):
                graf.remove_edge(left['stroj'].graphid, right['stroj'].graphid)


    '''
    Reparacni krok 4 u SBH.
    @param graf
    @param useky - seznam casovych useku
    @param slovnik_van
    @param slovnik_jerabu
    @param simple - True pokud G, False pokud G'
    @return cmax nebo None
    '''
    def sbh_reparation(graf, useky, slovnik_van, slovnik_jerabu, simple):
    
        # projdi kazdy usek
        for index, usek in enumerate(useky):
            # v i je ted pozice polozky se kterou muzes menit 
            for i in range(usek['lb'], usek['ub'] + 1):
                # pokud polozka se kterou chces menit umoznuje vymenu, resp index spada do intervalu <lb;ub> te polozky
                if useky[i]['lb'] <= index <= useky[i]['ub']:
                    # vyrob kopii
                    useky_copy = copy.deepcopy(useky)
                    # swapni oba prvky
                    useky_copy[index], useky_copy[i] = useky_copy[i], useky_copy[index]
                    # proved vlozeni sekvence
                    Graph.add_disjunctive(graf, useky_copy, slovnik_van, slovnik_jerabu, simple)
                    # otestuj na B-F
                    cmax, pozitivni_cyklus = Graph.bellman(graf, node_from="start", node_to="end")
                    if not pozitivni_cyklus:
                        return cmax
                    # odeber sekvenci z grafu
                    Graph.remove_disjunctive(graf, useky_copy)
        # nepodarilo se opravit
        return None
    
          
    '''
    Konstrukce jednoducheho grafu G.
    @param clen - clen populace
    @param slovnik_van
    @return graf G
    '''
    def simple_graph(clen, slovnik_van):

        # zacni stavet graf pro clena
        G = nx.MultiDiGraph()  # G = C U Vm U fakenodes
        G.add_node("start")
        
        # pridej postupne Vm a zaroven hrany C
        for prvek in clen['namaceni']:
            
            # pokud je to prvni namoceni, pokracuj
            if not prvek.prev:
                
                # vytvor pocatecni uzel namaceni, napoj ho na start
                G.add_node(prvek.graphid, obj=prvek)
                G.add_edge("start", prvek.graphid, weight=0)
                in_namaceni = True
                                
                # pokud existuje dalsi
                while prvek.next:
                    
                    # prepni se na tento prvek
                    prvek = prvek.next
                    in_namaceni ^= 1
                    
                    # pokud je na transportu, prepni
                    if not in_namaceni:
                        continue
                    
                    # vloz uzel tykajici se tohoto prvku namaceni
                    G.add_node(prvek.graphid, obj=prvek)
                    # provazuj tento uzel namaceni s predchozim namacenim o 2 uzly zpet
                    G.add_edge(prvek.prev.prev.graphid, prvek.graphid, weight=-slovnik_van[prvek.prev.prev.id_stroj]['exp_min'])
                    G.add_edge(prvek.graphid, prvek.prev.prev.graphid, weight=slovnik_van[prvek.prev.prev.id_stroj]['exp_max'])
                    
                    # pokud se jedna o posledni prvek
                    if not prvek.next:
                        # pridej fakenode a navaz na nej posledni operaci, coz je namaceni
                        # fakenode ma nazev: "fake" + graphid operace co na nej ukazuje. Takhle je jednodussi odvodit si jeho nazev, nikdo jiny k nemu totiz pristupovat primo nebude
                        G.add_node("fake" + prvek.graphid, obj=None)
                        G.add_edge(prvek.graphid, "fake" + prvek.graphid, weight=-slovnik_van[prvek.id_stroj]['exp_min'])
                        G.add_edge("fake" + prvek.graphid, prvek.graphid, weight=slovnik_van[prvek.id_stroj]['exp_max'])                        
                        break
                    
        # pridej koncovy uzel a napoj vsechny fakenodes na nej
        G.add_node("end", obj=None)
        for i in [p for p in clen['namaceni'] if not p.next]:
            G.add_edge("fake" + i.graphid, "end", weight=0)       

        return G
    

    '''
    Konstrukce uplneho grafu G'.
    @param clen - clen populace
    @param slovnik_van
    @return graf G'
    '''
    def full_graph(clen, slovnik_van, slovnik_jerabu, simple_g):

        # zacni stavet graf pro clena
        G = nx.MultiDiGraph()  # G = C U Vm U Vt U Dm (Dm pouze prvniho stroje)
        G.add_node("start")
        
        # pridej postupne Vm, Vt a zaroven hrany C
        for prvek in clen['namaceni']:
            
            # pokud je to prvni namoceni, pokracuj
            if not prvek.prev:
                
                # vytvor pocatecni uzel namaceni, napoj ho na start
                G.add_node(prvek.graphid, obj=prvek)
                G.add_edge("start", prvek.graphid, weight=0)
                in_namaceni = False
                                
                # pokud existuje dalsi
                while prvek.next:

                    # prepni se na tento prvek
                    prvek = prvek.next
                    
                    # vloz uzel tykajici se THIS prvku
                    G.add_node(prvek.graphid, obj=prvek)
                    
                    # provazuj tento uzel s predchozim
                    if in_namaceni:
                        # resis transport z predchoziho uzlu transportu na tento uzel namaceni
                        cas = slovnik_jerabu[prvek.prev.id_stroj]['raise_low'] + slovnik_van[prvek.prev.prev.id_stroj]['drain'] + \
                        slovnik_jerabu[prvek.prev.id_stroj]['raise_high'] + \
                        slovnik_jerabu[prvek.prev.id_stroj]['move'] * abs(slovnik_van[prvek.prev.prev.id_stroj]['position'] - slovnik_van[prvek.id_stroj]['position']) + \
                        slovnik_van[prvek.id_stroj]['dive']
                        G.add_edge(prvek.prev.graphid, prvek.graphid, weight=-cas)
                        G.add_edge(prvek.graphid, prvek.prev.graphid, weight=cas) 
                    else:
                        # budes resit namaceni z predchoziho uzlu na tento
                        G.add_edge(prvek.prev.graphid, prvek.graphid, weight=-slovnik_van[prvek.prev.id_stroj]['exp_min'])
                        G.add_edge(prvek.graphid, prvek.prev.graphid, weight=slovnik_van[prvek.prev.id_stroj]['exp_max'])
                    
                    # pokud se jedna o posledni prvek
                    if not prvek.next:
                        # pridej fakenode a navaz na nej posledni operaci, coz je namaceni
                        # fakenode ma nazev: "fake" + graphid operace co na nej ukazuje. Takhle je jednodussi odvodit si jeho nazev, nikdo jiny k nemu totiz pristupovat primo nebude
                        G.add_node("fake" + prvek.graphid, obj=None)
                        G.add_edge(prvek.graphid, "fake" + prvek.graphid, weight=-slovnik_van[prvek.id_stroj]['exp_min'])
                        G.add_edge("fake" + prvek.graphid, prvek.graphid, weight=slovnik_van[prvek.id_stroj]['exp_max'])                        
                        break
                        
                    in_namaceni ^= 1
                    
        # pridej koncovy uzel a napoj vsechny fakenodes na nej
        G.add_node("end", obj=None)
        for i in [p for p in clen['namaceni'] if not p.next]:
            G.add_edge("fake" + i.graphid, "end", weight=0)

        return G
