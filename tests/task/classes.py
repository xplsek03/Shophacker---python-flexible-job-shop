'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace
'''

from secrets import token_hex


'''
Tridy reprezentuji operace v ramci chromozomu jedince - namaceni a transporty.
'''
class Operation(object):
    
    
    def __init__(self, *args, **kwargs):
        self.start = 0  # zacatek operace
        self.end = 0  # konec operace
        self.next = None  # dalsi operace v poradi, last = None
        self.prev = None  # predchozi operace, dulezite hlavne u transportu, ktere tim odkazuji na umisteni kam maji jet
        self.id_produkt = kwargs['id_produkt']  # ke kteremu produktu to nalezi
        self.graphid = token_hex(16)  # id polozky v grafech G a G'
        
    
# reprezentuje operaci namaceni ve vane
class Namaceni(Operation):
    
    def __init__(self, *args, **kwargs):
        super(Namaceni, self).__init__(*args, **kwargs)
        self.id_stroj = kwargs['id_stroj']  # tohle zdruzuje informace o vane, at se to zbytecne nekopiruje vickrat
        self.id_ve_slovniku = kwargs['id_ve_slovniku']  # id ktere teto operaci namaceni nalezi ve slovniku produktu - kvuli dohledani alternativnich van
        

# reprezentuje operaci prejizdeni od vany k vane
class Transport(Operation):

    def __init__(self, *args, **kwargs):
        super(Transport, self).__init__(*args, **kwargs)
        self.id_stroj = kwargs['id_stroj']  # V2 - slo by sloucit vse do Operation a nedelat subclass, je tu kvuli snadnejsimu debugu
        
