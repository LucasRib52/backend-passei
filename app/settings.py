# app/settings.py
from pathlib import Path
import os

# ========= Helpers =========
def env_bool(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "t", "yes", "y")

def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

# ========= Paths =========
BASE_DIR = Path(__file__).resolve().parent.parent

# ========= Básico / Segurança =========
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-ME-ONLY-FOR-LOCAL")
DEBUG = env_bool("DEBUG", "False")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

# Segurança extra para produção (ajuste via env se precisar desabilitar algo)
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "True")
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", "True")
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", "True")
    # Opcional: endureça headers (pode ajustar conforme sua app)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))  # ex.: "31536000"
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False")
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", "False")
else:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "False")
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", "False")
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", "False")

# ========= Apps =========
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Adicione seus apps aqui (ex.: "core", "usuarios", etc.)
]

# ========= Middleware =========
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ========= URLs / WSGI =========
ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"

# ========= Templates =========
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
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

# ========= Banco de Dados =========
# Configure via env:
# DB_ENGINE = django.db.backends.mysql | django.db.backends.sqlite3 | django.db.backends.postgresql
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.mysql").strip()

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "3306" if DB_ENGINE.endswith("mysql") else "5432"),
            # Opções úteis para MySQL no PythonAnywhere
            "OPTIONS": {
                **({"charset": "utf8mb4"} if DB_ENGINE.endswith("mysql") else {})
            },
        }
    }

# ========= Password Validators =========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========= I18N / TZ =========
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "pt-br")
TIME_ZONE = os.getenv("TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

# ========= Static / Media =========
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # `collectstatic` vai colocar aqui

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ========= Default Auto Field =========
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========= Logging (ajuste por env) =========
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{levelname}] {asctime} {name} :: {message}", "style": "{"},
        "simple": {"format": "[{levelname}] {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

# ========= Integrações externas =========
# --- TheMembers ---
# Em produção, normalmente use o endpoint de produção. Se ficar em branco, default é o dev.
THEMEMBERS_API_URL = os.getenv(
    "THEMEMBERS_API_URL",
    "https://registration.themembers.dev.br/api"
).rstrip("/")

THEMEMBERS_DEVELOPER_TOKEN = os.getenv("THEMEMBERS_DEVELOPER_TOKEN", "")
THEMEMBERS_DEVELOPER_ID = os.getenv("THEMEMBERS_DEVELOPER_ID", "")
THEMEMBERS_PLATFORM_TOKEN = os.getenv("THEMEMBERS_PLATFORM_TOKEN", "")
THEMEMBERS_PLATFORM_ID = os.getenv("THEMEMBERS_PLATFORM_ID", "")

# --- Asaas ---
# Defina ASAAS_ENVIRONMENT = "sandbox" ou "production"
ASAAS_ENVIRONMENT = os.getenv("ASAAS_ENVIRONMENT", "sandbox").strip().lower()
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")

if ASAAS_ENVIRONMENT == "production":
    ASAAS_BASE_URL = "https://www.asaas.com/api/v3"
else:
    ASAAS_BASE_URL = "https://sandbox.asaas.com/api/v3"

# ========= Dicas de configuração de ambiente (PythonAnywhere) =========
# No painel Web → Environment variables, defina por exemplo:
# SECRET_KEY=*** (rotacione!)
# DEBUG=False
# ALLOWED_HOSTS=cursopasseii.pythonanywhere.com
# CSRF_TRUSTED_ORIGINS=https://cursopasseii.pythonanywhere.com
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=cursopasseii$passei_db
# DB_USER=cursopasseii
# DB_PASSWORD=***
# DB_HOST=cursopasseii.mysql.pythonanywhere-services.com
# DB_PORT=3306
# THEMEMBERS_API_URL=<<<endpoint correto (dev ou prod) >>>
# THEMEMBERS_DEVELOPER_TOKEN=***
# THEMEMBERS_DEVELOPER_ID=***
# THEMEMBERS_PLATFORM_TOKEN=***
# THEMEMBERS_PLATFORM_ID=4072
# ASAAS_API_KEY=***
# ASAAS_ENVIRONMENT=production  (ou sandbox)
# LOG_LEVEL=INFO
