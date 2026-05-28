from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AdminLoginForm,
    AdminRegistrationForm,
    EvaluationForm,
    FacultyLoginForm,
    FacultyForm,
    StudentLoginForm,
    StudentRegistrationForm,
)
from .models import DEPARTMENT_CHOICES, Evaluation, Faculty, StudentProfile


def get_achievement_badge(overall_average, evaluation_count):
    if overall_average is None or evaluation_count == 0:
        return None
    if overall_average >= 4.75:
        return {
            "title": "Gold Badge",
            "class": "gold",
            "description": "Outstanding evaluation score",
        }
    if overall_average >= 4.50:
        return {
            "title": "Silver Badge",
            "class": "silver",
            "description": "Excellent evaluation score",
        }
    if overall_average >= 4.25:
        return {
            "title": "Bronze Badge",
            "class": "bronze",
            "description": "Very good evaluation score",
        }
    return None


def add_faculty_rating_summary(faculty):
    averages = [
        faculty.avg_subject_knowledge,
        faculty.avg_teaching,
        faculty.avg_communication,
        faculty.avg_punctuality,
        faculty.avg_fairness,
    ]
    valid_averages = [score for score in averages if score is not None]
    faculty.overall_average = sum(valid_averages) / len(valid_averages) if valid_averages else None
    faculty.achievement_badge = get_achievement_badge(faculty.overall_average, faculty.evaluation_count)
    return faculty


def staff_required(view_func):
    return user_passes_test(lambda user: user.is_staff, login_url="evaluation")(view_func)


def get_department_navigation(request):
    selected_department = request.GET.get("department")
    valid_departments = [value for value, _ in DEPARTMENT_CHOICES]
    if selected_department not in valid_departments and selected_department != "all":
        selected_department = valid_departments[0]

    return {
        "departments": DEPARTMENT_CHOICES,
        "selected_department": selected_department,
        "show_all_departments": selected_department == "all",
    }


def home_view(request):
    return render(request, "home.html")


