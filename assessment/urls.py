from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_assessment, name='start_assessment'),
    path('submit/', views.submit_assessment, name='submit_assessment'),
]
