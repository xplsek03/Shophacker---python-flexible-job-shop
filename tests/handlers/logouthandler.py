'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from tornado.web import RequestHandler


# odhlasovaci stranka
class LogoutHandler(RequestHandler):

    def get(self):
        # smaz zabezpecenou cookie
        self.clear_cookie("mail")
        self.redirect(self.get_argument('next','/'))
