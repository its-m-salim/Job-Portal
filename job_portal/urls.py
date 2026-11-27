from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home'),

    path('registration/', views.registration, name='registration'),
    path('verify/<int:id>/', views.verify_email, name='verify_email'),
    path('verify/<int:id>/resend/', views.resend_code, name='resend_code'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('role/', views.choose_role, name='choose_role'),

    path('profile/create/', views.create_candidate_profile, name='candidate_form'),
    path('profile/edit/', views.edit_candidate_profile, name='edit_candidate_profile'),
    path('applications/my/', views.my_applications, name='my_applications'),

    path('company/create/', views.create_company, name='create_company'),
    path('company/edit/', views.edit_company, name='edit_company'),

    path('vacancies/my/', views.my_vacancies, name='my_vacancies'),
    path('vacancies/create/', views.create_vacancy, name='create_vacancy'),
    path('vacancies/<int:id>/', views.vacancy_info, name='vacancy_info'),
    path('vacancies/<int:id>/edit/', views.edit_vacancy, name='edit_vacancy'),
    path('vacancies/<int:id>/close/', views.close_vacancy, name='close_vacancy'),
    path('vacancies/<int:id>/apply/', views.apply_vacancy, name='apply_vacancy'),
    path('vacancies/<int:id>/applications/', views.vacancy_applications, name='vacancy_applications'),
    path('applications/<int:id>/edit/', views.edit_application, name='edit_application'),
]