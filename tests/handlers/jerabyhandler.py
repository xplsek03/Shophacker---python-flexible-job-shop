'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler, ContentMixin
import bson
from tornado.web import authenticated


# prehled jerabu, pridani jerabu, detail jerabu, smazani jerabu
class JerabyHandler(BaseHandler, ContentMixin):

    @authenticated
    def get(self, nazev=None):
        ContentMixin.get(self, nazev, 'jeraby', 'jerab')

    @authenticated
    def post(self, id=None):

        # id je pouzito v action formulare, kde je vic tlacitek

        # pokud kliknul na vytvorit novy jerab
        if self.get_argument('new', None) is not None:
            # uloz nove hodnoty
            new_val = {'sign': self.get_argument('sign'),
                       'nazev': self.get_argument('nazev'),
                       'empty_move': int(self.get_argument('prejezd')),
                       'move': int(self.get_argument('move')),
                       'raise_low': int(self.get_argument('raise_low')),
                       'raise_high': int(self.get_argument('raise_high'))
                       }
            self.db['jeraby'].insert_one(new_val)

        # pokud kliknul na SAVE.
        if self.get_argument('save', None) is not None:
            # uloz nove hodnoty
            new_val = {
               'nazev': self.get_argument('nazev'),
               'empty_move': int(self.get_argument('prejezd')),
               'move': int(self.get_argument('move')),
               'raise_low': int(self.get_argument('raise_low')),
               'raise_high': int(self.get_argument('raise_high'))
            }
            filtr = {'_id': bson.ObjectId(id)}
            self.db['jeraby'].update_one(filtr, {'$set': new_val})

        # kliknul na DELETE
        elif self.get_argument('delete', None) is not None:
            self.db['jeraby'].delete_one({'_id': bson.ObjectId(id)})

        # presmeruj ho na seznam van
        self.redirect("/jeraby")
