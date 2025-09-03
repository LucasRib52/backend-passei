"""
URLs para integração com TheMembers
"""
from django.urls import path
from . import views

app_name = 'themembers'

urlpatterns = [
    # Produtos e sincronização
    path('products/', views.get_available_products, name='get_available_products'),
    path('sync/', views.sync_products, name='sync_products'),
    
    # Vinculação de cursos
    path('link-course/', views.link_course_to_product, name='link_course_to_product'),
    path('course/<int:course_id>/integration/', views.get_course_integration, name='get_course_integration'),
    
    # Assinaturas
    path('create-subscription/', views.create_subscription_for_sale, name='create_subscription_for_sale'),
]
