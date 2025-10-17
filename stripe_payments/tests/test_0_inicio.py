"""
Test inicial que imprime banner de inicio
"""
from django.test import TestCase


class TestInicio(TestCase):
    """Imprime mensaje de inicio de tests"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "=" * 70)
        print("🚀 INICIANDO SUITE DE TESTS - stripe_payments".center(70))
        print("=" * 70)
        print("\n📋 Tests a ejecutar:")
        print("   • test_models.py    - Tests de modelos StripeTransaction")
        print("   • test_services.py  - Tests de servicios de pago")
        print("   • test_webhooks.py  - Tests de webhooks de Stripe")
        print("\n" + "=" * 70 + "\n")
    
    def test_inicio(self):
        """Test dummy para iniciar la suite"""
        self.assertTrue(True)
