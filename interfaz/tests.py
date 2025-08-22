
# interfaz/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from .forms import RegistroForm
from .models import PerfilUsuario

User = get_user_model()


class RegistroFormTests(TestCase):
    def test_form_valido_cuando_las_contrasenas_coinciden(self):
        form = RegistroForm(
            data={
                "username": "isaac",
                "email": "isaac@example.com",
                "password": "Secreta123!",
                "confirmar_password": "Secreta123!",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalido_cuando_las_contrasenas_no_coinciden(self):
        form = RegistroForm(
            data={
                "username": "isaac",
                "email": "isaac@example.com",
                "password": "Secreta123!",
                "confirmar_password": "OtraClave999!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Las contraseñas no coinciden.", form.errors["__all__"])

    def test_form_usa_campos_correctos(self):
        self.assertEqual(RegistroForm.Meta.fields, ["username", "email", "password"])


class RegistroViewTests(TestCase):
    def setUp(self):
        self.url_registro = reverse("registro")
        self.url_login = reverse("login")

    def test_get_registro_200(self):
        resp = self.client.get(self.url_registro)
        self.assertEqual(resp.status_code, 200)

    def test_post_crea_usuario_inactivo_y_perfil(self):
        payload = {
            "nombre": "Isaac Test",
            "email": "isaac@example.com",
            "telefono": "0981000000",
            "password": "Secreta123!",
        }
        resp = self.client.post(self.url_registro, data=payload, follow=True)
        self.assertRedirects(resp, self.url_login)

        user = User.objects.get(email="isaac@example.com")
        self.assertFalse(user.is_active)

        perfil = PerfilUsuario.objects.get(usuario=user)
        self.assertEqual(perfil.nombre_completo, "Isaac Test")
        self.assertEqual(perfil.telefono, "0981000000")

        messages = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("Registro exitoso" in m for m in messages))

    def test_post_email_duplicado_muestra_error(self):
        User.objects.create_user(
            username="yaexiste@example.com",
            email="yaexiste@example.com",
            password="abc12345",
        )
        payload = {
            "nombre": "Otro",
            "email": "yaexiste@example.com",
            "telefono": "0981111111",
            "password": "Secreta123!",
        }
        resp = self.client.post(self.url_registro, data=payload)
        self.assertEqual(resp.status_code, 200)
        messages = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("Ya existe un usuario con ese correo" in m for m in messages))


class VerificacionCorreoTests(TestCase):
    def setUp(self):
        self.url_login = reverse("login")



class LoginFlowTests(TestCase):
    def setUp(self):
        self.url_login = reverse("login")
        self.url_dashboard = reverse("dashboard")
        self.user = User.objects.create_user(
            username="isaac@example.com",
            email="isaac@example.com",
            password="Secreta123!",
            is_active=False,
        )

    def test_login_falla_si_usuario_inactivo(self):
        logged = self.client.login(
            username="isaac@example.com", password="Secreta123!"
        )
        self.assertFalse(logged)



    def test_dashboard_redirige_si_no_autenticado(self):
        self.client.logout()
        resp = self.client.get(self.url_dashboard)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)
}
