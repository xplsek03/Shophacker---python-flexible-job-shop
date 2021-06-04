'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from task.shophacker import ShophackerProcess
import datetime


'''
Trida se stara o informovani klienta o stavu procesu a zmenu jeho stavu.
'''
class Updater:
    
    # odkaz na taskmgr
    _process = None
    # odkaz na databazi
    _db = None
    # id ulohy kterou kontrolujes
    id = None
    # pocet vysledku pri posledni kontrole
    _pocet_vysledku = 0
    # nejlepsi vysledek
    _best = float("inf")
  
    
    '''
    Vytvoreni optimalizacniho procesu.
    @param db - instance pripojeni k databazi
    @param _id - id vytvorene ulohy
    '''
    @classmethod
    def startTask(cls, db, _id):
        # uloz odkaz na db
        cls._db = db
        # vytvor proces    
        cls._id = _id
        cls._process = ShophackerProcess(id=_id)
        cls._process.start()
        # vytvor prvni callback, za 30s
        IOLoop.current().call_later(5, cls.update)
        
    
    # periodicka kontrola db a existence procesu
    @classmethod
    def update(cls):
        # pokud je proces aktivni, jinak uz dalsi callback nevytvarej
        if cls._process.is_alive():
            # zkontroluj databazi a pripadne odesli do websocketu dalsi info
            zaznam = cls._db['historie'].find_one({'_id': cls._id})
            # mrkni na nove vysledky
            if 'vysledek' in zaznam:
                # pokud nasel lepsi vysledek
                if zaznam['vysledek']['cmax'] < cls._best:
                    # uloz nejlepsi vysledek
                    cls._best = zaznam['vysledek']['cmax']
                    # posli WSHandler.send(ZPRAVA O NOVEM VYSLEDKU)
                    try:
                        WSHandler.send({'message': 'update', 'best': cls._best})
                    except WebSocketClosedError:
                        pass
            # pridej dalsi callback
            IOLoop.current().call_later(5, cls.update)
        # proces uz nebezi
        else:
            try:
                # odesli klientovi zpravu o ukonceni
                WSHandler.send({'message': 'finished'})
            except WebSocketClosedError:
                pass
            # uzavri WS
            cls.stop()
     
        
    # ukonceni optimalizacniho procesu
    @classmethod
    def stop(cls):
        # ukonci proces
        cls._process.terminate()
        # nastav cas ukonceni v db
        cls._db['historie'].update_one({'_id': cls._id}, {'$set': {'end': datetime.datetime.now()}})
        # zavri websocket
        WSHandler.ws.close()
        

# WSS - secured websocket handler
class WSHandler(WebSocketHandler):

    # objekt websocketu
    ws = None
    
    # pri navazani spojeni
    def open(self):
        self.__class__.ws = self

    # pokud klient uzavre spojeni
    def on_close(self):
        pass
    
    # odesilani zprav z websocketu
    @classmethod
    def send(cls, message):
        cls.ws.write_message(message)
