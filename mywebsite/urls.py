from django.urls import include, path

from accounts import views

urlpatterns = [
    path("admin/", views.admin_login_view, name="old_admin_login"),
    path("", views.home_view, name="home"),
    path("", include("accounts.urls")),
]
