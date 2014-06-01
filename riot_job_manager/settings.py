"""
Django settings for riot_job_manager project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ebm!xgdgb-uslg3s-w##z4e3s*k^(kkp5s@9=%6bpme_40dat-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social.apps.django_app.default',
    'bootstrap3',
    'board_app_creator',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.github.GithubOrganizationOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = "/jobs"
LOGIN_URL = "/jobs/social_auth/login/github-org/"
LOGOUT_URL = "/jobs/logout"

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'riot_job_manager.urls'

WSGI_APPLICATION = 'riot_job_manager.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

SOCIAL_AUTH_GITHUB_ORG_KEY = '05cadf9099144536e910'
SOCIAL_AUTH_GITHUB_ORG_SECRET = '9b05256f76a3affeb7fbc252f6b2482fe1a9c416'
SOCIAL_AUTH_GITHUB_ORG_NAME = 'RIOT-OS'
SOCIAL_AUTH_GITHUB_ORG_SCOPE = ['read:org']

JENKINS_JOBS_PATH = '/var/lib/jenkins/jobs'

RIOT_DEFAULT_PAGINATION = 20
RIOT_REPO_BASE_PATH = os.environ['HOME']
RIOT_DEFAULT_APPLICATIONS = ['default']
RIOT_DEFAULT_BOARDS = ['msba2']
