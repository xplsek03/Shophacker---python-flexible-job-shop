'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler, ContentMixin
import bson
from pymongo import DESCENDING
import random
from tornado.web import authenticated


# prehled historie, detail historie, delete zaznamu historie
class HistorieHandler(BaseHandler, ContentMixin):

    @authenticated
    def get(self, nazev=None):
 
        # detail nebo smazani
        if nazev:
         
            # najdi v db
            item = self.db["historie"].find_one({"_id": bson.ObjectId(nazev)})
            if item:
                
                # vytvor slovniky van a jerabu
                slovnik_jerabu = {}
                slovnik_van = {}
                # slovnik operaci v ramci reseni, aby se daly snadneji dohledat prv a nxt operace
                slovnik_result = {}
                
                if 'vysledek' in item:
                
                    # generovani
                    ids_van = set()
                    for op in item['vysledek']['namaceni']:
                        op['typ'] = 'namaceni'
                        slovnik_result[op['id']] = op
                        ids_van.add(op['stroj'])
                    ids_jerabu = set()
                    for op in item['vysledek']['transporty']:
                        op['typ'] = 'transport'
                        slovnik_result[op['id']] = op
                        ids_jerabu.add(op['stroj'])
                    # slovnik jerabu
                    jeraby = self.db['jeraby'].find({"_id": {"$in": list(ids_jerabu)}})
                    for jerab in jeraby:
                        slovnik_jerabu[jerab['_id']] = jerab
                    # slovnik van
                    vany = self.db['vany'].find({"_id": {"$in": list(ids_van)}})
                    for vana in vany:
                        slovnik_van[vana['_id']] = vana
    
                    # vytvor textove instrukce
                    instrukce = self.create_instrukce(item, slovnik_van, slovnik_jerabu, slovnik_result)
                    # vytvor podklady pro gnerovani ganttu
                    gantt_jeraby, gantt_vany, vany_nazvy, jeraby_nazvy, vany_barvy = self.create_gantt(item, slovnik_van, slovnik_jerabu, slovnik_result)
                
                    # serad slovnik_result
                    animace = [v for k, v in slovnik_result.items() if v['typ'] == 'transport' or not v['prev'] or not v['next']]
                    animace.sort(key=lambda x: x['start'])
                    
                    uvodni_operace_jerabu = []
                    # zaloz uvodni pozice jerabu, kam maji byt umisteny
                    for id, j in slovnik_jerabu.items():
                        for op in animace:
                            if op['typ'] == 'transport' and op['stroj'] == id:
                                uvodni_operace_jerabu.append(op)
                                break
                
                    # vezmi vychozi pozice na techto jerabech a vytvor seznam
                    for u in uvodni_operace_jerabu:
                        slovnik_jerabu[u['stroj']]['starting_position'] = slovnik_van[slovnik_result[u['prev']]['stroj']]['position']

                    self.render("zaznam_detail.html", item=item, instrukce=instrukce, 
                                gantt_jeraby=gantt_jeraby, gantt_vany=gantt_vany, 
                                vany_nazvy=vany_nazvy, jeraby_nazvy=jeraby_nazvy, slovnik_jerabu=slovnik_jerabu, 
                                slovnik_van=slovnik_van, slovnik_result=slovnik_result, 
                                vany_barvy=vany_barvy, animace=animace)
                
        else:
            # ziskej seznam z db
            items = self.db["historie"].find(sort=[('_id', DESCENDING)])
            self.render("historie.html", items=items)

    @authenticated
    def post(self, id=None):

        # id je pouzito v action formulare, kde je vic tlacitek

        # smaz vse
        if self.get_argument('delete-all', None) is not None:
            self.db['historie'].delete_many({})

        # smazani nedokoncenych uloh
        if self.get_argument('delete-not-finished', None) is not None:
            self.db['historie'].delete_many({'vysledek': {'$exists': False}})

        # kliknul na DELETE
        elif self.get_argument('delete', None) is not None:
            self.db['historie'].delete_one({'_id': bson.ObjectId(id)})

        # presmeruj ho na seznam van
        self.redirect("/historie")


    # vytvor podklady pro ganttuv diagram
    def create_gantt(self, item, slovnik_van, slovnik_jerabu, slovnik_result):
                        
        # seznam pouzitelnych barev
        barvy_n = ["#00dc72","#6d33b8","#66bf2a","#bd56dd","#00870d","#3172fc","#c2cf2b","#018cff","#d67500","#0bc7ff","#9e2505","#02d2c6","#ff426c",
                    "#00744c","#ff60c7","#475913","#ef93ff","#bf8000","#3c4e93","#ffa354","#b50087","#abd19b","#c60049","#dac581","#ff6896","#aa8058",
                    "#7b6697","#ffa57d","#8f333c","#e1a0c3"]
        barvy_t = ["orange", "green", "red", "blue", "yellow", "pink", "black", "gray"]
        random.shuffle(barvy_n)
        random.shuffle(barvy_t)
        
        # aby se dal dohledat nazev produktu, kvuli ganttu
        slovnik_produktu = {}
        for i in item['produkty']:
            slovnik_produktu[i['id']] = i['nazev']
        
        # seznam jednotlivych van, podle kterych se udelaji pozice odshora ganttu
        vany_barvy = {}
        vany_pozice = {}
        vany_nazvy = {}
        i = 0
        j = 0
        for op in item['vysledek']['namaceni']:
            if op['productid'] not in vany_barvy:
                try:
                    vany_barvy[op['productid']] = barvy_n[i]
                except IndexError:
                    vany_barvy[op['productid']] = barvy_n[i - len(barvy_n)]
                i += 1
            if op['stroj'] not in vany_pozice:
                vany_nazvy[slovnik_van[op['stroj']]['sign']] = j * 50 + 5
                vany_pozice[op['stroj']] = j * 50
                j += 1
        
        # seznam jednotlivych jerabu, podle kterych se udelaji pozice odshora ganttu
        jeraby_barvy = {}
        jeraby_pozice = {}
        jeraby_nazvy = {}
        i = 0
        j = 0
        for op in item['vysledek']['transporty']:
            if op['stroj'] not in jeraby_barvy:
                jeraby_barvy[op['stroj']] = barvy_t[i]
                i += 1
            if op['stroj'] not in jeraby_pozice:
                jeraby_nazvy[slovnik_jerabu[op['stroj']]['sign']] = j * 50 + 5 + 20
                jeraby_pozice[op['stroj']] = j * 50
                j += 1
                
        # vytvor slovniky pro generovani casti grafu
        parts_vany = []
        for op in item['vysledek']['namaceni']:
            part = {'id': op['id'], 'nazev_produktu': slovnik_produktu[op['id_ve_slovniku']], 'sign': slovnik_van[op['stroj']]['sign'], 
                    'nazev': slovnik_van[op['stroj']]['nazev'], 'start': op['start'], 'end': op['end'], 
                    'left': 1000 * op['start'] / item['vysledek']['cmax'], 'width': 1000 * op['end'] / item['vysledek']['cmax'] - 1000 * op['start'] / item['vysledek']['cmax'], 
                    'color': vany_barvy[op['productid']], 'productid': op['productid'], 'position': vany_pozice[op['stroj']]}
            parts_vany.append(part)     

        parts_jeraby = []
        for op in item['vysledek']['transporty']:
            part = {'id': op['id'], 'nazev': slovnik_jerabu[op['stroj']]['nazev'], 'sign': slovnik_jerabu[op['stroj']]['sign'], 
                    'start': op['start'], 'end': op['end'], 'left': 1000 * op['start'] / item['vysledek']['cmax'], 
                    'width': 1000 * op['end'] / item['vysledek']['cmax'] - 1000 * op['start'] / item['vysledek']['cmax'], 'color': jeraby_barvy[op['stroj']], 
                    'position': jeraby_pozice[op['stroj']] + 20, 'product_color': vany_barvy[slovnik_result[op['prev']]['productid']]}
            parts_jeraby.append(part)
        
        return (parts_jeraby, parts_vany, vany_nazvy, jeraby_nazvy, vany_barvy)   
        
    
    # vygenerovani textovych instrukci
    def create_instrukce(self, item, slovnik_van, slovnik_jerabu, slovnik_result):

        # vytvor text co budes vkladat
        result = []
        for i, op in enumerate(item['vysledek']['transporty']):
            
            # vloz zaznam operace transportu
            # sekvence: dive, rise low, drain, raise high, move, dive, raise high
            prv = slovnik_van[slovnik_result[op['prev']]['stroj']]
            nxt = slovnik_van[slovnik_result[op['next']]['stroj']]
            
            # pokud je to prvni operace, musis tam nejdriv dojet
            if not i:
                result.append((0, slovnik_jerabu[op['stroj']]['sign'] + " " + str(0) + " " + "EMPTY_MOVE TO " + prv['sign']))   
            
            time = op['start'] - prv['dive']

            result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "DIVE"))
            
            time += prv['dive']
            
            result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "RAISE_LOW"))
            
            time += slovnik_jerabu[op['stroj']]['raise_low'] + prv['drain']
            
            result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "RAISE_HIGH"))
            
            time += slovnik_jerabu[op['stroj']]['raise_high']
            
            result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "LOADED_MOVE FROM " + prv['sign'] + " TO " + nxt['sign']))
            
            # time += (slovnik_jerabu[op['stroj']]['move'] * abs(prv['position'] - nxt['position']))
            # NEWGEN
            time = op['end'] - nxt['dive']
            
            result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "DIVE"))
            
            time = op['end']

            result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "RAISE_HIGH"))
            time += slovnik_jerabu[op['stroj']]['raise_high']
        
            # pokud dalsi operace co je na rade patri jinemu produktu, pohni se na dalsi operace a cekej tam
            if slovnik_result[op['prev']]['productid'] != slovnik_result[op['next']]['productid']:
                result.append((time, slovnik_jerabu[op['stroj']]['sign'] + " " + str(time) + " " + "EMPTY_MOVE FROM " + nxt['sign'] + " TO " + slovnik_van[slovnik_result[op['next']]['stroj']]))
            
            # serad result podle casu
            result.sort(key=lambda x: x[0])
                
        return [r[1] for r in result]
