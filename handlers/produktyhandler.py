'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler, ContentMixin
import bson
from tornado.web import authenticated


class ProduktyHandler(BaseHandler, ContentMixin):

    @authenticated
    def get(self, nazev):
        # pridani a detail
        if nazev:
            vany = self.db["vany"].find()
            kroky = {}
            for vana in vany:
                # KROKY = {ID: {'sign': SIGN, 'nazev': NAZEV}}
                kroky[vana['_id']] = {'sign': vana['sign'], 'nazev': vana['nazev']}
            # pridani
            if nazev == 'add':
                self.render("produkt_new.html", kroky=kroky)
            # detail
            else:
                item = self.db["produkty"].find_one({"_id": bson.ObjectId(nazev)})
                self.render("produkt_detail.html", item=item, kroky=kroky)
        # seznam
        else:
            # ziskej seznam z db
            items = self.db["produkty"].find()
            self.render("produkty.html", items=items)

    @authenticated
    def post(self, id=None):

        # id je pouzito v action formulare, kde je vic tlacitek

        # pokud kliknul na SAVE nebo NEW
        if (self.get_argument('save', None) is not None) or (self.get_argument('new', None) is not None):
            # uloz nove hodnoty
            # save
            if self.get_argument('save', None) is not None:
                new_val = {'kroky': [], 'nazev': self.get_argument('nazev')}
                filtr = {'_id': bson.ObjectId(id)}
            # new
            else:
                new_val = {'kroky': [], 'nazev': self.get_argument('nazev'), 'sign': self.get_argument('sign')}
            # alespon jedna zmena v krocich, jinak ignore
            at_least_one = False
            for key,val in self.request.arguments.items():
                if 'krok' in key:
                    at_least_one = True
                    # zpracuj jeden krok
                    new_val['kroky'].append([bson.ObjectId(i.decode()) for i in val])
            if at_least_one:
                # save
                if self.get_argument('save', None) is not None:
                    self.db['produkty'].update_one(filtr, {'$set': new_val})
                # new
                else:
                    self.db['produkty'].insert_one(new_val)
        # kliknul na DELETE
        elif self.get_argument('delete', None) is not None:
            self.db['produkty'].delete_one({'_id': bson.ObjectId(id)})
        # presmeruj ho na seznam van
        self.redirect("/produkty")
