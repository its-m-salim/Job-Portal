from django.db import models
from django.contrib.auth.models import User






class EmailConfirm(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE)
    full_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    about = models.TextField(blank=True)
    skills = models.TextField()
    experience = models.PositiveBigIntegerField(default=0)
    resume = models.FileField(upload_to='resumes/', blank=True)


class Company(models.Model):
    name = models.CharField(max_length=100)
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.TextField()
    city = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)



class Vacancy(models.Model):

    EMPLOYMENT_TYPE = [
        ("full", "Полная занятость"),
        ("part", "Частичная"),
        ("remote", "Удалённо"),
        ("intern", "Стажировка")
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    company = models.ForeignKey(Company, on_delete = models.CASCADE, related_name='vacancies')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    salary_from = models.PositiveIntegerField(null=True, blank=True)
    salary_to = models.PositiveIntegerField(null=True, blank=True)
    city = models.CharField(max_length=100)
    employment = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE)
    experience_required = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        permissions = [
            ("close_vacancy", "может закрыт вакансию")
        ]



class Applications(models.Model):
    STATUSES = [
        ("pending", "На рассмотрении"),
        ("accepted", "Принят"),
        ("rejected", "Отклонён")
    ]

    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    letter = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('vacancy', 'candidate')
        permissions = [
            ("can_change_status", "может ищменить статус отклика")
        ]
