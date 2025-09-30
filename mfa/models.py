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