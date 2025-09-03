"""
Configurações da API TheMembers
"""
from django.conf import settings

# Configurações da API
THEMEMBERS_API_URL = getattr(settings, 'THEMEMBERS_API_URL', 'https://registration.themembers.dev.br/api')
THEMEMBERS_DEVELOPER_TOKEN = getattr(settings, 'THEMEMBERS_DEVELOPER_TOKEN', 'c8ba2c31-3129-40ed-88cb-04e0f305d8d9')
THEMEMBERS_DEVELOPER_ID = getattr(settings, 'THEMEMBERS_DEVELOPER_ID', '097493d3-680d-439f-a405-0c50f132582a')
THEMEMBERS_PLATFORM_TOKEN = getattr(settings, 'THEMEMBERS_PLATFORM_TOKEN', 'c9012a5e-13c1-48ae-bfa9-584ff4a56c13')
THEMEMBERS_PLATFORM_ID = getattr(settings, 'THEMEMBERS_PLATFORM_ID', '4072')

# Endpoints da API
ENDPOINTS = {
    'products': f'/products/all-products/{THEMEMBERS_DEVELOPER_TOKEN}/{THEMEMBERS_PLATFORM_TOKEN}',
    'users': '/users',
    'subscriptions': '/subscriptions',
}

# Headers padrão para autenticação
DEFAULT_HEADERS = {
    'Authorization': f'Bearer {THEMEMBERS_PLATFORM_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# Configurações de retry
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # segundos

# Timeout das requisições
REQUEST_TIMEOUT = 30  # segundos
