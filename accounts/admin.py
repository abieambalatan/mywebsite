from django.contrib import admin

from .models import Evaluation, Faculty, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department")
    search_fields = ("user__username", "department")
    list_filter = ("department",)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "subject")
    search_fields = ("name", "department", "subject")
    list_filter = ("department",)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("faculty", "student_name", "average_rating", "created_at")
    list_filter = ("faculty__department", "faculty", "created_at")
    search_fields = ("faculty__name", "student_name", "comment")
    readonly_fields = ("created_at",)
