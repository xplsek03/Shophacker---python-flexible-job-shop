'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler
from tornado.web import authenticated


# hlavni stranka
class IndexHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render("index.html")
