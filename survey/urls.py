from django.urls import path
from . import views

urlpatterns = [
    path('page/<int:page>/', views.survey_page, name='survey_page'),
    path('submit/', views.submit, name='survey_submit'),
    path('done/', views.done, name='survey_done'),
    path('results/', views.results, name='survey_results'),
    path('register/', views.register, name='register'),
    path('reset/', views.reset_survey, name='reset_survey'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-report/', views.download_report, name='download_report'),
    path('export-excel/', views.export_excel, name='export_excel'),
]
