# suivi_poules/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('journalier/',        views.SuiviListCreateView.as_view(),  name='suivi-list'),
    path('journalier/<int:pk>/',views.SuiviDetailView.as_view(),     name='suivi-detail'),
    path('stats/',             views.stats_suivi,                    name='suivi-stats'),
    path('veterinaire/',       views.VetListCreateView.as_view(),    name='vet-list'),
    path('veterinaire/<int:pk>/',views.VetDetailView.as_view(),      name='vet-detail'),
]