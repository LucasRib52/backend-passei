from django.urls import path
from .views import (
    CourseReviewListCreateView,
    CourseReviewDetailView,
    CourseReviewAdminListView,
    CourseReviewAdminDetailView,
    CourseReviewStatsView
)

app_name = 'course_reviews'

urlpatterns = [
    # URLs públicas para clientes
    path('', CourseReviewListCreateView.as_view(), name='review-list-create'),
    path('<int:pk>/', CourseReviewDetailView.as_view(), name='review-detail'),
    path('course/<int:course_id>/stats/', CourseReviewStatsView.as_view(), name='course-stats'),
    
    # URLs administrativas
    path('admin/', CourseReviewAdminListView.as_view(), name='admin-review-list'),
    path('admin/<int:pk>/', CourseReviewAdminDetailView.as_view(), name='admin-review-detail'),
]
