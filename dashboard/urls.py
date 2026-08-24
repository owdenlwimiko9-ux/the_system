from django.urls import path
from . import views

app_name = 'dashboard' # ADD THIS LINE

urlpatterns = [
    path('', views.dashboard_view, name='home'),  # Only 1 path
]