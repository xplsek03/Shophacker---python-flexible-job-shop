'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from tornado.web import RequestHandler, authenticated
import bson
from pymongo import DESCENDING


# zakladni handler, resi cookies
class BaseHandler(RequestHandler):

    def initialize(self, db):
        self.db = db

    def get_current_user(self):
        return self.get_secure_cookie("mail")
    

# spolecna metoda GET atd. pro ruzne typy handleru
class ContentMixin(object):

    @authenticated
    def get(instance, nazev, mnozne, jednotne):
        # pridani
        if nazev == 'add':
            instance.render(jednotne+"_new.html")
        # detail
        elif nazev:
            # najdi v db
            item = instance.db[mnozne].find_one({"_id": bson.ObjectId(nazev)})
            if item:
                instance.render(jednotne+"_detail.html", item=item)
        else:
            # ziskej seznam z db
            items = instance.db[mnozne].find(sort=[('_id', DESCENDING)])
            instance.render(mnozne+".html", items=items)
