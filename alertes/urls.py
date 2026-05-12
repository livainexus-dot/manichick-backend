# alertes/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.AlerteListView.as_view(), name='alertes-list'),
    path('<int:pk>/acquitter/', views.acquitter_alerte, name='alerte-acquitter'),
    path('acquitter-toutes/', views.acquitter_toutes, name='acquitter-toutes'),
]