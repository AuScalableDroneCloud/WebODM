#https://auth0.com/docs/quickstart/backend/django/01-authorization

from functools import wraps
import jwt
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

def get_token_auth_header(request):
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.META.get("HTTP_AUTHORIZATION", None)
    token = None
    if auth:
        parts = auth.split()
        if len(parts) > 1:
            token = parts[1]

    return token

def requires_scope(required_scope):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    def require_scope(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_auth_header(args[0])
            if token:
                decoded = jwt.decode(token, verify=False)
                if decoded.get("scope"):
                    token_scopes = decoded["scope"].split()
                    for token_scope in token_scopes:
                        if token_scope == required_scope:
                            return f(*args, **kwargs)
            response = JsonResponse({'message': 'You don\'t have access to this resource'})
            response.status_code = 403
            return response
        return decorated
    return require_scope

# These are some initial example endpoints,
# can add to here as our API is defined
@api_view(['GET'])
@permission_classes([AllowAny])
def public(request):
    return JsonResponse({'message': 'Hello from a public endpoint! You don\'t need to be authenticated to see this.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def private(request):
    return JsonResponse({'message': 'Hello from a private endpoint! You need to be authenticated to see this.'})

@api_view(['GET'])
@requires_scope('read:projects')
@permission_classes([IsAuthenticated])
def private_scoped(request):
    return JsonResponse({'message': 'Hello from a private endpoint! You need to be authenticated and have a scope of read:projects to see this.'})


