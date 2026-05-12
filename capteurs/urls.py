# capteurs/urls.py — version finale complète

from django.urls import path
from . import views

urlpatterns = [
    path('mesures/',                                  views.MesureListView.as_view(),    name='mesures-list'),
    path('mesures/derniere/',                         views.MesureDerniereView.as_view(),name='mesure-derniere'),
    path('mesures/creer/',                            views.creer_mesure,                name='mesure-creer'),
    path('ia/',                                       views.analyse_ia,                  name='analyse-ia'),
    path('photos-intrusion/',                         views.photos_intrusion,            name='photos-list'),
    path('photos-intrusion/<int:pk>/acquitter/',      views.acquitter_photo,             name='photo-acquitter'),
    path('big-data/',                                 views.big_data_dashboard,          name='big-data'),
    path('export-csv/',                               views.export_csv,                  name='export-csv'),
]