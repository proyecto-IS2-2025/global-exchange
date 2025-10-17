"""
Configuración de tests para stripe_payments con autenticación simplificada
"""
from django.test import TestCase, override_settings


@override_settings(
    # Desactivar middleware de MFA para tests
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
)
class StripePaymentsTestCase(TestCase):
    """
    TestCase base para stripe_payments que desactiva middleware de MFA
    """
    pass
