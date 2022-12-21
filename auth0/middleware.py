#https://github.com/python-social-auth/social-app-django/blob/master/social_django/middleware.py
#https://python-social-auth.readthedocs.io/en/latest/configuration/django.html
from social_django.middleware import SocialAuthExceptionMiddleware

from django.shortcuts import HttpResponse
from social_core import exceptions as social_exceptions

class SocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        #if isinstance(exception, SocialAuthBaseException):
        if type(exception) == social_exceptions.AuthCanceled:
            msg = """
            <h1>Auth Error</h1>
            <h2>{}</h2>
            <p>If this error relates to your email not having been verified, the verification email has been resent, 
            it may take a few minutes to arrive, check your inbox and follow the link provided before logging in again.</p>
            <a href="/logout">Logout - return to login page</a>
            """.format(exception)
            return HttpResponse(msg)
        else:
            raise exception
