'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler
from tornado.web import authenticated


# konfigurace parametru
class ConfigHandler(BaseHandler):

    @authenticated
    def get(self):
        # tady mu konfiguracni stranku
        config = self.db['konfig'].find_one({"_default": True})
        if config:
            self.render("konfig.html", config=config)

    @authenticated
    def post(self):
        # over jestli existuje v db
        if self.db['konfig'].find_one({"_default": True}):

            # pokud neni checkbox zaskrtnuty, hodnota neni v POST!

            # uloz nove hodnoty
            new_val = {'mutace_single': float(self.get_argument('mutace_single')),
                       'mutace_single_pocet_namaceni': int(self.get_argument('mutace_single_pocet_namaceni')),
                       'mutace_single_pocet_transporty': int(self.get_argument('mutace_single_pocet_transporty')),
                       'mutace_order': float(self.get_argument('mutace_order')),
                       'mutace_order_pocet': int(self.get_argument('mutace_order_pocet')),
                       'generace': int(self.get_argument('generace')),
                       'populace': int(self.get_argument('populace')),
                       'nekonecno': True if ('nekonecno' in self.request.arguments) else False,
                       'cores': int(self.get_argument('cores'))}
            filtr = {'_default': True}
            self.db['konfig'].update_one(filtr, {'$set': new_val})
            # prejdi na hl. stranku
            self.redirect("/")
