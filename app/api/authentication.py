from rest_framework_jwt.authentication import JSONWebTokenAuthentication

class JSONWebTokenAuthenticationQS(JSONWebTokenAuthentication):
    #If using django-rest-framework-jwt
    #(https://github.com/jpadilla/django-rest-framework-jwt/blob/master/rest_framework_jwt/authentication.py)
    def get_jwt_value(self, request):
         return request.query_params.get('jwt')

    #If using drf-jwt
    #(https://github.com/Styria-Digital/django-rest-framework-jwt/blob/master/src/rest_framework_jwt/authentication.py)
    def get_token_from_request(self, request):
         return request.query_params.get('jwt')

