'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import matplotlib.pyplot as plt
from random import randrange


'''
Testovaci trida pro zobrazeni ganttova diagramu pri provadeni SBH.
@param clen - clen populace
@param slovnik_van
@param slovnik_produktu
'''
def beautiful_gantt(clen, slovnik_van, slovnik_produktu):
    
    # obecne nastaveni obrazku
    fig, gnt = plt.subplots()
    gnt.set_xlabel('s')
    gnt.set_ylabel('Vana')
    gnt.set_yticks([15 + 10 * x for x in range(len(slovnik_van))])
    gnt.grid(True)
    
    # nastav popisky podle stroju
    gnt.set_yticklabels([str(x) for x in range(len(slovnik_van))])
    # nastav barvy jednotlivych jobu a transportu
    operation_colors = ['palegreen', 'lightcoral', 'mediumorchid',  'lightgrey', 'blue', 'lightyellow']
    transport_colors = ['yellow']
    
    # pole ids produktu - pro zvoleni barvy
    ids_produktu = [i.id_produkt for i in clen['namaceni'] if not i.prev]
            
    # vykresli vsechny operace namaceni
    for item in clen['namaceni']:
        gnt.broken_barh([(item.start, item.end - item.start)], (5 + ids_produktu.index(item.id_produkt) * 1 + 10 * slovnik_van[item.id_stroj]['position'], 1), facecolors=(operation_colors[ids_produktu.index(item.id_produkt)]))
    
    # 
    for transport in clen['transporty']:
        gnt.broken_barh([(transport.start, transport.end - transport.start)], (8 + 1 * ids_produktu.index(transport.prev.id_produkt) + 10 * slovnik_van[transport.prev.id_stroj]['position'], 1), facecolors=(transport_colors[randrange(len(transport_colors))]))
    
    plt.show()
    #plt.savefig('images/' + secrets.token_hex() + '.png')
    plt.close()
