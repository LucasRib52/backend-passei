from django.contrib import admin
from .models import CourseReview

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'course', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'course', 'created_at']
    search_fields = ['user_name', 'user_email', 'title', 'comment', 'course__title']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('user_name', 'user_email')
        }),
        ('Avaliação', {
            'fields': ('course', 'rating', 'title', 'comment')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} avaliações foram aprovadas com sucesso!')
    approve_reviews.short_description = "Aprovar avaliações selecionadas"
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} avaliações foram desaprovadas com sucesso!')
    disapprove_reviews.short_description = "Desaprovar avaliações selecionadas"
