# apps/users/serializers.py
from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'date_joined', 'is_active']
        read_only_fields = ['id', 'date_joined']

class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'rol', 'telefono']

    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            rol=validated_data.get('rol', 'auxiliar'),
            telefono=validated_data.get('telefono'),
        )
        usuario.set_password(validated_data['password'])
        usuario.save()
        return usuario

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)