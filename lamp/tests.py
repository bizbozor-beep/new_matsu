from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import RobloxUser


class AccountFlowTests(TestCase):
    def test_signup_creates_hashed_password_and_redirects_to_login(self):
        response = self.client.post(
            "/signup/",
            {
                "username": "testuser",
                "password1": "StrongPassword!908",
                "password2": "StrongPassword!908",
            },
        )

        self.assertRedirects(response, "/login/")
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        created_user = get_user_model().objects.get(username="testuser")
        self.assertTrue(created_user.check_password("StrongPassword!908"))
        self.assertNotEqual(created_user.password, "StrongPassword!908")

    def test_login_protects_home_and_logout_requires_login_again(self):
        get_user_model().objects.create_user(
            username="testuser",
            password="StrongPassword!908",
        )

        self.assertRedirects(self.client.get("/"), "/login/?next=/")

        login_response = self.client.post(
            "/login/",
            {"username": "testuser", "password": "StrongPassword!908"},
        )
        self.assertRedirects(login_response, "/")
        self.assertEqual(self.client.get("/").status_code, 200)

        logout_response = self.client.post("/logout/")
        self.assertRedirects(logout_response, "/login/")
        self.assertRedirects(self.client.get("/"), "/login/?next=/")

    def test_tournament_registration_is_saved_and_requires_login(self):
        response = self.client.post(
            "/",
            {
                "Roblox_username": "Builder123",
                "roblox_email": "builder@example.com",
                "phone_number": "+998901234567",
            },
        )
        self.assertRedirects(response, "/login/?next=/")
        self.assertEqual(RobloxUser.objects.count(), 0)

        get_user_model().objects.create_user(
            username="tournamentuser",
            password="StrongPassword!908",
        )
        self.client.login(username="tournamentuser", password="StrongPassword!908")

        response = self.client.post(
            "/",
            {
                "Roblox_username": "Builder123",
                "roblox_email": "builder@example.com",
                "phone_number": "+998901234567",
            },
        )

        self.assertRedirects(response, "/")
        registration = RobloxUser.objects.get()
        self.assertEqual(registration.Roblox_username, "Builder123")
        self.assertEqual(registration.roblox_email, "builder@example.com")
        self.assertEqual(registration.phone_number, "+998901234567")
        self.assertEqual(registration.user.username, "tournamentuser")

        second_response = self.client.post(
            "/",
            {
                "Roblox_username": "SecondBuilder",
                "roblox_email": "second@example.com",
                "phone_number": "+998991234567",
            },
        )
        self.assertRedirects(second_response, "/")
        self.assertEqual(
            RobloxUser.objects.filter(user__username="tournamentuser").count(),
            2,
        )

    def test_user_can_edit_their_registration(self):
        user = get_user_model().objects.create_user(
            username="edituser",
            password="StrongPassword!908",
        )
        registration = RobloxUser.objects.create(
            user=user,
            Roblox_username="OldName",
            roblox_email="old@example.com",
            phone_number="+998901234567",
        )
        self.client.login(username="edituser", password="StrongPassword!908")

        edit_page = self.client.get(f"/?edit={registration.pk}")
        self.assertEqual(edit_page.status_code, 200)
        self.assertContains(edit_page, 'value="OldName"')
        self.assertContains(edit_page, 'value="old@example.com"')

        response = self.client.post(
            "/",
            {
                "registration_id": registration.pk,
                "Roblox_username": "UpdatedName",
                "roblox_email": "updated@example.com",
                "phone_number": "+998991112233",
            },
        )

        self.assertRedirects(response, "/")
        registration.refresh_from_db()
        self.assertEqual(registration.Roblox_username, "UpdatedName")
        self.assertEqual(registration.roblox_email, "updated@example.com")
        self.assertEqual(registration.phone_number, "+998991112233")
        self.assertEqual(RobloxUser.objects.count(), 1)

    def test_user_can_add_and_edit_multiple_registrations(self):
        user = get_user_model().objects.create_user(
            username="multiuser",
            password="StrongPassword!908",
        )
        self.client.login(username="multiuser", password="StrongPassword!908")

        for username in ("PlayerOne", "PlayerTwo"):
            response = self.client.post(
                "/",
                {
                    "Roblox_username": username,
                    "roblox_email": f"{username.lower()}@example.com",
                    "phone_number": "+998901234567",
                },
            )
            self.assertRedirects(response, "/")

        registrations = list(RobloxUser.objects.filter(user=user).order_by("id"))
        self.assertEqual(len(registrations), 2)
        self.assertContains(self.client.get("/"), "Yana akkaunt qo'shish")

        response = self.client.get(f"/?edit={registrations[1].pk}")
        self.assertContains(response, 'value="PlayerTwo"')

        self.client.post(
            "/",
            {
                "registration_id": registrations[1].pk,
                "Roblox_username": "UpdatedPlayerTwo",
                "roblox_email": "updated@example.com",
                "phone_number": "+998991112233",
            },
        )
        registrations[0].refresh_from_db()
        registrations[1].refresh_from_db()
        self.assertEqual(registrations[0].Roblox_username, "PlayerOne")
        self.assertEqual(registrations[1].Roblox_username, "UpdatedPlayerTwo")
        self.assertEqual(RobloxUser.objects.filter(user=user).count(), 2)

        other_user = get_user_model().objects.create_user(
            username="otherowner",
            password="StrongPassword!908",
        )
        self.client.force_login(other_user)
        self.assertEqual(
            self.client.get(f"/?edit={registrations[0].pk}").status_code,
            404,
        )

    def test_users_do_not_see_unlinked_legacy_registrations_as_their_own(self):
        RobloxUser.objects.create(
            Roblox_username="UnlinkedParticipant",
            roblox_email="unlinked@example.com",
            phone_number="+998901234567",
        )
        get_user_model().objects.create_user(
            username="anotheruser",
            password="StrongPassword!908",
        )
        self.client.login(username="anotheruser", password="StrongPassword!908")

        response = self.client.get("/?add=1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Akkauntni qo'shish")
        self.assertNotContains(response, "UnlinkedParticipant")

    def test_admin_can_edit_participant_from_matsu_list(self):
        participant = RobloxUser.objects.create(
            Roblox_username="NeedsCorrection",
            roblox_email="wrong@example.com",
            phone_number="+998901234567",
        )
        admin = get_user_model().objects.create_superuser(
            username="editadmin",
            email="editadmin@example.com",
            password="AdminPassword!908",
        )
        self.client.login(username=admin.username, password="AdminPassword!908")

        self.client.post("/matsu/", {"password": "AdminPassword!908"})
        response = self.client.get("/matsu/")
        self.assertContains(
            response,
            f'href="/matsu/{participant.pk}/edit/"',
        )

        edit_response = self.client.get(f"/matsu/{participant.pk}/edit/")
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, 'value="wrong@example.com"')

        save_response = self.client.post(
            f"/matsu/{participant.pk}/edit/",
            {
                "Roblox_username": "CorrectedName",
                "roblox_email": "correct@example.com",
                "phone_number": "+998991112233",
            },
        )
        self.assertRedirects(save_response, "/matsu/")
        participant.refresh_from_db()
        self.assertEqual(participant.Roblox_username, "CorrectedName")
        self.assertEqual(participant.roblox_email, "correct@example.com")
        self.assertEqual(participant.phone_number, "+998991112233")

    def test_participant_edit_requires_admin_confirmation(self):
        participant = RobloxUser.objects.create(
            Roblox_username="PrivateParticipant",
            roblox_email="private@example.com",
            phone_number="+998901234567",
        )
        get_user_model().objects.create_superuser(
            username="unconfirmedadmin",
            email="unconfirmed@example.com",
            password="AdminPassword!908",
        )
        self.client.login(username="unconfirmedadmin", password="AdminPassword!908")

        response = self.client.get(f"/matsu/{participant.pk}/edit/")

        self.assertRedirects(response, "/matsu/")

    def test_matsu_requires_staff_and_password_to_show_participant_details(self):
        RobloxUser.objects.create(
            Roblox_username="VisibleRobloxName",
            roblox_email="private@example.com",
            phone_number="+998901234567",
        )

        response = self.client.get("/matsu/")
        self.assertRedirects(response, "/login/?next=/matsu/")

        get_user_model().objects.create_user(
            username="rosteruser",
            password="RosterAdmin!908",
        )
        self.client.login(username="rosteruser", password="RosterAdmin!908")
        self.assertRedirects(
            self.client.get("/matsu/"),
            "/admin/login/?next=/matsu/",
        )

        get_user_model().objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="AdminPassword!908",
        )
        self.client.logout()
        self.client.login(username="adminuser", password="AdminPassword!908")

        response = self.client.get("/matsu/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin akkaunti paroli")
        self.assertNotContains(response, "VisibleRobloxName")

        wrong_password_response = self.client.post(
            "/matsu/",
            {"password": "wrong-password"},
        )
        self.assertEqual(wrong_password_response.status_code, 200)
        self.assertIn(
            "Parol noto'g'ri.",
            wrong_password_response.context["form"].errors["password"],
        )
        self.assertNotContains(wrong_password_response, "private@example.com")

        response = self.client.post(
            "/matsu/",
            {"password": "AdminPassword!908"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VisibleRobloxName")
        self.assertContains(response, "private@example.com")
        self.assertContains(response, "+998901234567")
        self.assertNotContains(response, "AdminPassword!908")

    def test_json_export_includes_phone_only_when_selected(self):
        RobloxUser.objects.create(
            Roblox_username="JsonPlayer",
            roblox_email="json@example.com",
            phone_number="+998901234567",
        )
        get_user_model().objects.create_superuser(
            username="jsonadmin",
            email="jsonadmin@example.com",
            password="AdminPassword!908",
        )
        self.client.login(username="jsonadmin", password="AdminPassword!908")

        self.client.post(
            "/matsu/",
            {"password": "AdminPassword!908"},
        )
        without_phone = self.client.post(
            "/matsu/",
            {"action": "export"},
        )
        self.assertEqual(without_phone.status_code, 200)
        self.assertEqual(
            without_phone.json(),
            [{"roblox_username": "JsonPlayer", "email": "json@example.com"}],
        )
        self.assertIn("attachment;", without_phone["Content-Disposition"])
        self.assertIn("no-store", without_phone["Cache-Control"])

        with_phone = self.client.post(
            "/matsu/",
            {
                "action": "export",
                "include_phone": "on",
            },
        )
        self.assertEqual(
            with_phone.json(),
            [
                {
                    "roblox_username": "JsonPlayer",
                    "email": "json@example.com",
                    "phone_number": "+998901234567",
                }
            ],
        )
