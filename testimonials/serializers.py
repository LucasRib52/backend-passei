from rest_framework import serializers
from .models import Testimonial
from courses.serializers import CourseListSerializer


class TestimonialSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Testimonial
        fields = '__all__'


class TestimonialCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de depoimentos
    Aceita apenas o ID do curso
    """
    
    class Meta:
        model = Testimonial
        fields = [
            'name', 'position', 'location', 'course', 'result', 
            'rating', 'testimonial', 'image', 'video', 'video_url', 'year', 'status'
        ]


class TestimonialListSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Testimonial
        fields = [
            'id', 'name', 'position', 'location', 'course',
            'result', 'rating', 'testimonial', 'image', 'video', 'video_url', 'year', 'status'
        ] 