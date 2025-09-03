from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # O campo 'username' pode conter email ou username
        username_or_email = attrs.get('username')
        password = attrs.get('password')
        
        # Tentar encontrar usuário por email primeiro
        try:
            user = User.objects.get(email=username_or_email)
            # Se encontrou por email, usar o username real
            attrs['username'] = user.username
        except User.DoesNotExist:
            # Se não encontrou por email, tentar por username
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Usuário não encontrado")
        
        # Validar senha
        if not user.check_password(password):
            raise serializers.ValidationError("Senha incorreta")
        
        # Se chegou até aqui, login válido
        return super().validate(attrs) 