from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # DASHBOARD
    path('', views.class_list, name='class_list'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # CLASS
    path('classes/', views.class_list, name='class_list_all'),
    path('classes/add/', views.class_create, name='class_create'),
    path('classes/<int:pk>/', views.class_dashboard, name='class_dashboard'),
    path('class/<int:class_id>/', views.class_overview, name='class_overview'),
    path('class/<int:pk>/detail/', views.class_detail, name='class_detail'), # Nimeongeza /detail/ ili isi-conflict
    path('class/<int:class_id>/generate/', views.generate_reports, name='generate_reports'),
    path('class/<int:pk>/reports/', views.report_list, name='report_list'),
    path('class/<int:class_id>/send-whatsapp/', views.send_whatsapp_page, name='send_whatsapp_page'),
    path('class/<int:class_id>/send-results/<int:term_number>/', views.send_results_to_parents, name='send_results_to_parents'),
    path('class/<int:class_pk>/exam/<int:exam_pk>/marks/', views.enter_marks, name='enter_marks'),

    # STUDENT / REPORT
    path('student/<int:pk>/', views.student_profile, name='student_profile'),
    path('report/<int:pk>/', views.report_detail, name='report_detail'),
    path('report/<int:pk>/pdf/', views.report_pdf, name='report_pdf'),
    path('bulk-print/<int:class_id>/<int:exam_id>/', views.bulk_print_class_reports, name='bulk_print_class_reports'),

    # EXAM
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_create, name='exam_create'),
    path('exam/<int:exam_id>/download-template/', views.download_template, name='download_template'),
    path('exam/<int:exam_id>/bulk-upload/', views.bulk_upload_results, name='bulk_upload_results'),

    # SUBJECT
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    # TEACHER
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:pk>/edit/', views.teacher_update, name='teacher_update'),
    path('teachers/<int:pk>/assign-subject/', views.assign_subject_to_teacher, name='assign_subject_to_teacher'),

    # YEAR / TERM
    path('years/', views.year_list, name='year_list'),
    path('years/add/', views.year_create, name='year_create'),
    path('years/<int:pk>/edit/', views.year_update, name='year_update'),
    path('years/<int:pk>/activate/', views.year_activate, name='year_activate'),
    path('terms/', views.term_list, name='term_list'),
    path('terms/add/', views.term_create, name='term_create'),
    path('terms/<int:pk>/edit/', views.term_update, name='term_update'),
    path('terms/<int:pk>/delete/', views.term_delete, name='term_delete'),
]