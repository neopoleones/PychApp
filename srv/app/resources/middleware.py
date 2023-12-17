import falcon
import cryptography.fernet
from app.storage.mongo import EntityNotFoundException


class Middleware:
    def process_request(self, req, resp):
        raise falcon.HTTPServiceUnavailable(
            title='Middleware is unimplemented',
        )


class TokenMiddleware(Middleware):
    def __init__(self, sp):
        self.sp = sp

    def process_request(self, req, resp):
        token = req.get_header('Auth')

        if token is None:
            req.context['auth'] = {
                'user_id': None,
                'err': 'Auth token is not specified'
            }
            return

        try:
            uid = self.__get_data(token)
            req.context['auth'] = {
                'user_id': uid,
            }
        except cryptography.fernet.InvalidToken:
            req.context['auth'] = {
                'user_id': None,
                'err': 'Auth token is invalid'
            }

    def __get_data(self, token):
        return self.sp.decrypt(token)


class UserByTokenMiddleware(Middleware):
    def __init__(self, ps):
        self.ps = ps

    def process_request(self, req, resp):
        auth_data = req.context['auth']
        if 'err' in auth_data:
            return

        try:
            req.context['auth'] = {
                'user': self.ps.get_user_by_uid(auth_data['user_id'].decode())
            }

        except EntityNotFoundException as e:
            req.context['auth'] = {
                'user': None,
                'err': 'Invalid user'
            }

    @staticmethod
    def check_user(req, res, resource, params):
        auth_data = req.context['auth']
        if 'err' in auth_data:
            raise falcon.HTTPUnauthorized(title="Not authorized", description=auth_data['err'])


class RequireJSON(Middleware):
    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                description='Only json responses supported',
            )

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    title='Only json requests supported',
                )
