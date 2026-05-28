from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import DEPARTMENT_CHOICES, Evaluation, Faculty, StudentProfile


RATING_CHOICES = [(score, str(score)) for score in range(1, 6)]


class StudentRegistrationForm(forms.Form):
    username = forms.CharField(
        label="Student ID Number",
        max_length=30,
        widget=forms.TextInput(attrs={"placeholder": "Enter your student ID number"}),
    )
    department = forms.ChoiceField(label="Department", choices=DEPARTMENT_CHOICES)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username.isdigit():
            raise forms.ValidationError("Student ID number must contain numbers only.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This student ID number is already registered.")
        return username

    def save(self, commit=True):
        user = User(username=self.cleaned_data["username"])
        user.set_unusable_password()
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            StudentProfile.objects.create(user=user, department=self.cleaned_data["department"])
        return user


class StudentLoginForm(forms.Form):
    username = forms.CharField(
        label="Student ID Number",
        widget=forms.TextInput(attrs={"placeholder": "Enter your student ID number"}),
    )
    department = forms.ChoiceField(label="Department", choices=DEPARTMENT_CHOICES)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username.isdigit():
            raise forms.ValidationError("Student ID number must contain numbers only.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        department = cleaned_data.get("department")
        if not username or not department:
            return cleaned_data

        try:
            user = User.objects.select_related("student_profile").get(username=username, is_staff=False)
        except (User.DoesNotExist, StudentProfile.DoesNotExist):
            raise forms.ValidationError("Student ID is not registered.")

        profile = getattr(user, "student_profile", None)
        if profile is None:
            raise forms.ValidationError("Student ID is not registered.")

        if profile.department != department:
            raise forms.ValidationError("Student ID and department do not match.")

        cleaned_data["user"] = user
        return cleaned_data


class AdminRegistrationForm(forms.Form):
    username = forms.CharField(
        label="Admin Username",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Enter admin username"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already registered.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data["username"],
            is_staff=True,
            is_superuser=False,
        )
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        label="Admin Username",
        widget=forms.TextInput(attrs={"placeholder": "Enter admin username"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if not username or not password:
            return cleaned_data

        user = authenticate(username=username, password=password)
        if user is None or not user.is_staff:
            raise forms.ValidationError("Invalid admin username or password.")

        cleaned_data["user"] = user
        return cleaned_data


class FacultyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["faculty_id"].required = True

    class Meta:
        model = Faculty
        fields = ["faculty_id", "name", "department", "subject"]
        widgets = {
            "faculty_id": forms.TextInput(attrs={"placeholder": "Faculty ID number"}),
            "name": forms.TextInput(attrs={"placeholder": "Teacher name"}),
            "department": forms.Select(choices=DEPARTMENT_CHOICES),
            "subject": forms.TextInput(attrs={"placeholder": "Subject handled"}),
        }


class FacultyLoginForm(forms.Form):
    faculty_id = forms.CharField(
        label="Faculty ID Number",
        max_length=30,
        widget=forms.TextInput(attrs={"placeholder": "Enter your faculty ID number"}),
    )

    def clean_faculty_id(self):
        faculty_id = self.cleaned_data["faculty_id"].strip()
        try:
            faculty = Faculty.objects.get(faculty_id__iexact=faculty_id)
        except Faculty.DoesNotExist:
            if faculty_id.isdigit():
                try:
                    faculty = Faculty.objects.get(pk=int(faculty_id), faculty_id__isnull=True)
                except Faculty.DoesNotExist:
                    raise forms.ValidationError("Faculty ID is not registered.")
            else:
                raise forms.ValidationError("Faculty ID is not registered.")

        self.cleaned_data["faculty"] = faculty
        return faculty_id


class EvaluationForm(forms.ModelForm):
    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department:
            self.fields["faculty"].queryset = Faculty.objects.filter(department__iexact=department)

    class Meta:
        model = Evaluation
        fields = [
            "faculty",
            "student_name",
            "subject_knowledge",
            "teaching",
            "communication",
            "punctuality",
            "fairness",
            "comment",
        ]
        widgets = {
            "faculty": forms.Select(),
            "student_name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "subject_knowledge": forms.RadioSelect(choices=RATING_CHOICES),
            "teaching": forms.RadioSelect(choices=RATING_CHOICES),
            "communication": forms.RadioSelect(choices=RATING_CHOICES),
            "punctuality": forms.RadioSelect(choices=RATING_CHOICES),
            "fairness": forms.RadioSelect(choices=RATING_CHOICES),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Optional comment"}),
        }
