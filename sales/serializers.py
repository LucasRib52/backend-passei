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
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'student_name', 'email', 'phone', 'course_title',
            'price', 'payment_method', 'status', 'created_at'
        ] 