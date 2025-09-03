from django.contrib import admin
from .models import Sale


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'student_name', 'email', 'course', 'price', 'payment_method', 
        'status', 'asaas_payment_id', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'created_at', 'course'
    ]
    search_fields = [
        'student_name', 'email', 'course__title', 'asaas_payment_id'
    ]
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações do Aluno', {
            'fields': ('student_name', 'email', 'phone', 'cpf_cnpj')
        }),
        ('Curso e Pagamento', {
            'fields': ('course', 'price', 'payment_method', 'status')
        }),
        ('Endereço', {
            'fields': (
                'address', 'address_number', 'address_complement',
                'neighborhood', 'city', 'state', 'postal_code'
            ),
            'classes': ('collapse',)
        }),
        ('Integrações', {
            'fields': (
                'asaas_payment_id', 'themembers_subscription_id', 
                'themembers_access_granted'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_address_display(self, obj):
        return obj.full_address
    full_address_display.short_description = 'Endereço Completo'
