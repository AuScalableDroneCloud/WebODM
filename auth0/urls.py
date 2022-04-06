#https://auth0.com/docs/quickstart/backend/django/01-authorization

from django.urls import path
from django.conf.urls import include, url

from . import views

# These are some initial example endpoints,
# can add to here as our API is defined
urlpatterns = [
    path('api/public', views.public),
    path('api/private', views.private),
    path('api/private-scoped', views.private_scoped),
]

