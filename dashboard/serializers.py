from rest_framework import serializers
from .models import DashboardMetric, StudentActivity, CoursePerformance


class DashboardMetricSerializer(serializers.ModelSerializer):
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    
    class Meta:
        model = DashboardMetric
        fields = '__all__'


class StudentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentActivity
        fields = '__all__'


class CoursePerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePerformance
        fields = '__all__'


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer para visão geral do dashboard"""
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_sales = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    period_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    period_sales = serializers.IntegerField()
    period_label = serializers.CharField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    recent_sales = serializers.ListField()
    top_courses = serializers.ListField()
    new_students_period = serializers.IntegerField()
    revenue_chart_data = serializers.ListField()
    sales_chart_data = serializers.ListField()


class RecentSaleSerializer(serializers.Serializer):
    """Serializer para vendas recentes"""
    id = serializers.IntegerField()
    student_name = serializers.CharField()
    course_title = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    payment_method_display = serializers.CharField()


class TopCourseSerializer(serializers.Serializer):
    """Serializer para cursos mais vendidos"""
    course_title = serializers.CharField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    last_sale_date = serializers.DateTimeField()
