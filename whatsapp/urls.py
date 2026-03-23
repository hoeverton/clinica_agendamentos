from django.urls import path, include
from .views import whatsapp_webhook, qr_code_whatsapp

urlpatterns = [
    path("whatsapp/", whatsapp_webhook),
    #path("conectar/", conectar_whatsapp),
    path("qr/", qr_code_whatsapp),
   
]

