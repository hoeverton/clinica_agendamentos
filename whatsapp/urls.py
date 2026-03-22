from django.urls import path, include
from .views import whatsapp_webhook

urlpatterns = [
    path("whatsapp/", whatsapp_webhook),
   
]

