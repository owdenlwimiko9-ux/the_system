from django.urls import path
from. import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('admissions/', views.admission_list_view, name='admission_list'),
    path('admissions/approve/<int:id>/', views.admission_approve, name='admission_approve'),
    path('admissions/reject/<int:id>/', views.admission_reject, name='admission_reject'),
]