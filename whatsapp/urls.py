from django.urls import path, include
from .views import whatsapp_webhook, qr_code_whatsapp,webhook_whatsapp


urlpatterns = [
    path("whatsapp/", whatsapp_webhook),
    #path("conectar/", conectar_whatsapp),
    path("qr/", qr_code_whatsapp),
    path("webhook/", webhook_whatsapp, name="webhook_whatsapp"),
    
   
]

