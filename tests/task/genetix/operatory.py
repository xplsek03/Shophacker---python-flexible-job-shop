'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from pymoo.model.crossover import Crossover
from pymoo.model.mutation import Mutation
from pymoo.model.duplicate import ElementwiseDuplicateElimination
import numpy as np
import copy
import random


'''
pymoo subclass: operator krizeni
'''
class Krizeni(Crossover):
    
    
    def __init__(self):

        '''
        vychozi pravdepodobnost krizeni: 0.9
        2 = pocet rodicu
        2 = pocet potomku
        '''
        super().__init__(2, 2)


    '''
    samotne provedeni provedeni krizeni clenu A a B
    
    @param problem - instance optimalizacniho problemu pymoo
    @param syn - potomek
    @param otec - rodic
    '''
    def crossover(self, problem, syn, otec):

        # vyber typ ktery budes krizit - namaceni nebo transprty
        typ = 'transporty'
        
        # pokud bylo mozne sestavit uplny graf G' syna
        if problem.bads[syn['id']] == 1:
                
            if random.randrange(0,2):
                typ = 'namaceni'
        
        # pokud bylo mozne sestavit pouze jednoduchy graf G syna
        elif problem.bads[syn['id']] == 16:
            typ = 'namaceni'
                            
        # bod krizeni, nemel by byt uplne na kraji
        bod = random.randrange(2, len(otec[typ]) - 2)

        # vyber stranu otce, ze ktere budes brat poradi operaci
        left = True
        if random.randrange(0,2):
            left = False            

        # vytvor seznam operaci otce z te strany            
        product_list_parent = []
        for i, item in enumerate(otec[typ][:bod] if left else otec[typ][bod:]):
            product_list_parent.append(item.id_produkt)

        # seznam, do ktereho budes ukladat prehozenou cast syna
        swap = []
        
        # seznam operaci syna - ta cast kterou budes prehazovat
        operations = syn[typ][:bod] if left else syn[typ][bod:]
        
        # prochazis seznam ids otce
        for j, id in enumerate(product_list_parent):
            
            # jestli byla nalezena operace se stejnym id - v synovi
            found = False
            
            # projdi postupne vzdy znovu seznamem operaci
            for i, op in enumerate(operations):
                
                # pokud najdes operaci se stejnym id
                if op.id_produkt == id:
                    found = True
                    # pridej ji
                    swap.append(op)
                    operations.pop(i)
                    break                    
                
            # pokud dojel nakonec a nenasel tenhle prvek, pridej ten prvni co zbyva v operations
            if not found:
                swap.append(operations[0])
                operations.pop(0)
        
        # nahrad upravene casti syna
        syn[typ] = [*syn[typ][bod:], *swap] if left else [*swap, *syn[typ][:bod]]
        

    '''
    operator krizeni - pymoo
    
    @param problem - instance optimalizacniho problemu
    @param X - numpy pole, obsahujici cleny kteri maji byt spolu krizeni
    @return numpy pole stejneho tvaru jako X, obsahujici nove jedince
    '''
    def _do(self, problem, X, **kwargs):
       
        # n_parents - pocet rodicu ke krizeni
        # n_matings - pocet krizeni ke kterym ma dojit
        # n_var - pocet promennych v ramci jednoho reseni
        _, n_matings, _ = X.shape

        # Vystupem je (n_offsprings, n_matings, n_var): tedy stejny tvar jako X
        Y = np.full_like(X, None, dtype=object)

        # kazde krizeni ke kteremu ma dojit
        for k in range(n_matings):
            
            # ziskani rodicu
            a, b = X[0, k, 0], X[1, k, 0]         
            
            # zaloz potomky, ty budes modifikovat podle druheho rodice
            syn_a = copy.deepcopy(a)
            syn_b = copy.deepcopy(b)
            
            # proved samotne krizeni
            self.crossover(problem, syn_a, b)
            self.crossover(problem, syn_b, a)
            
            # uloz nove potomky
            Y[0, k, 0], Y[1, k, 0] = syn_a, syn_b
            
        return Y
    

