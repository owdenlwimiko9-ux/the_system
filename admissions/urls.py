from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('apply/', views.apply_view, name='apply'),
    path('manage/', views.admission_list_view, name='list'),
    path('approve/<int:id>/', views.admission_approve, name='approve'),
    path('reject/<int:id>/', views.admission_reject, name='reject'),
]