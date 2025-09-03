"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/v1/courses/', include('courses.urls')),
    path('api/v1/professors/', include('professors.urls')),
    path('api/v1/testimonials/', include('testimonials.urls')),
    path('api/v1/news/', include('news.urls')),
    path('api/v1/sales/', include('sales.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/categories/', include('courses.category_urls')),
    path('api/v1/themembers/', include('themembers.urls')),
    path('api/v1/asaas/', include('integration_asas.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
    path('api/v1/course-reviews/', include('course_reviews.urls')),
    
    # Documentação da API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Configuração para arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
