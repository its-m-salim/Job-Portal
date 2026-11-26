from django.urls import path
from .views import *

urlpatterns = [
    path('', home_page, name='home'),
    path("registration/", registration, name = "registration"),
    path("verify/<int:id>/", verify_email, name = "verify_email"),
    path("resend/<int:id>/", resend_code, name = "resend_code"),
    path("login/", login_user, name = "login"),
    path("logout/", logout_user, name = "logout"),
    path("choose-role/", choose_role, name="choose_role"),
    path("candidate/create/", create_candidate_profile, name="candidate_form"),
    path("company/create/", create_company, name="create_company"),
]
