'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from task.bab.node import Node
import copy
#from task.output.timer import timer


'''
Obsahuje funkce pro provadeni metody branch and bound.
'''
class Edd:

    
    '''
    Provedeni metody branch and bound pro konkretni stroj.
    @param slovnik_van
    @param slovnik_jerabu
    @param graf - G/G'
    @param m - seznam operaci provadenych na stroji
    @param cmax
    @param is_namaceni - zda se jedna o vanu nebo o jerab
    @return instance uzlu obsahujici optimalni sekvenci operaci nebo None
    '''
    def branch_and_bound(slovnik_van, slovnik_jerabu, graf, m, cmax, is_namaceni=True):
        
        # DEBUG: seznam ids v ramci m. Dopredu uz to sem posli v tomhle formatu..
        m_ids = [i.graphid for i in m]   
        
        # vytvor uzel urovne 0
        this_node = Node()
        
        # stanov lowerbound - tuhle operaci delas jen pro ucely vypoctu lowerbound u 0 uzlu
        this_node.single_machine_planning(graf, cmax, slovnik_van, slovnik_jerabu, m, is_namaceni=is_namaceni)
        
        # nejlepsi uzel, ktery jsi zatim ziskal
        best_node = None
        
        while True:
            
            # konec hledani - bud chyba nebo uz neni co validniho rozgenerovat
            if not this_node:
                # vrat nejlepsi NEPREEMPTIVNI uzel nebo v horsim pripade None
                return best_node
            
            # ted jses na uzlu this_node, kam ses dostal budto stoupanim nebo rozgenerovanim
            
            # alternativni zpusob jak vytvaret seznam
            seznam = [k for k in m_ids if k not in this_node.planned]
            
            # vytvor poddane - tady vybiras z operaci ktere nejsou naplanovane
            for item in seznam:
                
                # kazdemu zaloz seznam naplanovanych a dej do nej tu jeho aktualni naplanovanou polozku
                potomek_planned = copy.deepcopy(this_node.planned)
                potomek_planned.append(item)
                    
                # zaloz uzel potomka s odkazem na nadrazeny uzel
                new_node = Node(planned=potomek_planned, father=this_node)

                # pridej ho do seznamu poddanych
                this_node.poddani.append(new_node)
                
                # na kazdem uzlu proved EDD
                new_node.single_machine_planning(graf, cmax, slovnik_van, slovnik_jerabu, m, is_namaceni=is_namaceni)                

                # pokud je uzel nepreemptivni, pomer s momentalnim best_node
                if new_node.is_ok and new_node.kriterium_A:
    
                    # pokud uz best node existuje, srovnej
                    if best_node and new_node.lmax < best_node.lmax: 
                        best_node = new_node
                    # best node jeste neexistuje, tak ho uloz jako best
                    else:
                        best_node = new_node
              
            # pokud se jedna o list, ber ho automaticky na test
            if len(seznam) == 1:
                selected_node = this_node
                
            # jedna se o nejaky meziuzel, tak vyber kterym pujdes dal
            else:
                
                # projdi potomky a hledej nejmensi lmax, jen kde je splneno kiterium C
                lmax_min = float("inf")
                selected_node = None
                
                # projdi potomky a pokracuj tim nejmensim co je validni, pokud splnuje kriterium C
                for item in this_node.poddani:

                    # vybirej jen z vetvi co splnuji kriterium C a zaroven jsou nizsi nez NEPREEMPTIVNI best_node, pokud teda ovsem existuje
                    if best_node and item.lmax > best_node.lmax:
                        item.is_ok = False
                        continue

                    # najdi postupne uzel s nejnizsim Lmax                    
                    if item.is_ok and (item.lmax < lmax_min):
                        lmax_min = item.lmax
                        selected_node = item
            
            # pokud sis vybral dalsi uzel
            if selected_node:
                        
                # pokud ses dostal na meziuzel
                if len(seznam) != 1:
                    this_node = selected_node
                # dostal ses na koncovy list, tak jdi zpatky nahoru
                else:
                    this_node = Edd.crawl_up(selected_node, best_node)
            
            # nevybral sis dalsi uzel, pokracuj ve stoupani nahoru
            else:
                this_node = Edd.crawl_up(this_node, best_node)


    '''
    Navrat z uzlu do vyssi urovne.
    @param node - aktualni uzel
    @param best_node - nejlepsi nalezeny nepreemptivni uzel
    @return cilovy uzel nebo None
    '''  
    def crawl_up(node, best_node):
        
        # dostal se az nahoru
        top = False
        
        # oznac ze uz jsi na tomto uzlu byl
        node.is_ok = False
        
        # dokud nenajdes otce co ma pouzitelne deti, bez nahoru a oznacuj otce jako nepouzitelne
        while 1:
            
            # pokud se dostal az do uzlu 0
            if not node.father:
                top = True
                
            # jeste neni v uzlu 0, tak stoupej nahoru
            else:
                node = node.father
                
            # pokud ma tento uzel pouzitelne dite, prejdi na nej
            for son in node.poddani:
                
                # pokud je mozne timto uzlem pokracovat
                if son.is_ok:
                    
                    # pokud to dite nesplnuje pozadavky na nejlepsi NEPREEMPTIVNI UZEL
                    if best_node and son.lmax > best_node.lmax:
                        son.is_ok = False
                
                    # jinak pokracuj timto synem
                    else:                    
                        return son
                
            # nenasel pouzitelny uzel, takze oznac tento otcovsky uzel jako nepouzitelny a pokracuj ve vzestupu
            node.is_ok = False
            
            # nenasel potomka v node zero, tzn. konec hledani
            if top:
                return None
        
