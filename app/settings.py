"""
Django settings for app project (prod-ready p/ PythonAnywhere).
"""

import os
from pathlib import Path
from datetime import timedelta

# ===================== Paths =====================
BASE_DIR = Path(__file__).resolve().parent.parent

# ===================== Helpers =====================
def env_bool(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "t", "yes", "y")

def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]

# ===================== Segurança / Básico =====================
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-ME-LOCAL-ONLY")
DEBUG = env_bool("DEBUG", "True")  # local por padrão; em prod, defina DEBUG=False no WSGI ou no painel

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "*")
# Ex.: ALLOWED_HOSTS=cursopasseii.pythonanywhere.com

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
# Ex.: CSRF_TRUSTED_ORIGINS=https://cursopasseii.pythonanywhere.com

# Endurece cookies/SSL em produção
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "True")
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", "True")
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", "True")
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))  # ex.: 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False")
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", "False")
else:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "False")
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", "False")
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", "False")

APPEND_SLASH = True

# ===================== Apps =====================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceiros
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_filters",  # necessário pois você usa DjangoFilterBackend

    # Seus apps
    "courses",
    "professors",
    "testimonials",
    "news",
    "sales",
    "users",
    "themembers",
    "integration_asas",
    "dashboard",
    "course_reviews",
]

# ===================== Middleware =====================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # tem que vir antes de CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ===================== URLs / WSGI =====================
ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"

# ===================== Templates =====================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ===================== Database (MySQL por env) =====================
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.getenv("DB_NAME", "cursopasseii$passei_db"),
        "USER": os.getenv("DB_USER", "cursopasseii"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "cursopasseii.mysql.pythonanywhere-services.com"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ===================== Password validators =====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===================== I18N / TZ =====================
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en-us")
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# ===================== Static / Media =====================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===================== Email =====================
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Cursos Passei <no-reply@cursopassei.com>")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")) if EMAIL_HOST else 587
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", "True")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

# ===================== DRF / JWT =====================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=int(os.getenv("JWT_REFRESH_HOURS", "24"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ===================== CORS =====================
# Override via env: CORS_ALLOWED_ORIGINS=https://seu-front.app,https://outro.site
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:8080,http://127.0.0.1:8080,"
    "http://192.168.1.67:8080,http://192.168.1.67:5173,http://192.168.1.67:3000,"
    "https://frontend-passei.vercel.app"
)
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", "True")

CORS_ALLOW_HEADERS = env_list(
    "CORS_ALLOW_HEADERS",
    "accept,accept-encoding,authorization,content-type,dnt,origin,user-agent,x-csrftoken,x-requested-with"
)
CORS_ALLOW_METHODS = env_list(
    "CORS_ALLOW_METHODS",
    "DELETE,GET,OPTIONS,PATCH,POST,PUT"
)

# ===================== DRF Spectacular =====================
SPECTACULAR_SETTINGS = {
    "TITLE": os.getenv("OPENAPI_TITLE", "Passei API"),
    "DESCRIPTION": os.getenv("OPENAPI_DESCRIPTION", "API para o sistema Passei - Plataforma de cursos"),
    "VERSION": os.getenv("OPENAPI_VERSION", "1.0.0"),
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
}

# ===================== Integrações: TheMembers =====================
THEMEMBERS_API_URL = os.getenv(
    "THEMEMBERS_API_URL",
    "https://registration.themembers.dev.br/api"
).rstrip("/")
THEMEMBERS_DEVELOPER_TOKEN = os.getenv("THEMEMBERS_DEVELOPER_TOKEN", "")
THEMEMBERS_DEVELOPER_ID = os.getenv("THEMEMBERS_DEVELOPER_ID", "")
THEMEMBERS_PLATFORM_TOKEN = os.getenv("THEMEMBERS_PLATFORM_TOKEN", "")
THEMEMBERS_PLATFORM_ID = os.getenv("THEMEMBERS_PLATFORM_ID", "")

# ===================== Integrações: Asaas =====================
ASAAS_ENVIRONMENT = os.getenv("ASAAS_ENVIRONMENT", "sandbox").strip().lower()  # 'sandbox' | 'production'
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")
ASAAS_BASE_URL = "https://www.asaas.com/api/v3" if ASAAS_ENVIRONMENT == "production" else "https://sandbox.asaas.com/api/v3"

# ===================== Logging básico (útil pra depurar em prod) =====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}
