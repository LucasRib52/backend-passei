from rest_framework import serializers
from .models import Sale
from courses.serializers import CourseListSerializer


class SaleSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    themembers_product_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = '__all__'

    def get_themembers_product_ids(self, obj):
        try:
            return obj.course.get_themembers_product_ids()
        except Exception:
            return []


class SaleListSerializer(serializers.ModelSerializer):
    # OTIMIZADO: usa SerializerMethodField para lidar com cursos excluídos sem query extra
    course_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'student_name', 'email', 'phone', 'course_title',
            'price', 'payment_method', 'status', 'created_at'
        ]
    
    def get_course_title(self, obj):
        """Retorna título do curso do snapshot se curso foi excluído"""
        if obj.course:
            return obj.course.title
        return obj.course_title_snapshot or 'Curso removido' 