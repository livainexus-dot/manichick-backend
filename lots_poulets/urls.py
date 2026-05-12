# lots_poulets/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.LotListCreateView.as_view(),  name='lots-list'),
    path('tableau-bord/',             views.tableau_bord_lots,            name='lots-tableau-bord'),
    path('<int:pk>/',                 views.LotDetailView.as_view(),      name='lot-detail'),
    path('<int:lot_id>/suivis/',      views.SuiviLotListCreateView.as_view(), name='lot-suivis'),
    path('<int:lot_id>/ia-besoins/',  views.ia_besoins_lot,               name='lot-ia-besoins'),
    path('<int:lot_id>/ia-croissance/', views.ia_analyse_croissance,      name='lot-ia-croissance'),
    path('<int:lot_id>/ventes/',      views.VenteListCreateView.as_view(), name='lot-ventes'),
]