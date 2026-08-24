from django.urls import path
from .views import (
    account_manage, 
    account_create, 
    AccountUpdateView, 
    AccountDeleteView,
    RoleBasedLoginView  # <-- import the class
)

app_name = 'accounts'

urlpatterns = [
    path('login/', RoleBasedLoginView.as_view(), name='login'),
    path('manage/', account_manage, name='account_manage'),
    path('create/', account_create, name='account_create'),
    path('edit/<int:pk>/', AccountUpdateView.as_view(), name='account_edit'),
    path('delete/<int:pk>/', AccountDeleteView.as_view(), name='account_delete'),
]