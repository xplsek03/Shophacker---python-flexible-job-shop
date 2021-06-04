'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

'''
Funkce vypocita hodn. obj. f. Storage u jednoducheho grafu G.
@param clen - clen populace
@param slovnik_van
@return hodnota Storage
''' 
def calculate_simple_storage(clen, slovnik_van):
    # hodnota Storage
    storage = 0
    # vezmi pocatecni prvky
    products = [i.id_produkt for i in clen['namaceni'] if not i.prev]
    # projdi postupne po kazdem id produktu
    for p in products:
        # vyrob seznam operaci v kazdem produktu
        filtered = [o for o in clen['namaceni'] if o.id_produkt == p]
        # projdi postupne rozdily intervalu
        for left,right in zip(filtered[:-1], filtered[1:]):            
            # tady vypocitej jestli je mezera mezi nima vetsi nez rozdil mezi exp_max a exp_max
            delta = slovnik_van[left.id_stroj]['exp_max'] - slovnik_van[left.id_stroj]['exp_min']
            # mezera mezi zacatkem a koncem
            hole = right.start - left.end
            # pokud je mezera vetsi nez 0 a jestli je rozdil takovy aby prekrocil maximalni moznou dobu ulozeni
            if hole > 0 and hole > delta:
                storage += abs(hole)
    return storage


'''
Funkce vypocita hodn. obj. f. Storage u uplneho grafu G'.
@param clen - clen populace
@param slovnik_van
@return hodnota Storage
''' 
def calculate_full_storage(clen, slovnik_van):

    # objective Storage - vypocet
    storage = 0
    
    # prochazej vany a zaroven delej transporty jejich operaci a navaznosti operaci v ramci tech van
    products = [i.id_produkt for i in clen['namaceni'] if not i.prev]
    for p in products:
        filtered = [o for o in clen['namaceni'] if o.id_produkt == p]
        for left,right in zip(filtered[:-1], filtered[1:]):

            if left.next:
                if left.next.start > left.end:
                    # pokud existuje mezera mezi operaci a jejim nasledujicim transportem
                    storage += abs(left.next.start - left.end)  
                # pokud existuje presah do nasledujiciho transportu
                elif left.next.start < left.end:
                    storage += abs(left.end - left.next.start)
            
    # pokud jses v jedne vane a hodis tam hned po tehle operaci dalsi operaci, tahle predchozi operace neni posledni a transport sem te nove a transport tehle stare probiha na stejnem jerabu: nekompatibilni
    for v in list(slovnik_van):
        ops = [i for i in clen['namaceni'] if i.id_stroj == v]
        # projdi operace na jedne vane
        for left, right in zip(ops[:-1], ops[1:]):
            # pokud leva operace prekryva castecne pravou
            if left.end > right.start:
                storage += abs(left.end - right.start)
            # pokud na sebe navazuji
            elif left.end == right.start:
                # pokud leva neni posledni, prava neni prvni a transporty probihaji na stejnem jerabu
                if left.next and right.prev and (left.next.id_stroj == right.prev.id_stroj):
                    # zatim pricti delku toho transportu co jde do teto vany
                    storage += abs(right.prev.end - right.prev.start)
    return storage
   
 
'''
Proved vytvoreni oken u clena populace, data jsi ziskal z jednoducheho grafu
@param clen - clen populace
@param slovnik_van
'''
def simple_windowing(clen, slovnik_van):
     
    products = [c for c in clen['namaceni'] if not c.prev]
    for op in products:
      
        while op:
            if op.next:
                op.end = op.next.start
            else:
                op.end = op.start + slovnik_van[op.id_stroj]['exp_min']
            op = op.next

     
'''
Proved vytvoreni oken u clena populace, data jsi ziskal z uplneho grafu
@param clen - clen populace
@param slovnik_van
@param slovnik_jerabu
'''
def full_windowing(clen, slovnik_van, slovnik_jerabu):
     
    # tady je jistota ze starty jsou nastavene dobre, nastav ale jeste dobu trvani
    products = [c for c in clen['namaceni'] if not c.prev]
    # postupne posouvej produkty
    for op in products:
       
        trans = False

        while op:
               
            if trans:
                op.end = op.next.start
            else:
               # vezmi end z toho dalsiho prvku co nasleduje v produktu                             
               if op.next:
                   op.end = op.next.start
               # vezmi min expozici ve vane
               else:
                   op.end = op.start + slovnik_van[op.id_stroj]['exp_min']
     
            # prejdi na dalsi operaci
            trans ^= 1
            op = op.next 
