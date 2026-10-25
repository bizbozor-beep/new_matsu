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

    def test_registration_requires_roblox_and_telegram_usernames(self):
        response = self.client.post(
            "/",
            {"Roblox_username": "Builder123", "telegram_username": "@builder"},
        )
        self.assertRedirects(response, "/login/?next=/")
        self.assertEqual(RobloxUser.objects.count(), 0)

        user = get_user_model().objects.create_user(
            username="tournamentuser",
            password="StrongPassword!908",
        )
        self.client.login(username=user.username, password="StrongPassword!908")

        response = self.client.post("/", {"Roblox_username": "Builder123"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Telegram username")
        self.assertEqual(RobloxUser.objects.count(), 0)

        response = self.client.post(
            "/",
            {"Roblox_username": "Builder123", "telegram_username": "@builder"},
        )
        self.assertRedirects(response, "/")

        registration = RobloxUser.objects.get()
        self.assertEqual(registration.Roblox_username, "Builder123")
        self.assertEqual(registration.telegram_username, "@builder")
        self.assertEqual(registration.user, user)

    def test_user_can_add_multiple_registrations_and_edit_one(self):
        user = get_user_model().objects.create_user(
            username="multiuser",
            password="StrongPassword!908",
        )
        self.client.login(username=user.username, password="StrongPassword!908")

        for roblox_name, telegram_name in (
            ("PlayerOne", "@player_one"),
            ("PlayerTwo", "@player_two"),
        ):
            response = self.client.post(
                "/",
                {
                    "Roblox_username": roblox_name,
                    "telegram_username": telegram_name,
                },
            )
            self.assertRedirects(response, "/")

        registrations = list(RobloxUser.objects.filter(user=user).order_by("id"))
        self.assertEqual(len(registrations), 2)
        self.assertContains(self.client.get("/"), "Yana akkaunt qo'shish")

        response = self.client.get(f"/?edit={registrations[1].pk}")
        self.assertContains(response, 'value="PlayerTwo"')
        self.assertContains(response, 'value="@player_two"')

        response = self.client.post(
            "/",
            {
                "registration_id": registrations[1].pk,
                "Roblox_username": "UpdatedPlayerTwo",
                "telegram_username": "@updated_player",
            },
        )
        self.assertRedirects(response, "/")
        registrations[0].refresh_from_db()
        registrations[1].refresh_from_db()
        self.assertEqual(registrations[0].Roblox_username, "PlayerOne")
        self.assertEqual(registrations[1].Roblox_username, "UpdatedPlayerTwo")
        self.assertEqual(registrations[1].telegram_username, "@updated_player")
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

    def test_unlinked_legacy_registration_is_not_exposed_to_other_users(self):
        RobloxUser.objects.create(
            Roblox_username="UnlinkedParticipant",
            telegram_username="",
        )
        user = get_user_model().objects.create_user(
            username="anotheruser",
            password="StrongPassword!908",
        )
        self.client.login(username=user.username, password="StrongPassword!908")

        response = self.client.get("/?add=1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Akkauntni qo'shish")
        self.assertNotContains(response, "UnlinkedParticipant")

    def test_admin_can_edit_participant_from_matsu_list(self):
        participant = RobloxUser.objects.create(
            Roblox_username="NeedsCorrection",
            telegram_username="@wrong_username",
        )
        admin = get_user_model().objects.create_superuser(
            username="editadmin",
            email="editadmin@example.com",
            password="AdminPassword!908",
        )
        self.client.login(username=admin.username, password="AdminPassword!908")

        self.client.post(
            "/matsu/",
            {"password": "AdminPassword!908", "action": "confirm"},
        )
        response = self.client.get("/matsu/")
        self.assertContains(response, f'href="/matsu/{participant.pk}/edit/"')
        self.assertContains(response, "Telegram Username")
        self.assertNotContains(response, "Email")
        self.assertNotContains(response, "Telefon")

        edit_response = self.client.get(f"/matsu/{participant.pk}/edit/")
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, 'value="@wrong_username"')

        save_response = self.client.post(
            f"/matsu/{participant.pk}/edit/",
            {
                "Roblox_username": "CorrectedName",
                "telegram_username": "@correct_username",
            },
        )
        self.assertRedirects(save_response, "/matsu/")
        participant.refresh_from_db()
        self.assertEqual(participant.Roblox_username, "CorrectedName")
        self.assertEqual(participant.telegram_username, "@correct_username")

    def test_participant_edit_requires_admin_confirmation(self):
        participant = RobloxUser.objects.create(
            Roblox_username="PrivateParticipant",
            telegram_username="@private_user",
        )
        admin = get_user_model().objects.create_superuser(
            username="unconfirmedadmin",
            email="unconfirmed@example.com",
            password="AdminPassword!908",
        )
        self.client.login(username=admin.username, password="AdminPassword!908")

        response = self.client.get(f"/matsu/{participant.pk}/edit/")

        self.assertRedirects(response, "/matsu/")

    def test_matsu_is_public_shows_count_and_registration_time(self):
        participant = RobloxUser.objects.create(
            Roblox_username="VisibleRobloxName",
            telegram_username="@visible_user",
        )

        response = self.client.get("/matsu/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jami 1 ta")
        self.assertContains(response, "VisibleRobloxName")
        self.assertContains(
            response,
            participant.registered_at.strftime("%d.%m.%Y %H:%M"),
        )
        self.assertContains(response, "@visible_user")
        self.assertNotContains(response, "participant-edit-button")
        self.assertNotContains(response, "Admin akkaunti paroli")

    def test_matsu_admin_actions_and_json_export_still_require_confirmation(self):
        RobloxUser.objects.create(
            Roblox_username="VisibleRobloxName",
            telegram_username="@visible_user",
        )
        admin = get_user_model().objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="AdminPassword!908",
        )
        self.client.force_login(admin)

        export_response = self.client.post("/matsu/", {"action": "export"})
        self.assertRedirects(export_response, "/matsu/")

        wrong_password_response = self.client.post(
            "/matsu/",
            {"password": "wrong-password", "action": "confirm"},
        )
        self.assertIn(
            "Parol noto'g'ri.",
            wrong_password_response.context["form"].errors["password"],
        )
        self.assertContains(wrong_password_response, "@visible_user")

        response = self.client.post(
            "/matsu/",
            {"password": "AdminPassword!908", "action": "confirm"},
        )
        self.assertContains(response, "VisibleRobloxName")
        self.assertContains(response, "@visible_user")

    def test_json_export_contains_usernames_and_registration_time(self):
        RobloxUser.objects.create(
            Roblox_username="JsonPlayer",
            telegram_username="@json_player",
        )
        admin = get_user_model().objects.create_superuser(
            username="jsonadmin",
            email="jsonadmin@example.com",
            password="AdminPassword!908",
        )
        self.client.force_login(admin)

        self.client.post(
            "/matsu/",
            {"password": "AdminPassword!908", "action": "confirm"},
        )
        response = self.client.post("/matsu/", {"action": "export"})

        self.assertEqual(response.status_code, 200)
        exported = response.json()[0]
        self.assertEqual(exported["roblox_username"], "JsonPlayer")
        self.assertEqual(exported["telegram_username"], "@json_player")
        self.assertEqual(
            exported["registered_at"],
            RobloxUser.objects.get().registered_at.isoformat(),
        )
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn("no-store", response["Cache-Control"])
