# -*- coding: utf-8 -*-
from oauthlib.oauth2 import LegacyApplicationClient
from oauthlib.common import add_params_to_uri, add_params_to_qs

AUTH_HEADER = 'auth_header'
URI_QUERY = 'query'
BODY = 'body'

class LegacyApplicationClientJWT(LegacyApplicationClient):

    def __init__(self, client_id, **kwargs):
        super(LegacyApplicationClientJWT, self).__init__(client_id, **kwargs)

    @property
    def token_types(self):
        """Supported token types and their respective methods

        Additional tokens can be supported by extending this dictionary.

        The Bearer token spec is stable and safe to use.

        The MAC token spec is not yet stable and support for MAC tokens
        is experimental and currently matching version 00 of the spec.
        """
        return {
            'Bearer': self._add_bearer_token,
            'MAC': self._add_mac_token,
            'urn:ietf:params:oauth:token-type:jwt': self._add_accessToken_token
        }

    def _add_accessToken_token(self, uri, http_method='GET', body=None,
                          headers=None, token_placement=None):
        """Add a AccessToken token to the request uri, body or authorization header."""
        if token_placement == AUTH_HEADER:
            headers = prepare_accessToken_headers(self.access_token, headers)
        
        elif token_placement == URI_QUERY:
            uri = prepare_accessToken_uri(self.access_token, uri)

        elif token_placement == BODY:
            body = prepare_accessToken_body(self.access_token, body)

        else:
            raise ValueError("Invalid token placement.")
        
        return uri, headers, body

def prepare_accessToken_headers(token, headers=None):
    """Add a `AccessToken`_ to the request URI.
    AccessToken: h480djs93hd8
    """
    headers = headers or {}
    headers['AccessToken'] = token
    headers['api-version'] = '5'
    return headers

def prepare_accessToken_uri(token, uri):
    """Add a `AccessToken`_ to the request URI.
    http://www.example.com/path?access_token=h480djs93hd8
    """
    return add_params_to_uri(uri, [(('access_token', token))])

def prepare_accessToken_body(token, body=''):
    """Add a `AccessToken`_ to the request body.
    access_token=h480djs93hd8
    """
    return add_params_to_qs(body, [(('access_token', token))])