'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

from handlers.custom import BaseHandler
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from tornado.gen import coroutine


# prihlasovaci stranka
class LoginHandler(BaseHandler):

    def get(self):
        # tady mu posli sablonu prihlasovaci stranky
        self.render("login.html")

    @coroutine
    def post(self):
        # over jestli existuje v db
        user = self.db['users'].find_one({"email": self.get_argument("email")})

        if user:
            kdf = Scrypt(salt=bytes.fromhex(user['salt']),
                    length=32,
                    n=2**14,
                    r=8,
                    p=1,
            )
            kdf.verify(self.get_argument("pass").encode(), bytes.fromhex(user['password']))

            # nastav cookie
            self.set_secure_cookie("mail", self.get_argument("email"))
            # prejdi na hl stranku
            self.redirect("/")
