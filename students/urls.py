from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path("", views.student_list, name="student_list"),
    path("add/", views.student_create, name="student_create"),
    
    path("attendance/daily/", views.daily_attendance_summary, name="daily_attendance_summary"),
    
    path("class/<int:class_id>/", views.students_by_class, name="students_by_class"), 
    path("class/<int:class_id>/attendance/", views.take_class_attendance, name="take_class_attendance"),
    
    # NEW: Parent dashboard
    path("my-children/", views.MyChildrenListView.as_view(), name="my_children"),
    
    # REPLACE the old detail with the protected one
    path("<int:pk>/", views.student_detail_protected, name="student_detail"),
    
    path("<int:pk>/edit/", views.student_update, name="student_update"),
    path('bulk-upload/', views.student_bulk_upload, name='student_bulk_upload'),
    path('id-cards/', views.student_id_cards, name='student_id_cards'),
    path('id-card/<int:pk>/', views.student_id_card_single, name='student_id_card_single'),
path('id-cards/<int:class_id>/', views.student_id_cards_by_class, name='student_id_cards_by_class'),
    path('bulk-upload/template/', views.download_student_template, name='download_student_template'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),

    # DELETE
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path("<int:student_id>/attendance/", views.student_attendance_report, name="student_attendance_report"),
]