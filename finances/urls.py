# finances/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('depenses/',              views.DepenseListCreateView.as_view(),  name='depenses-list'),
    path('depenses/<int:pk>/',     views.DepenseDetailView.as_view(),      name='depense-detail'),
    path('revenus/',               views.RevenuListCreateView.as_view(),   name='revenus-list'),
    path('revenus/<int:pk>/',      views.RevenuDetailView.as_view(),       name='revenu-detail'),
    path('categories/',            views.CategoriListView.as_view(),       name='categories-list'),
    path('tableau-bord/',          views.tableau_bord_finances,            name='finances-tableau-bord'),
    path('rapport/',               views.rapport_mensuel,                  name='rapport-mensuel'),
]