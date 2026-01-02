"""
Django settings for mycompany project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-change-this-key-to-something-secure'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'employees',
    'django.contrib.humanize',
    'import_export',
    'sales',
    
    # ✅ เพิ่มบรรทัดนี้ครับ: ระบบฐานข้อมูลลูกค้า
    'customers',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mycompany.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'employees.context_processors.company_global',
            ],
        },
    },
]

WSGI_APPLICATION = 'mycompany.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'JCNeed1975$hr_db',    # ชื่อ Database
        'USER': 'JCNeed1975',          # Username
        'PASSWORD': 'HrSystem2025',    # Password
        'HOST': 'JCNeed1975.mysql.pythonanywhere-services.com', # Host
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (Images)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# ตั้งค่าการล็อกอิน/ล็อกเอาท์
# ==========================================
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = '/'

# ==========================================
# 📅 การตั้งค่าวันที่ (Date Format)
# ==========================================
DATE_INPUT_FORMATS = ['%d/%m/%Y']
USE_L10N = False 
DATE_FORMAT = 'd/m/Y'