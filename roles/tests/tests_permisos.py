from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
import re


class PermissionAssignmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("sync_permissions", verbosity=0)
        cls.sample_perm = Permission.objects.select_related("content_type").filter(metadata__isnull=False).first()
        if cls.sample_perm is None:
            raise AssertionError("Se requiere al menos un permiso con metadata para ejecutar estas pruebas.")
        cls.perm_codename = cls.sample_perm.codename
        cls.perm_fullname = f"{cls.sample_perm.content_type.app_label}.{cls.sample_perm.codename}"
        cls.UserModel = get_user_model()

    def _create_user(self, suffix):
        return self.UserModel.objects.create_user(
            username=f"user_{suffix}",
            email=f"user_{suffix}@example.com",
            password="pass123",
        )

    def test_assign_permission_via_group(self):
        titulo = "[TEST] Asignación de un permiso a través de un grupo y verificación en el usuario."
        print(f"\n{titulo}")
        try:
            user = self._create_user("group_assign")
            group = Group.objects.create(name="Operador Test")
            group.permissions.add(self.sample_perm)
            user.groups.add(group)

            self.assertTrue(user.has_perm(self.perm_fullname))
            self.assertIn(self.sample_perm, group.permissions.all())
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_remove_permission_from_group(self):
        titulo = "[TEST] Revocación de un permiso quitándolo del grupo asignado al usuario."
        print(f"\n{titulo}")
        try:
            user = self._create_user("group_remove")
            group = Group.objects.create(name="Operador Remove")
            group.permissions.add(self.sample_perm)
            user.groups.add(group)
            self.assertTrue(user.has_perm(self.perm_fullname))

            group.permissions.remove(self.sample_perm)
            user = self.UserModel.objects.get(pk=user.pk)  # refrescar
            self.assertFalse(user.has_perm(self.perm_fullname))
            self.assertNotIn(self.sample_perm, group.permissions.all())
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_assign_direct_permission_to_user(self):
        titulo = "[TEST] Asignación directa de un permiso al usuario."
        print(f"\n{titulo}")
        try:
            user = self._create_user("direct_assign")
            user.user_permissions.add(self.sample_perm)
            user = self.UserModel.objects.get(pk=user.pk)

            self.assertTrue(user.has_perm(self.perm_fullname))
            self.assertIn(self.sample_perm, user.user_permissions.all())
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_remove_direct_permission_from_user(self):
        titulo = "[TEST] Eliminación de un permiso asignado directamente al usuario."
        print(f"\n{titulo}")
        try:
            user = self._create_user("direct_remove")
            user.user_permissions.add(self.sample_perm)
            self.assertTrue(user.has_perm(self.perm_fullname))

            user.user_permissions.remove(self.sample_perm)
            user = self.UserModel.objects.get(pk=user.pk)
            self.assertFalse(user.has_perm(self.perm_fullname))
            self.assertNotIn(self.sample_perm, user.user_permissions.all())
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")

    def test_sync_permissions_command_idempotent(self):
        titulo = "[TEST] Reejecución del comando sync_permissions para confirmar idempotencia."
        print(f"\n{titulo}")
        try:
            before = Permission.objects.count()
            buf = StringIO()
            call_command("sync_permissions", stdout=buf, verbosity=1)
            after = Permission.objects.count()

            self.assertEqual(before, after)
            clean_output = re.sub(r"\x1b\[[0-9;]*m", "", buf.getvalue())
            self.assertIn("Sincronización completa:", clean_output)
        except AssertionError:
            print(f"[X] {titulo}")
            raise
        else:
            print(f"[✓] {titulo}")