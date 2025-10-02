# mfa/tests.py

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from mfa.models import OTPCode
from mfa.utils import generate_and_send_otp, check_otp_validity, MASTER_CODE

import traceback
import sys
from functools import wraps

User = get_user_model()

# Colores ANSI para la terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def report(fn):
    """Decorador mejorado para imprimir resultados de tests con formato."""
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        test_name = f"{self.__class__.__name__}.{fn.__name__}"
        
        # Obtener la descripción del test (docstring)
        description = fn.__doc__.strip() if fn.__doc__ else "Sin descripción"
        
        try:
            fn(self, *args, **kwargs)
            # Test exitoso
            print(f"\n{Colors.GREEN}✓ PASS{Colors.RESET} {Colors.BOLD}{test_name}{Colors.RESET}")
            print(f"  {Colors.CYAN}→{Colors.RESET} {description}")
            
        except Exception as e:
            # Test fallido
            print(f"\n{Colors.RED}✗ FAIL{Colors.RESET} {Colors.BOLD}{test_name}{Colors.RESET}")
            print(f"  {Colors.CYAN}→{Colors.RESET} {description}")
            print(f"  {Colors.RED}Error:{Colors.RESET} {str(e)}")
            print(f"  {Colors.YELLOW}Traceback:{Colors.RESET}")
            
            # Imprimir solo las líneas relevantes del traceback
            tb_lines = traceback.format_exc().split('\n')
            for line in tb_lines:
                if line.strip():
                    print(f"    {line}")
            raise
    return wrapper


class MFAUtilityTests(TestCase):
    """
    Pruebas para las funciones de utilidad en mfa/utils.py
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}  SUITE: MFAUtilityTests - Pruebas de Utilidades MFA{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    
    def setUp(self):
        # Crear un usuario de prueba
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123'
        )

    @report
    @patch('mfa.utils.send_mail')
    def test_generate_and_send_otp_success(self, mock_send_mail):
        """Genera un nuevo código OTP y envía el correo correctamente"""
        
        # 1. Ejecutar la función
        result = generate_and_send_otp(self.user)
        
        # 2. Asertos
        self.assertTrue(result)
        self.assertEqual(OTPCode.objects.filter(user=self.user, is_active=True).count(), 1)
        mock_send_mail.assert_called_once()
        
        latest_code = OTPCode.objects.get(user=self.user)
        self.assertEqual(len(latest_code.code), 6)

    @report
    @patch('mfa.utils.send_mail')
    def test_generate_and_send_otp_invalidates_previous_codes(self, mock_send_mail):
        """Invalida todos los códigos activos anteriores al generar uno nuevo"""
        
        # 1. Crear un código activo anterior
        OTPCode.objects.create(user=self.user, code='111111')
        self.assertEqual(OTPCode.objects.filter(user=self.user, is_active=True).count(), 1)
        
        # 2. Generar un nuevo código
        generate_and_send_otp(self.user)
        
        # 3. Asertos
        self.assertEqual(OTPCode.objects.filter(user=self.user, is_active=False).count(), 1)
        self.assertEqual(OTPCode.objects.filter(user=self.user, is_active=True).count(), 1)

    @report
    def test_check_otp_validity_master_code(self):
        """Verifica que el código maestro (000000) siempre funciona"""
        
        self.assertTrue(check_otp_validity(self.user, MASTER_CODE))
        self.assertEqual(OTPCode.objects.filter(user=self.user).count(), 0)

    @report
    def test_check_otp_validity_success(self):
        """Valida correctamente un código activo y lo marca como inactivo después del uso"""
        
        # 1. Crear un código activo y válido
        valid_code = '987654'
        OTPCode.objects.create(user=self.user, code=valid_code)
        
        # 2. Ejecutar la verificación
        self.assertTrue(check_otp_validity(self.user, valid_code))
        
        # 3. Asertos (Debe estar inactivo después de su uso)
        active_code = OTPCode.objects.get(user=self.user, code=valid_code)
        self.assertFalse(active_code.is_active)

    @report
    def test_check_otp_validity_fail_incorrect_code(self):
        """Rechaza correctamente un código incorrecto"""
        
        valid_code = '123456'
        OTPCode.objects.create(user=self.user, code=valid_code)
        
        self.assertFalse(check_otp_validity(self.user, '000001'))

    @report
    def test_check_otp_validity_fail_inactive_code(self):
        """Rechaza un código que ya fue usado (marcado como inactivo)"""
        
        used_code = '555555'
        OTPCode.objects.create(user=self.user, code=used_code, is_active=False)
        
        self.assertFalse(check_otp_validity(self.user, used_code))

    @report
    def test_check_otp_validity_fail_expired_code(self):
        """Rechaza correctamente un código que ha expirado"""
        
        expired_code = '666666'
        expired_otp = OTPCode.objects.create(user=self.user, code=expired_code)
        expired_otp.expires_at = timezone.now() - timedelta(minutes=1) 
        expired_otp.save()
        
        self.assertFalse(check_otp_validity(self.user, expired_code))


class OTPCodeModelTests(TestCase):
    """
    Pruebas para el modelo OTPCode en mfa/models.py
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}  SUITE: OTPCodeModelTests - Pruebas del Modelo OTPCode{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser', 
            email='model@example.com', 
            password='password123'
        )

    @report
    def test_otp_code_expiration_set_on_creation(self):
        """Establece automáticamente la expiración a 5 minutos al crear el código"""
        
        five_minutes = timedelta(minutes=5)
        
        with self.assertNumQueries(1):
            code = OTPCode.objects.create(user=self.user, code='111222')
            
        self.assertGreater(code.expires_at, timezone.now())
        
        time_difference = code.expires_at - code.created_at
        self.assertTrue(abs(time_difference - five_minutes) < timedelta(seconds=1))

    @report
    def test_is_valid_method_active_and_fresh(self):
        """El método is_valid() retorna True para códigos activos y no expirados"""
        
        code = OTPCode.objects.create(user=self.user, code='111222')
        self.assertTrue(code.is_valid())

    @report
    def test_is_valid_method_inactive(self):
        """El método is_valid() retorna False para códigos marcados como inactivos"""
        
        code = OTPCode.objects.create(user=self.user, code='111222', is_active=False)
        self.assertFalse(code.is_valid())

    @report
    def test_is_valid_method_expired(self):
        """El método is_valid() retorna False para códigos que han expirado"""
        
        code = OTPCode.objects.create(user=self.user, code='111222')
        code.expires_at = timezone.now() - timedelta(seconds=1)
        code.save()
        
        self.assertFalse(code.is_valid())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}  ✓ Todas las pruebas completadas{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}\n")