from django.contrib import admin
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'course', 'rating', 'status', 'year', 'created_at']
    list_filter = ['status', 'rating', 'year', 'created_at']
    search_fields = ['name', 'position', 'testimonial', 'course__title']
    ordering = ['-created_at']
    
    fields = (
        'name', 'position', 'location', 'course',
        'result', 'rating', 'testimonial',
        'image', 'video', 'video_url',
        'year', 'status'
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')