def register_view(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please login using your student ID and department.")
            return redirect("login")
    else:
        form = StudentRegistrationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("evaluation")
        return render(request, "login.html", {"form": form, "error": "Invalid student ID number or department"})

    form = StudentLoginForm()
    return render(request, "login.html", {"form": form})


def admin_register_view(request):
    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Admin registration successful. Please login.")
            return redirect("admin_login")
    else:
        form = AdminRegistrationForm()

    return render(request, "admin_register.html", {"form": form})


def admin_login_view(request):
    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("dashboard")
        return render(request, "admin_login.html", {"form": form, "error": "Invalid admin username or password"})

    form = AdminLoginForm()
    return render(request, "admin_login.html", {"form": form})


@login_required
@staff_required
def dashboard_view(request):
    department_navigation = get_department_navigation(request)
    selected_department = department_navigation["selected_department"]
    department_choices = DEPARTMENT_CHOICES
    if selected_department != "all":
        department_choices = [choice for choice in DEPARTMENT_CHOICES if choice[0] == selected_department]

    department_summaries = []
    for department_value, department_label in department_choices:
        department_summaries.append(
            {
                "value": department_value,
                "label": department_label,
                "faculty_count": Faculty.objects.filter(department=department_value).count(),
                "student_count": StudentProfile.objects.filter(department=department_value).count(),
                "evaluation_count": Evaluation.objects.filter(faculty__department=department_value).count(),
                "latest_evaluations": Evaluation.objects.select_related("faculty")
                .filter(faculty__department=department_value)[:5],
            }
        )

    if selected_department == "all":
        faculty_count = Faculty.objects.count()
        student_count = User.objects.filter(is_staff=False).count()
        evaluation_count = Evaluation.objects.count()
    else:
        faculty_count = Faculty.objects.filter(department=selected_department).count()
        student_count = StudentProfile.objects.filter(department=selected_department).count()
        evaluation_count = Evaluation.objects.filter(faculty__department=selected_department).count()

    context = {
        "faculty_count": faculty_count,
        "student_count": student_count,
        "evaluation_count": evaluation_count,
        "department_summaries": department_summaries,
        **department_navigation,
    }
    return render(request, "dashboard.html", context)


@login_required
@staff_required
def faculty_list(request):
    department_navigation = get_department_navigation(request)
    selected_department = department_navigation["selected_department"]
    faculty = Faculty.objects.all()
    if selected_department != "all":
        faculty = faculty.filter(department=selected_department)

    return render(
        request,
        "accounts/faculty_list.html",
        {"faculty": faculty, **department_navigation},
    )


@login_required
@staff_required
def add_faculty(request):
    form = FacultyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Faculty added successfully.")
        return redirect("faculty_list")

    return render(request, "accounts/faculty_form.html", {"form": form, "title": "Add Faculty"})


@login_required
@staff_required
def edit_faculty(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    form = FacultyForm(request.POST or None, instance=faculty)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Faculty updated successfully.")
        return redirect("faculty_list")

    return render(request, "accounts/faculty_form.html", {"form": form, "title": "Edit Faculty"})


@login_required
@staff_required
def delete_faculty(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == "POST":
        faculty.delete()
        messages.success(request, "Faculty deleted successfully.")
        return redirect("faculty_list")

    return render(request, "accounts/confirm_delete.html", {"faculty": faculty})


@login_required
def evaluation_view(request):
    initial = {}
    student_department = None
    departments = DEPARTMENT_CHOICES

    if request.user.is_authenticated and not request.user.is_staff:
        initial["student_name"] = request.user.username
        profile, _ = StudentProfile.objects.get_or_create(
            user=request.user,
            defaults={"department": DEPARTMENT_CHOICES[0][0]},
        )
        student_department = profile.department
        departments = [choice for choice in DEPARTMENT_CHOICES if choice[0] == student_department]

    selected_department = request.GET.get("department") if request.user.is_staff else student_department
    if request.user.is_staff and not selected_department and departments:
        selected_department = departments[0][0]

    form = EvaluationForm(request.POST or None, initial=initial, department=selected_department)
    if not request.user.is_staff:
        form.fields["student_name"].label = "Student ID Number"
        form.fields["student_name"].disabled = True

    if request.method == "POST" and form.is_valid():
        evaluation = form.save(commit=False)
        if not request.user.is_staff:
            evaluation.student_name = request.user.username
        evaluation.save()
        messages.success(request, "Evaluation submitted successfully.")
        return redirect("evaluation")

    return render(
        request,
        "evaluation.html",
        {
            "form": form,
            "departments": departments,
            "selected_department": selected_department,
        },
    )


def portal_view(request):
    return redirect("faculty_dashboard")


def faculty_login_view(request):
    if request.method == "POST":
        form = FacultyLoginForm(request.POST)
        if form.is_valid():
            request.session["faculty_portal_id"] = form.cleaned_data["faculty"].pk
            return redirect("faculty_dashboard")
    else:
        form = FacultyLoginForm()

    return render(request, "faculty_login.html", {"form": form})


def faculty_dashboard_view(request):
    faculty_pk = request.session.get("faculty_portal_id")
    if not faculty_pk:
        return redirect("faculty_login")

    faculty = get_object_or_404(
        Faculty.objects
        .annotate(
            evaluation_count=Count("evaluations"),
            avg_subject_knowledge=Avg("evaluations__subject_knowledge"),
            avg_teaching=Avg("evaluations__teaching"),
            avg_communication=Avg("evaluations__communication"),
            avg_punctuality=Avg("evaluations__punctuality"),
            avg_fairness=Avg("evaluations__fairness"),
        ),
        pk=faculty_pk,
    )
    add_faculty_rating_summary(faculty)
    evaluations = faculty.evaluations.all()[:20]

    return render(
        request,
        "faculty_dashboard.html",
        {
            "faculty": faculty,
            "evaluations": evaluations[:10],
        },
    )


def faculty_logout_view(request):
    request.session.pop("faculty_portal_id", None)
    return redirect("faculty_login")


@login_required
@staff_required
def results_view(request):
    department_navigation = get_department_navigation(request)
    selected_department = department_navigation["selected_department"]
    faculty_queryset = Faculty.objects.all()
    evaluations = Evaluation.objects.select_related("faculty")
    if selected_department != "all":
        faculty_queryset = faculty_queryset.filter(department=selected_department)
        evaluations = evaluations.filter(faculty__department=selected_department)

    faculty_results = list(faculty_queryset.annotate(
        evaluation_count=Count("evaluations"),
        avg_subject_knowledge=Avg("evaluations__subject_knowledge"),
        avg_teaching=Avg("evaluations__teaching"),
        avg_communication=Avg("evaluations__communication"),
        avg_punctuality=Avg("evaluations__punctuality"),
        avg_fairness=Avg("evaluations__fairness"),
    ))
    for faculty in faculty_results:
        add_faculty_rating_summary(faculty)

    evaluations = evaluations[:20]
    return render(
        request,
        "results.html",
        {"faculty_results": faculty_results, "evaluations": evaluations, **department_navigation},
    )


def logout_view(request):
    was_staff = request.user.is_authenticated and request.user.is_staff
    logout(request)
    if was_staff:
        return redirect("admin_login")
    return redirect("login")
