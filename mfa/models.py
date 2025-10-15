# mfa/models.py

from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

class OTPCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otp_codes',
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=['user'])]
        get_latest_by = 'created_at'

    def save(self, *args, **kwargs):
        if not self.id or self._state.adding:
            # 5 minutos de caducidad
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Verifica si el código está activo y no ha expirado."""
        return self.is_active and (self.expires_at > timezone.now())


class MFAConfig(models.Model):
    """
    Configuración global de MFA.
    Solo debe existir un registro (singleton).
    """
    mfa_login_enabled = models.BooleanField(
        default=True,
        verbose_name="MFA en Login",
        help_text="Activar verificación MFA al iniciar sesión"
    )
    mfa_compra_enabled = models.BooleanField(
        default=True,
        verbose_name="MFA en Compra",
        help_text="Activar verificación MFA al confirmar una compra"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mfa_config_updates'
    )

    class Meta:
        verbose_name = "Configuración MFA"
        verbose_name_plural = "Configuración MFA"

    def __str__(self):
        return f"MFA Config (Login: {self.mfa_login_enabled}, Compra: {self.mfa_compra_enabled})"

    @classmethod
    def get_config(cls):
        """Obtiene o crea la configuración (singleton)."""
        config, created = cls.objects.get_or_create(pk=1)
        return config

    def save(self, *args, **kwargs):
        self.pk = 1  # Forzar PK=1 para singleton
        super().save(*args, **kwargs)