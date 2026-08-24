from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('generate-bills/', views.generate_bills, name='generate_bills'),
    path('download-template/', views.download_control_template, name='download_template'),
    path('upload-controls/', views.upload_bank_controls, name='upload_bank_controls'),
    path('import-report/', views.import_bank_report, name='import_bank_report'),
    path('unpaid-bills/', views.unpaid_bills_list, name='unpaid_bills'),
    path('bill/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('send-reminders/', views.send_reminders_page, name='send_reminders'),
    path('unpaid-bills/', views.unpaid_bills_list, name='unpaid_bills_list'),
]