'''
pymoo subclass - operator mutace
'''
class Mutace(Mutation):
    
    
    def __init__(self):
        super().__init__()


    '''
    provedeni mutace zmenou poradi
    
    @param x - mutovany jedinec
    @param problem - instance problemu
    '''
    def mutate_order(self, x, problem):
        
        # s polovicni pravdepodobnosti mutuj namaceni
        if random.randrange(2):

            y = x['namaceni']
            ids = [i.id_produkt for i in y if not i.prev]
        
        else:
            y = x['transporty']
            ids = [i.id_produkt for i in y if not i.prev.prev]
        
        # mutuj zvoleny pocet prvku
        for i in range(problem.konfig['mutace_order_pocet']):
        
            # vyber nahodne id
            id = ids[random.randrange(0, len(ids))]
            
            # vyfiltrovane operace jednoho produktu - s timto id
            filtered = [i for i in y if i.id_produkt == id]
            
            # vytyc bod odkud budes vkladat tyhle operace
            bod = random.randrange(0, len(y))
            
            # od tohoto bodu vkladej na random umisteni tyto operace
            for f in filtered:
                
                # vyhod ten prvek ven a vloz ho na pozici bod
                y.insert(bod, y.pop(y.index(f)))
                
                # stanov nasledujici bod 
                bod = random.randrange(bod + 1, max(len(y), bod + 2))
                # bod = random.randrange(bod + 1, bod + random.randrange(2, 5) )
    
            
    '''
    provedeni mutace zmenou prvku

    @param x - mutovany jedinec
    @param problem - instance problemu    
    '''
    def mutate_change(self, x, problem):
        
        # s polovicdni pravdepodobnosti resis namaceni
        if random.randrange(2):
            
            # pravdepodobnost zmeny prvku
            p = min(len(x['namaceni']), problem.konfig['mutace_single_pocet_namaceni']) / len(x['namaceni'])
                
            # vytvor seznam prvnich prvku pokud budes resit namaceni    
            first = [o for o in x['namaceni'] if not o.prev]    
            
            # projed postupne prvek po prvku
            for op in first:
            
                # pocitadlo poradi v produktu
                produkt_index = 0
                
                # projed kazdy produkt
                while 1:
                    
                    if np.random.random() > p:
                        
                        # proved zmenu vany
                        seznam_kroku = problem.slovnik_produktu[op.id_ve_slovniku]['kroky'][produkt_index]
                        op.id_stroj = seznam_kroku[random.randrange(len(seznam_kroku))]
                        
                    # skoc na dalsi prvek
                    if op.next:
                        op = op.next.next
                    else:
                        break
                    produkt_index += 1
            
        # resis transporty
        else:
    
            # pravdepodobnost zmeny
            p = min(len(x['transporty']), problem.konfig['mutace_single_pocet_transporty']) / len(x['transporty'])
            
            # prochazej postupne vsechny prvky
            for i, item in enumerate(x['transporty']):
                
                # pokud vyjde pravdepodobnost zmeny
                if np.random.random() > p:
                    
                    # zmena jerabu
                    item.id_stroj = problem.jeraby[random.randrange(len(problem.jeraby))]
        
    
    '''
    pymoo subclass - operator mutace
    
    @param problem - instance problemu
    @param X - numpy pole obsahujici jedince
    '''
    def _do(self, problem, X, **kwargs):
        
        # pro kazdeho jedince postupne proved
        for i in range(len(X)):
            
            r = np.random.random()
            
            # zpravdepodobnost zmeny poradi prvku - prehazeni poradi
            if r < problem.konfig['mutace_order']:
                
                '''
                print('MUT ORDER')
                
                for x in X[i, 0]['namaceni']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print(" || ", end = "")
                for x in X[i, 0]['transporty']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print("")
                '''
                
                # mutace zmenou poradi
                self.mutate_order(X[i, 0], problem)

                '''
                for x in X[i, 0]['namaceni']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print(" || ", end = "")
                for x in X[i, 0]['transporty']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print("")
                '''
                
            # pravdepodobnost nahodne zmeny v prvku
            elif r < (problem.konfig['mutace_order'] + problem.konfig['mutace_single']):
                
                '''
                print('MUT CHANGE')
                
                for x in X[i, 0]['namaceni']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print(" || ", end = "")
                for x in X[i, 0]['transporty']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print("")
                '''
                
                # mutace zmenou prvku
                self.mutate_change(X[i, 0], problem)                       
                   
                '''
                for x in X[i, 0]['namaceni']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print(" || ", end = "")
                for x in X[i, 0]['transporty']:
                    print(str(x.id_stroj)[-2:], end=" ")
                print("")
                '''
        return X
    
'''
pymoo subclass - operator deduplikace
'''
class Deduplikace(ElementwiseDuplicateElimination):
    
    
    '''
    metoda stanovuje, zda je vykrizeny jedinec uz obsazen v momentalni populaci
    '''
    def is_equal(self, a, b):     
        
        # stejny prvek znamena stejne transporty i stejne namaceni        
        return [i.id_produkt for i in a.X[0]['namaceni']] == [i.id_produkt for i in b.X[0]['namaceni']] and [i.id_produkt for i in a.X[0]['transporty']] == [i.id_produkt for i in b.X[0]['transporty']]   
  






    
'''
STARE 
dead evangelions   

def cross_type(self, otec, syn, count, typ):
     
     a_list = []
     
     # projed postupne pocet prvku
     while len(a_list) != count:
          
          # vyber x prvku, ktery budes radit podle a: <0; len-1>
          n = random.randrange(0, len(otec[typ]))

          if otec[typ][n].id_produkt not in a_list:
               a_list.append(otec[typ][n].id_produkt)
     
     # projed postupne po jednotlivem ID
     for id in a_list:
          
          # vyber ze syna seznam prvku s timto id: to jsou prvky co je budes vkladat do noveho seznamu
          tosort = [e for e,o in enumerate(syn[typ]) if o.id_produkt == id]
          
          # indexy polozek co maji byt zarazeny na konkretnim miste - dle A
          a_indexes = [otec[typ].index(o) for o in otec[typ] if o.id_produkt == id]
          
          #print('PREDTIM:')
          #print(len(syn[typ]))
          
          # projdi indexy obracene
          for op, i in zip(reversed(tosort), reversed(a_indexes)):
               # vezmi prvek a hod ho na to umisteni
               syn[typ].insert(i, syn[typ].pop(op))

          #print('NOVA DELKA:')
          #print(len(syn[typ]))
          

# NOW: fakticke provedeni crossoveru
def crossover(self, syn, otec, count, bads):

     # jed podle hodnoty BAD u chromozomu
     if bads[syn['id']] == 1:
     
          if random.randrange(0, 2):
               self.cross_type(otec, syn, 1, 'namaceni')
          else:
               self.cross_type(otec, syn, 1, 'transporty')          
          
     elif bads[syn['id']] == 5:
          self.cross_type(otec, syn, 2, 'transporty')
          
     else:
          self.cross_type(otec, syn, 2, 'namaceni')
'''

'''
# zatim konstanta, uloz do parametru skriptu
#count = 2
# bacha, jedes podle a a b - ty zustanou v originalnim poradi
#self.crossover(syn_a, b, count, problem.bads)
#self.crossover(syn_b, a, count, problem.bads)
'''
