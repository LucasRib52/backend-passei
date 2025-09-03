from django.urls import path
from . import views

app_name = 'testimonials'

urlpatterns = [
    # URLs Públicas
    path('', views.TestimonialListView.as_view(), name='testimonial-list'),
    
    # URLs de Administração
    path('admin/', views.AdminTestimonialViewSet.as_view(), name='admin-testimonial-list'),
    path('admin/<int:id>/', views.AdminTestimonialDetailView.as_view(), name='admin-testimonial-detail'),
] 