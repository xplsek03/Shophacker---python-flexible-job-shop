'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from pymongo import MongoClient
from tornado import ioloop
from tornado.httpserver import HTTPServer
from tornado.web import Application
import base64
import uuid
import os
from handlers.indexhandler import IndexHandler
from handlers.jerabyhandler import JerabyHandler
from handlers.produktyhandler import ProduktyHandler
from handlers.vanyhandler import VanyHandler
from handlers.confighandler import ConfigHandler
from handlers.historiehandler import HistorieHandler
from handlers.taskhandler import TaskHandler
from handlers.loginhandler import LoginHandler
from handlers.logouthandler import LogoutHandler
import logging
import credentials


if __name__ == "__main__":

    # logovani
    logging.basicConfig(filename='log.log', filemode='w', level=logging.DEBUG)
    
    # pripoj se k db
    db = MongoClient(credentials.cred['db_string'], tls=True)
    db = db['database1']

    # cookies nastaveni
    settings = {
        "cookie_secret": base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
        "login_url": "/login",
        "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "static_path": os.path.join(os.path.dirname(__file__), "templates"),
        "xsrf_cookies": True
    }

    # handlery
    app = Application([
        (r"/", IndexHandler, dict(db=db)),
        (r"/login", LoginHandler, dict(db=db)),
        (r"/logout", LogoutHandler),
        (r"/jeraby/?(.*?)", JerabyHandler, dict(db=db)),
        (r"/produkty/?(.*?)", ProduktyHandler, dict(db=db)),
        (r"/vany/?(.*?)", VanyHandler, dict(db=db)),
        (r"/konfig", ConfigHandler, dict(db=db)),
        (r"/historie/?(.*?)", HistorieHandler, dict(db=db)),
        (r"/task", TaskHandler, dict(db=db))
    ], **settings)

    # ssl twisted kontext
    server = HTTPServer(app, ssl_options={
        "certfile": "ssl/cert.crt",
        "keyfile": "ssl/cert.key",
    })
    server.listen(8888)
    ioloop.IOLoop.instance().start()
