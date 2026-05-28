from django.urls import path

from . import views

urlpatterns = [
    path("faculty-login/", views.faculty_login_view, name="faculty_login"),
    path("faculty-dashboard/", views.faculty_dashboard_view, name="faculty_dashboard"),
    path("faculty-logout/", views.faculty_logout_view, name="faculty_logout"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("admin-login/", views.admin_login_view, name="admin_login"),
    path("admin-register/", views.admin_register_view, name="admin_register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("faculty/", views.faculty_list, name="faculty_list"),
    path("faculty/add/", views.add_faculty, name="add_faculty"),
    path("faculty/<int:pk>/edit/", views.edit_faculty, name="edit_faculty"),
    path("faculty/<int:pk>/delete/", views.delete_faculty, name="delete_faculty"),
    path("evaluation/", views.evaluation_view, name="evaluation"),
    path("portal/", views.portal_view, name="portal"),
    path("results/", views.results_view, name="results"),
    path("logout/", views.logout_view, name="logout"),
]
