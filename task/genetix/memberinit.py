'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import numpy as np
from pymoo.model.sampling import Sampling
from task.classes import Namaceni, Transport
import random
import secrets


'''
pymoo subclass: odpovida za inicializaci jedincu v ramci uvodni populace
'''
class Memberinit(Sampling):


    '''
    randomizace poradi seznamu namaceni a transportu v chromozomu
    
    @param seznam - cast clena populace
    @param namaceni - jestli se jedna o namaceni nebo o transport
    @return nove serazeny seznam
    
    '''
    def lepsi_serazeni(self, seznam, namaceni=True):
        # tohle je seznam prvnich polozek
        if namaceni:
            first_items = [i for i in seznam if not i.prev]
        else:
            first_items = [i for i in seznam if not i.prev.prev]
        # tohle je nove vytvoreny seznam namaceni
        new_clen = []
        while len(first_items):
            # nahodne poradi
            r = random.randrange(len(first_items))
            # pridej do noveho clena nahodny prvek
            new_clen.append(first_items[r])
            if namaceni:
                first_items[r] = first_items[r].next
            else:
                first_items[r] = first_items[r].next.next
            # pokud uz tam dalsi neni, odstran ze seznamu
            if not first_items[r]:
                first_items.pop(r)                
        return new_clen
    

    '''
    generovani jednoho clena populace
    
    @param problem - instance pymoo Problem
    @param n_samples - pocet clenu populace
    @return numpy pole obsahujici uvodni populaci
    
    '''
    def _do(self, problem, n_samples, **kwargs):
        
        X = np.full((n_samples, 1), None, dtype=object)

        # generuj x clenu - muzes pouzit cokoliv z instance problemu
        for i in range(n_samples):

            # serad nahodne produkty jak maji jit za sebou
            random.shuffle(problem.seznam_produktu)
            
            # zpracovavas jednoho clena, ve kterem budou ulozene instance Transport a Namaceni vsech produktu v ramci nej
            clen_namaceni = []
            
            # projdi jeden produkt za druhym a podle toho generuj clena populace
            for produkt in problem.seznam_produktu:
                # do clena postupne pridavej jednotlive uzly, krome pocatecniho a koncoveho uzlu
                for j, krok in enumerate(problem.slovnik_produktu[produkt['id']]['kroky']):                
                    # vyber nahodnou vanu a pridej Namaceni do produktu
                    id_vana = krok[random.randrange(len(krok))]
                    clen_namaceni.append(Namaceni(id_produkt=produkt['uid'], id_stroj=id_vana, id_ve_slovniku=produkt['id']))
                
                # provaz next a prev mezi sebou, docasne: pouze pro ucely serazeni
                pocet_vlozenych = len(problem.slovnik_produktu[produkt['id']]['kroky'])
                nove_vlozene = clen_namaceni[len(clen_namaceni)-pocet_vlozenych:]
                for j, item in enumerate(nove_vlozene):  
                    # prvni polozka
                    if j != 0:
                        item.prev = nove_vlozene[j-1]
                    # posledni polozka
                    if j != (len(nove_vlozene) - 1):
                        item.next = nove_vlozene[j+1]   

            # tady musis cleny zamichat mezi sebou a srovnat to aby odpovidaly poradi kroku v ramci jednotlivych produktu                       
            clen_namaceni = self.lepsi_serazeni(clen_namaceni)

            # pridani operaci transportu a propojeni obou casti pomoci next a prev
            clen_transporty = []

            # na konci transport neni, posledni namaceni = vystupni misto neboli vana!
            for produkt in problem.seznam_produktu:
                # seznam operaci v jednom produktu
                filtered = list(filter(lambda x: (x.id_produkt == produkt['uid']), clen_namaceni)) 
                # projdi seznam vsech operaci po jednotlivejch produktech oddelene
                for j, operace in enumerate(filtered): 
                    
                    # vse krome posledni operace
                    if j < len(filtered) - 1:   
                        # instance transportu
                        transport = Transport(id_produkt=produkt['uid'], id_stroj=problem.jeraby[random.randrange(len(problem.jeraby))])
                        transport.prev = filtered[j]
                        transport.next = filtered[j+1]
                        # pokud ma operace neco predchoziho a neni to prvni operace, navaz to na posledni pridany transport
                        if operace.prev:
                            operace.prev = clen_transporty[-1]
                        # pokud ma mit dalsi v poradi, coz ma urcite protoze jsme vynechali posledni operaci
                        operace.next = transport
                        # vloz transport
                        clen_transporty.append(transport)
                    # jen posledni polozka, odkaz zpetne na posledni clen transportu
                    else:
                        operace.prev = clen_transporty[-1]       
            
            # V2 - over jestli je potreba
            # serazeni transportu, tak aby se nepredbihaly jednotlive transporty v ramci jednoho produktu
            clen_transporty = self.lepsi_serazeni(clen_transporty, namaceni=False)

            # tohle je plnohodnotny clen populace
            X[i, 0] = {'namaceni': clen_namaceni, 'transporty': clen_transporty, 'id': secrets.token_hex(16)}

        return X    
