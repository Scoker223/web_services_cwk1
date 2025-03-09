from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),               # Admin dashboard
    path('api/', include('myapp.urls')),           # Include app-level URLs for APIs
    path('', RedirectView.as_view(url='/api/')),   # Redirect to /api/
]
