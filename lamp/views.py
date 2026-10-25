from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import MatsuPasswordForm, RobloxUserRegistrationForm
from .models import RobloxUser

MATSU_CONFIRMATION_SESSION_KEY = "matsu_admin_confirmation"


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("login")

    return render(request, "registration/signup.html", {"form": form})


@login_required
def home(request):
    registrations = RobloxUser.objects.filter(user=request.user).order_by("id")
    registration = None
    editing = False
    adding = request.GET.get("add") == "1"
    edit_id = request.GET.get("edit")

    if edit_id:
        editing = True
        registration = get_object_or_404(registrations, pk=edit_id)

    if request.method == "POST":
        registration_id = request.POST.get("registration_id")
        if registration_id:
            registration = get_object_or_404(registrations, pk=registration_id)
        else:
            registration = None
        form = RobloxUserRegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            saved_registration = form.save(commit=False)
            if registration is None:
                saved_registration.user = request.user
            saved_registration.save()
            message = (
                "Ma'lumotlaringiz yangilandi."
                if registration is not None
                else "Roblox akkauntingiz qo'shildi!"
            )
            messages.success(request, message)
            return redirect("home")
    else:
        form = RobloxUserRegistrationForm(instance=registration)

    show_form = adding or editing or not registrations.exists() or bool(form.errors)
    return render(
        request,
        "home.html",
        {
            "adding": adding,
            "editing": editing,
            "form": form,
            "registrations": registrations,
            "registration": registration,
            "show_form": show_form,
        },
    )


@login_required
def matsu(request):
    if not request.user.is_staff:
        return redirect(f"{reverse('admin:login')}?next={request.path}")

    confirmation = request.session.get(MATSU_CONFIRMATION_SESSION_KEY)
    confirmed = confirmation == [
        request.user.pk,
        request.user.get_session_auth_hash(),
    ]
    if not confirmed:
        request.session.pop(MATSU_CONFIRMATION_SESSION_KEY, None)

    form = MatsuPasswordForm()
    if request.method == "POST" and request.POST.get("action") != "export":
        form = MatsuPasswordForm(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data["password"]):
                request.session[MATSU_CONFIRMATION_SESSION_KEY] = [
                    request.user.pk,
                    request.user.get_session_auth_hash(),
                ]
                request.session.set_expiry(900)
                confirmed = True
            else:
                form.add_error("password", "Parol noto'g'ri.")

    participants = RobloxUser.objects.order_by("Roblox_username") if confirmed else ()

    if (
        request.method == "POST"
        and request.POST.get("action") == "export"
        and confirmed
    ):
        include_phone = request.POST.get("include_phone") == "on"
        data = []
        for participant in participants:
            row = {
                "roblox_username": participant.Roblox_username,
                "email": participant.roblox_email,
            }
            if include_phone:
                row["phone_number"] = participant.phone_number
            data.append(row)

        response = JsonResponse(
            data,
            safe=False,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )
        response["Content-Disposition"] = (
            'attachment; filename="tournament-registrations.json"'
        )
        response["Cache-Control"] = "private, no-store"
        return response

    return render(
        request,
        "matsu.html",
        {
            "confirmed": confirmed,
            "form": form,
            "participants": participants,
        },
    )


@login_required
def edit_participant(request, pk):
    if not request.user.is_staff:
        return redirect(f"{reverse('admin:login')}?next={request.path}")

    confirmation = request.session.get(MATSU_CONFIRMATION_SESSION_KEY)
    if confirmation != [
        request.user.pk,
        request.user.get_session_auth_hash(),
    ]:
        request.session.pop(MATSU_CONFIRMATION_SESSION_KEY, None)
        messages.info(request, "Tahrirlashdan oldin admin parolini tasdiqlang.")
        return redirect("matsu")

    participant = get_object_or_404(RobloxUser, pk=pk)
    if request.method == "POST":
        form = RobloxUserRegistrationForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            messages.success(request, "Ishtirokchi ma'lumotlari yangilandi.")
            return redirect("matsu")
    else:
        form = RobloxUserRegistrationForm(instance=participant)

    return render(
        request,
        "edit_participant.html",
        {"form": form, "participant": participant},
    )
