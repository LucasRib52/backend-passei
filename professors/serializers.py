from rest_framework import serializers
from .models import Professor


class ProfessorSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Professor
        fields = '__all__'
    
    def get_courses_count(self, obj):
        return obj.course_set.count()


class ProfessorListSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Professor
        fields = [
            'id', 'name', 'specialties', 'approvals_count', 
            'rating', 'image', 'created_at', 'courses_count'
        ]
    
    def get_courses_count(self, obj):
        return obj.course_set.count()


class ProfessorDetailSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Professor
        fields = '__all__'
    
    def get_courses_count(self, obj):
        return obj.course_set.count() 