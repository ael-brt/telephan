from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import TelephanLoginView, csrf, signup

urlpatterns = [
    path('csrf/', csrf, name='csrf'),
    path('login/', TelephanLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
]
