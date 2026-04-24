from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from education import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('firebase-messaging-sw.js', views.firebase_messaging_sw),
    path('save-token/', views.save_fcm_token),
    path('', include('education.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
