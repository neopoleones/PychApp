import falcon
import cryptography.fernet
from app.storage.mongo import EntityNotFoundException


class Middleware:
    """
    Base middleware class.

    This class serves as a base for other middleware classes. It provides a basic structure
    for processing requests and responses in a Falcon web application.
    """
    def process_request(self, req, resp):
        """
        Process an incoming request.

        Args:
            req: The request object.
            resp: The response object.

        Raises:
            falcon.HTTPServiceUnavailable: By default, this method raises an exception
                                           indicating that the middleware functionality is unimplemented.
        """
        raise falcon.HTTPServiceUnavailable(
            title='Middleware is unimplemented',
        )


class TokenMiddleware(Middleware):
    """
    Middleware for handling authentication tokens.

    This middleware checks for the presence of an authentication token in the request headers,
    validates it, and adds authentication context to the request.

    Attributes:
        sp: An instance of a FernetAdapter(security provider) that offers token decryption/encryption.
    """

    def __init__(self, sp):
        """
        Initialize TokenMiddleware with a security provider for token decryption.

        Args:
            sp: An instance of a FernetAdapter for decrypting tokens.
        """
        self.sp = sp

    def process_request(self, req, resp):
        """
        Process an incoming request for token authentication.

        The method extracts the 'Auth' token from the request headers, validates it,
        and adds authentication context to the request. In case of missing or invalid tokens,
        appropriate error information is added to the request context.

        Args:
            req: The request object.
            resp: The response object.
        """

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
        """
        Decrypt the token to retrieve user data.

        This private method is used internally to decrypt the authentication token.
        Args:
            token: The encrypted token.

        Returns:
            The decrypted user identifier.
        """
        return self.sp.decrypt(token)


class UserByTokenMiddleware(Middleware):
    """
    Middleware for retrieving user instance based on the authentication token.

    This middleware is responsible for fetching user details using the user identifier
    obtained from the authentication token.

    Attributes:
        ps: An instance of a mongodb storage that offers user retrieval functionality.
    """

    def __init__(self, ps):
        """
        Initialize UserByTokenMiddleware with a mongodb storage for user retrieval.

        Args:
            ps:  An instance of a mongodb storage that offers user retrieval.
        """

        self.ps = ps

    def process_request(self, req, resp):
        """
        Process an incoming request to add user information to the context.

        This method uses the user identifier from the authentication context to retrieve user details
        and adds them to the request context. In case of errors, appropriate error information is added.

        Args:
            req: The request object.
            resp: The response object.
        """

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
        """
        Check if the user is authorized.

        This static method is used as a hook for resource methods to ensure that the user is authorized.
        It checks the authentication context for any errors and raises an HTTPUnauthorized exception if necessary.

        Args:
            req: The request object.
            res: The response object.
            resource: The resource object.
            params: The parameters for the request.

        Raises:
            falcon.HTTPUnauthorized: If the user is not authorized.
        """

        auth_data = req.context['auth']
        if 'err' in auth_data:
            raise falcon.HTTPUnauthorized(
                title="Not authorized", description=auth_data['err']
            )


class RequireJSON(Middleware):
    """
    Middleware to enforce JSON request and response types.

    This middleware ensures that the client accepts JSON responses and, for certain HTTP methods,
    sends requests with a JSON content type.
    """

    def process_request(self, req, resp):
        """
        Process an incoming request to enforce JSON requirements.

        This method checks the client's ability to accept JSON responses and the content type of the request.
        If the requirements are not met, appropriate HTTP exceptions are raised.

        Args:
            req: The request object.
            resp: The response object.

        Raises:
            falcon.HTTPNotAcceptable: If the client does not accept JSON responses.
            falcon.HTTPUnsupportedMediaType: If the request content type is not JSON for POST or PUT methods.
        """

        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                description='Only json responses supported',
            )

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    title='Only json requests supported',
                )
