from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


DEPARTMENT_CHOICES = [
    ("IT", "IT"),
    ("CS", "CS"),
    ("EDUCATION", "Education"),
    ("BUSINESS", "Business"),
    ("HOSPITALITY", "Hospitality"),
]


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.department}"


class Faculty(models.Model):
    faculty_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)
    subject = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Faculty"

    def __str__(self):
        return self.name


class Evaluation(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="evaluations")
    student_name = models.CharField(max_length=100)
    subject_knowledge = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    teaching = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    punctuality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    fairness = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.faculty.name} - {self.student_name}"

    def average_rating(self):
        scores = [
            self.subject_knowledge,
            self.teaching,
            self.communication,
            self.punctuality,
            self.fairness,
        ]
        return sum(scores) / len(scores)
