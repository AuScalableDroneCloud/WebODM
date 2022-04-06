#https://auth0.com/docs/quickstart/backend/django/01-authorization

from django.contrib.auth import authenticate
import json
import jwt
import requests
from webodm import settings

def jwt_get_username_from_payload_handler(payload):
    #username = payload.get('sub').replace('|', '.')

    # Auth0 social login has a user id code instead of username in payload
    # Use the social_django database to look up the actual username
    from social_django.models import UserSocialAuth
    # select_related for performance.
    UID = payload.get('sub')
    user_details = UserSocialAuth.objects.select_related("user").filter(uid=UID)
    if user_details and len(user_details) == 1:
        username = str(user_details[0].user)
        authenticate(remote_user=username, create_unknown_user=False)
        return username

    from rest_framework.exceptions import AuthenticationFailed
    raise(AuthenticationFailed(detail="Username not available", code=None))

def jwt_decode_token(token):
    header = jwt.get_unverified_header(token)
    jwks = requests.get('https://{}/.well-known/jwks.json'.format(settings.SOCIAL_AUTH_AUTH0_DOMAIN)).json()
    public_key = None
    for jwk in jwks['keys']:
        if jwk['kid'] == header['kid']:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    if public_key is None:
        raise Exception('Public key not found.')


    issuer = 'https://{}/'.format(settings.SOCIAL_AUTH_AUTH0_DOMAIN)
    return jwt.decode(token, public_key, audience=settings.JWT_AUTH['JWT_AUDIENCE'], issuer=issuer, algorithms=['RS256'])

