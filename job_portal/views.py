from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth.models import Group, User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count, Prefetch
from django.core.mail import send_mail
import random




def home_page(request):
    return render(request, 'home.html')




def send_code(user):
    code = str(random.randint(100000, 999999))

    EmailConfirm.objects.update_or_create(
        user = user,
        defaults = {"code": code}
    )


    send_mail(
        "Код подтверждения",
        f"Ваш код подтверждения: {code}",
        None,
        [user.email]
    )



def registration(request):
    if request.method == "POST":
        data = request.POST

        if  User.objects.filter(username = data['username']).exists():
            return render(request, "registration.html", {"error": "Такой логин уже занят"})

        if User.objects.filter(email=data['email']).exists():
            return render(request, "registration.html", {"error": "Эта почта уже используется"})
        

        user = User.objects.create_user(
            username = data['username'],
            password = data['password'],
            email = data['email'],
            is_active = False
        )

        send_code(user)

        return redirect("verify_email", id = user.id)

    return render(request, "registration.html")



def verify_email(request, id):

    user = get_object_or_404(User, pk = id, is_active = False)

    if request.method == "POST":
        code = request.POST['code']

        record = EmailConfirm.objects.filter(user = user, code = code).first()

        if record is None:
            return render(request, "verify_email.html", {"user_id": user.id, "error": "Неверный код"})

        user.is_active = True
        user.save()
        record.delete()


        login(request, user)
        return redirect("choose_role")

    return render(request, "verify_email.html", {"user_id": user.id})



def login_user(request):
    if request.method == "POST":
        data = request.POST
        username = data["username"]
        password = data["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if is_employer(user):
                if not Company.objects.filter(owner=user).exists():
                    return redirect("create_company")
            
            elif is_condidate(user):
                if not CandidateProfile.objects.filter(user=user).exists():
                    return redirect("candidate_form")
            
            else:
                return redirect("choose_role")

            return redirect("home")

        inactive = User.objects.filter(username=username, is_active=False).first()

        if inactive is not None and inactive.check_password(password):
            send_code(inactive)
            return redirect("verify_email", id=inactive.id)

        return render(request, "login.html", {"error": "Неверный логин или пароль"})

    return render(request, "login.html")


def resend_code(request, id):
    user = get_object_or_404(User, pk = id, is_active = False)

    if request.method == "POST":
        send_code(user)

    return redirect("verify_email", id=user.id)




@login_required
def logout_user(request):
    logout(request)
    return redirect("login")



def is_employer(user):
    return bool(user.groups.filter(name = 'Employers').exists())


def is_condidate(user):
    return bool(user.groups.filter(name = "Candidates").exists())


@login_required
def choose_role(request):
    if request.method == 'POST':
        role = request.POST.get('role', "")

        if not role.strip():
            return render(request, 'choose_role.html', {"error": "Выбкрите роль пожалуйста"})

        user = request.user

        if role == "employer":
            employer_group = Group.objects.get(name = 'Employers')
            user.groups.add(employer_group)
            return redirect('create_company')
        
        elif role == 'candidate':
            condidates_group = Group.objects.get(name = 'Candidates')
            user.groups.add(condidates_group)
            return redirect('candidate_form')
        else:
            return render(request, 'choose_role.html', {"error": "выбран не существуюущий роль"})

    return render(request, 'choose_role.html')






@login_required
@permission_required("job_portal.add_candidateprofile", raise_exception=True)
def create_candidate_profile(request):

    if CandidateProfile.objects.filter(user = request.user).exists():
        return redirect("home")


    if request.method == 'POST':

        data = request.POST

        experience = data.get('experience')

        if experience:
            if experience.isdigit():
                experience = int(data['experience'])
            else:
                return render(request, 'candidate_form.html', {"error": "Вводите корректное число или оставьте пустым"})
        else:
            experience = 0
       
        CandidateProfile.objects.create(
            user = request.user,
            full_name = data['full_name'],
            city = data['city'],
            about = data['about'],
            skills = data['skills'],
            experience = experience,
            resume = request.FILES.get('resume')
        )
        return redirect('home')

    return render(request, 'candidate_form.html')



@login_required
@permission_required('job_portal.add_company', raise_exception=True)
def create_company(request):

    if Company.objects.filter(owner = request.user).exists():
        return redirect('home')

    if request.method == 'POST':
        data = request.POST

        

        name = data['name'].strip()
        description = data['description'].strip()
        city = data['city'].strip()

        logo = request.FILES['logo'] if request.FILES.get('logo') else None

        Company.objects.create(
            name = name,
            description = description,
            owner = request.user,
            city = city,
            logo = logo
        )
        return redirect('home')

    return render(request, 'create_company.html')





# @login_required
# @permission_required('job_portal.add_vacancy', raise_exception=True)
# def create_vacancy(request):
