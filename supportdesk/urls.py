from django.urls import path
from . import views

app_name = 'supportdesk'

urlpatterns = [
    path('', views.ticket_create, name='ticket_create'),
    path('success/', views.ticket_success, name='ticket_success'),
    path('priority-check/', views.priority_checker, name='priority_checker'),
]
