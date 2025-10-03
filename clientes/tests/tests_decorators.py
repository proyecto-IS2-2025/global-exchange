from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from clientes.decorators import require_permission
from clientes.models import AsignacionCliente, Cliente, Segmento


class RequirePermissionDecoratorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.factory = RequestFactory()
        cls.user = cls.User.objects.create_user(
            username="decorator_user",
            email="decorator@test.com",
            password="pass123",
        )
        cls.segmento = Segmento.objects.create(name="Segmento Decorator")
        cls.cliente = Cliente.objects.create(
            cedula="12345678",
            nombre_completo="Cliente Decorator",
            segmento=cls.segmento,
        )
        content_type = ContentType.objects.get_for_model(Cliente)
        cls.permission = Permission.objects.create(
            codename="can_use_decorator_test",
            name="Puede usar vista protegida por decorador",
            content_type=content_type,
        )
        cls.permission_fullname = f"{content_type.app_label}.{cls.permission.codename}"

    def setUp(self):
        @require_permission(self.permission_fullname)
        def protected_view(request):
            return "OK"

        @require_permission(self.permission_fullname, check_client_assignment=False)
        def protected_view_no_client(request):
            return "OK"

        self.protected_view = protected_view
        self.protected_view_no_client = protected_view_no_client

    def _request_with_session(self, cliente_id=None):
        request = self.factory.get("/")
        request.user = self.user
        session = self.client.session
        if cliente_id:
            session["cliente_activo_id"] = cliente_id
        else:
            session.pop("cliente_activo_id", None)
        session.save()
        request.session = session
        return request

    def test_denies_when_user_lacks_permission(self):
        titulo = "[TEST] Deniega acceso cuando el usuario no tiene el permiso requerido."
        print(f"\n{titulo}")
        try:
            request = self._request_with_session(self.cliente.id)
            with self.assertRaises(PermissionDenied):
                self.protected_view(request)
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_denies_when_user_not_assigned_to_cliente(self):
        titulo = "[TEST] Deniega acceso cuando el cliente activo no está asignado al usuario."
        print(f"\n{titulo}")
        try:
            self.user.user_permissions.add(self.permission)
            request = self._request_with_session(self.cliente.id)
            with self.assertRaises(PermissionDenied):
                self.protected_view(request)
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_allows_when_user_has_permission_and_assignment(self):
        titulo = "[TEST] Permite acceso con permiso y cliente asignado."
        print(f"\n{titulo}")
        try:
            self.user.user_permissions.add(self.permission)
            AsignacionCliente.objects.create(usuario=self.user, cliente=self.cliente)
            request = self._request_with_session(self.cliente.id)
            self.assertEqual(self.protected_view(request), "OK")
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_allows_without_assignment_when_flag_disabled(self):
        titulo = "[TEST] Permite acceso sin asignación cuando check_client_assignment=False."
        print(f"\n{titulo}")
        try:
            self.user.user_permissions.add(self.permission)
            request = self._request_with_session()
            self.assertEqual(self.protected_view_no_client(request), "OK")
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")