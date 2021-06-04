'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler
import datetime
import bson
from communication.network import Updater, WSHandler
from pymongo import DESCENDING
import secrets
from tornado.web import authenticated


# nova uloha a vytvoreni trvaleho spojeni
class TaskHandler(BaseHandler):

    @authenticated
    def get(self):
        # najdi dostupne produkty a jeraby
        produkty = self.db['produkty'].find()
        jeraby = self.db['jeraby'].find()
        has_prev = self.db['historie'].find().count()
        self.render("task_new.html", produkty=list(produkty), jeraby=jeraby, has_prev=has_prev)  # bacha, vysledek find() je generator, nebo teda byl spis

    @authenticated
    def post(self):

        # pokud chce zobrazit vysledek, hod ho na historii
        if self.get_argument('show-result', None):
            self.redirect("/historie")
            
        # pokud to chce zastavit tu ulohu
        elif self.get_argument('kill', None):
            
            # killni websocket
            Updater.stop()
            # renderuj hl stranu
            self.redirect('/')

        # tady posli formular a otevri spojeni, vytvor websocket
        inserted = None
        
        # pokud opakuje posledni spustenou ulohu
        if self.get_argument('last', None) is not None:
            # vytahni z databaze posledni spustenou ulohu
            last = self.db['historie'].find_one(sort=[('_id', DESCENDING)])
            if last:
                inserted = self.db['historie'].insert_one({'nazev': last['nazev'] + secrets.token_hex(1),
                                                      'start': datetime.datetime.now(),
                                                      'produkty': last['produkty'],
                                                      'jeraby': last['jeraby'],
                                                      'multiply': last['multiply']
                                                      })                               
            
        # vytvari novou ulohu
        else:
            # neco tam pridal za produkty
            if self.get_arguments('produkt') and self.get_arguments('pocet') and self.get_arguments('jeraby[]'):
                jeraby = self.get_arguments('jeraby[]')
                produkty = self.get_arguments('produkt')
                pocty = self.get_arguments('pocet')
                multiply = int(self.get_argument('multiply'))
                nazev = self.get_argument('nazev', None)
                # musi zadat vzdy u obou, jinak se to bude fakt blbe dohledavat
                if len(produkty) == len(pocty):
                    recipes = list(zip(produkty, [int(i) for i in pocty]))  # (str->ObjectId, pocet)
                    # revize zadanych produktu
                    repaired_recipes = {}
                    for r in recipes:
                        # jeste tam neni
                        if r[0] not in repaired_recipes:
                            repaired_recipes[r[0]] = r[1]
                        # uz tam je, pricist
                        else:
                            repaired_recipes[r[0]] += r[1]
                            
                    # vytvor pole s nazvy produktu, abys ho pak pri zobraxovani vysledku nemusel pracne dohledavat
                    zaznamy = self.db['produkty'].find({"_id": {"$in": [bson.ObjectId(i) for i in repaired_recipes]}})
                    nazvy_produktu = {}
                    for z in zaznamy:
                        nazvy_produktu[z['_id']] = z['nazev']
                    
                    inserted = self.db['historie'].insert_one({'nazev': nazev if nazev else secrets.token_hex(8),
                                                          'start': datetime.datetime.now(),
                                                          'produkty': [{'id': bson.ObjectId(key), 'pocet': val, 'nazev': nazvy_produktu[bson.ObjectId(key)]} for key,val in repaired_recipes.items()],
                                                          'jeraby': [bson.ObjectId(j) for j in jeraby],
                                                          'multiply': multiply
                                                          })
    
        # pokud doslo k vlozeni zaznamu do db
        if inserted:
            # nastartuj websocket
            self.startWebsocket(self.get_argument('nazev'), datetime.datetime.now())
            # odesli oznameni o startu
            Updater.startTask(self.db, inserted.inserted_id)

    # zahajeni websocketu
    def startWebsocket(self, nazev, start):
        # aktivuj handler WS
        self.application.add_handlers(r".*", [(r"/ws", WSHandler)])
        # pred timhle klidne jeste proved enjakou kontrolu jestli vsechno existuje atd.
        self.render("task_started.html", nazev=nazev, start=start)
