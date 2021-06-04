'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

f = open('../log.log', 'r')

slovnik_funkci = {}

# projdi soubor a ukladej hromadne casy
for line in f:
    
    # vytvor seznam hodnot
    fun, t = line.split("\t")
    
    # pokud funkce jeste neni ve slovniku
    if fun in slovnik_funkci:
        slovnik_funkci[fun][1] += float(t)
        slovnik_funkci[fun][0] += 1
        
    else:
        slovnik_funkci[fun] = [0,0]
        slovnik_funkci[fun][1] = float(t)
        slovnik_funkci[fun][0] = 1
        
f.close()

for k,v in sorted(slovnik_funkci.items(), key = lambda x: x[1], reverse=True):
    
    print(k , "\t" , v[0], "\t" , v[1])
    
