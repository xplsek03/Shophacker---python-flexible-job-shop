'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler, ContentMixin
import bson
from tornado.web import authenticated


# prehled, detail, pridani vany, smazani vany
class VanyHandler(BaseHandler):

    @authenticated
    def get(self, nazev=None):
        ContentMixin.get(self, nazev, 'vany', 'vana')

    @authenticated
    def post(self, id=None):

        # id je pouzito v action formulare, kde je vic tlacitek

        # pokud kliknul na vytvorit novou vanu
        if self.get_argument('new', None) is not None:
            # uloz nove hodnoty
            new_val = {'sign': self.get_argument('sign'),
                       'nazev': self.get_argument('nazev'),
                       'position': int(self.get_argument('position')),
                       'exp_min': int(self.get_argument('exp_min')),
                       'exp_max': int(self.get_argument('exp_max')),
                       'drain': int(self.get_argument('drain')),
                       'dive': int(self.get_argument('dive')),
                       }
            self.db['vany'].insert_one(new_val)

        # pokud kliknul na SAVE.
        if self.get_argument('save', None) is not None:
            # uloz nove hodnoty
            new_val = {'nazev': self.get_argument('nazev'),
                       'position': int(self.get_argument('position')),
                       'exp_min': int(self.get_argument('exp_min')),
                       'exp_max': int(self.get_argument('exp_max')),
                       'drain': int(self.get_argument('drain')),
                       'dive': int(self.get_argument('dive')),
                       }
            filtr = {'_id': bson.ObjectId(id)}
            self.db['vany'].update_one(filtr, {'$set': new_val})

        # kliknul na DELETE
        elif self.get_argument('delete', None) is not None:
            self.db['vany'].delete_one({'_id': bson.ObjectId(id)})
            # smaz dotcene produkty
            self.cascade_delete(bson.ObjectId(id))

        # presmeruj ho na seznam van
        self.redirect("/vany")

    # smaz zavisle produkty
    def cascade_delete(self, id):
        produkty = self.db['produkty'].find()
        for produkt in produkty:
            for krok in produkt['kroky']:
                if krok == id:
                    # smaz tenhle nalezeny produkt
                    self.db['produkty'].delete_one({'_id': produkt['_id']})
                    # pokracuj dal
                    break
