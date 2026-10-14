from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('', views.apply, name='apply'),
    path('manage/', views.manage_list, name='manage'),
    path('approve/<int:id>/', views.approve, name='approve'),
    path('reject/<int:id>/', views.reject, name='reject'),
    path('status/<str:code>/', views.status, name='status'),
    path('track/', views.track, name='track'),
]