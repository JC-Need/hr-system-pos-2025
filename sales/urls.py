from django.urls import path
from . import views

urlpatterns = [
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/create/', views.quotation_create, name='quotation_create'),
    path('quotations/<int:qt_id>/', views.quotation_detail, name='quotation_detail'),
]