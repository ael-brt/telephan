from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from .forms import SignUpForm


class TelephanLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and request.user.is_authenticated:
            return redirect(self.get_success_url())
        next_path = request.GET.get(self.redirect_field_name, "/")
        if not isinstance(next_path, str) or not next_path.startswith("/") or next_path.startswith("//"):
            next_path = "/"
        login_url = settings.FRONTEND_LOGIN_URL
        if "next=" in login_url:
            prefix, _ = login_url.split("next=", 1)
            return redirect(f"{prefix}next={quote(next_path, safe='')}")
        sep = "&" if "?" in login_url else "?"
        return redirect(f"{login_url}{sep}next={quote(next_path, safe='')}")

    def form_valid(self, form):
        response = super().form_valid(form)
        remember_me = self.request.POST.get("remember_me")
        if remember_me in {"1", "true", "on", "yes"}:
            self.request.session.set_expiry(60 * 60 * 24 * 30)  # 30 jours
        else:
            self.request.session.set_expiry(0)  # expire à la fermeture du navigateur
        return response


@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"ok": True})

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connexion auto après inscription
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})
