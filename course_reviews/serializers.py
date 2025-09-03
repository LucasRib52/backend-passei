from rest_framework import serializers
from .models import CourseReview

class CourseReviewSerializer(serializers.ModelSerializer):
    """Serializer para listar avaliações"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    
    class Meta:
        model = CourseReview
        fields = [
            'id', 'user_name', 'rating', 'title', 'comment', 
            'course_title', 'rating_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CourseReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar novas avaliações"""
    
    class Meta:
        model = CourseReview
        fields = [
            'course', 'user_name', 'user_email', 'rating', 
            'title', 'comment'
        ]
    
    def validate_rating(self, value):
        """Valida se a avaliação está entre 1 e 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("A avaliação deve estar entre 1 e 5 estrelas.")
        return value
    
    def validate_user_email(self, value):
        """Valida se o email é único para o curso"""
        course = self.initial_data.get('course')
        if course and CourseReview.objects.filter(
            course=course, 
            user_email=value
        ).exists():
            raise serializers.ValidationError(
                "Você já avaliou este curso. Cada cliente pode avaliar um curso apenas uma vez."
            )
        return value

class CourseReviewAdminSerializer(serializers.ModelSerializer):
    """Serializer para administração das avaliações"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    
    class Meta:
        model = CourseReview
        fields = [
            'id', 'course', 'course_title', 'user_name', 'user_email',
            'rating', 'rating_display', 'title', 'comment', 'is_approved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
