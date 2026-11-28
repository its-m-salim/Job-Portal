from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth.models import Group, User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count, Prefetch
from django.core.mail import send_mail
import random




def home_page(request):

    vacancies = Vacancy.objects.filter(is_active = True).select_related('company', 'category')

    q = request.GET.get('q')

    if q:
        vacancies = vacancies.filter(
            Q(title__icontains = q) | Q(description__icontains = q) | Q(company__name__icontains = q)
        
        )

    city = request.GET.get('city')
    
    if city:
        vacancies = vacancies.filter(city__icontains = city)

    category = request.GET.get('category')

    if category and category.isdecimal():
        vacancies = vacancies.filter(category_id = int(category))

    employment = request.GET.get('employment')

    if employment in dict(Vacancy.EMPLOYMENT_TYPE):
        vacancies = vacancies.filter(employment = employment)
    
    salary = request.GET.get('salary')

    if salary and salary.isdigit():
        vacancies = vacancies.filter(salary_to__gte = int(salary))

    experience = request.GET.get('experience')

    if experience and experience.isdigit():
        vacancies = vacancies.filter(experience_required__lte = int(experience))

    sort = request.GET.get('sort', "new")

    if sort == 'old':
    
        vacancies = vacancies.order_by('created_at')
    
    elif sort == 'salary':
        vacancies = vacancies.order_by('-salary_to')
    else:
        vacancies = vacancies.order_by('-created_at')

    favorite_ids = None

    if request.user.is_authenticated and is_condidate(request.user):
        favorite_ids = set(
            Favorite.objects.filter(user = request.user).values_list('vacancy_id', flat=True)
        )

    context = {
        "vacancies": vacancies,
        "data": request.GET,
        "categories": Category.objects.filter(is_active = True),
        "employment_types": Vacancy.EMPLOYMENT_TYPE
    }

    return render(request, 'home.html', context)









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

        if is_condidate(request.user) or is_employer(request.user):
            return redirect('home')

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

        if request.FILES.get('resume'):
            resume = request.FILES['resume']
        else:
            resume = None


        CandidateProfile.objects.create(
            user = request.user,
            full_name = data['full_name'],
            city = data['city'],
            about = data['about'],
            skills = data['skills'],
            experience = experience,
            resume = resume
        )
        return redirect('home')

    return render(request, 'candidate_form.html')



@login_required
@permission_required('job_portal.add_company', raise_exception=True)
def create_company(request):

    if Company.objects.filter(owner = request.user).exists():
        return redirect('home')

    if not is_employer(request.user):
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




@login_required
@permission_required('job_portal.add_vacancy', raise_exception=True)
def create_vacancy(request):

    company = Company.objects.filter(owner = request.user).first()

    if company is None:
        return redirect('create_company')
    categories = Category.objects.filter(is_active = True)

    if request.method == "POST":
        data = request.POST

        context = {
            "categories": categories,
            "employment_types": Vacancy.EMPLOYMENT_TYPE,
            "data": data
        }

        
        title = data.get('title', "").strip()
        description = data.get('description', "").strip()
        city = data.get('city', "").strip()

        if not title or not description or not city:
            context["error"] = "Заполните название, описание и город"
            return render(request, 'create_vacancy.html', context)

       

        category_id = data.get('category', "").strip()
        category = None

        if category_id and category_id.isdigit():
            category = categories.filter(pk = category_id).first()

        if category is None:
            context["error"] = "Выберите категорию"
            return render(request, 'create_vacancy.html', context)


        employment = data.get('employment', "").strip()
        if employment not in dict(Vacancy.EMPLOYMENT_TYPE):
            context["error"] = "Выберите тип занятости"
            return render(request, 'create_vacancy.html', context)


        salary_from = data.get('salary_from', "").strip()

        if salary_from:
            if salary_from.isdigit():
                salary_from = int(salary_from)
            else:
                context["error"] = "Зарплата «от» должна быть числом"
                return render(request, 'create_vacancy.html', context)
        else:
            salary_from = None

        salary_to = data.get('salary_to', "").strip()

        if salary_to:
            if salary_to.isdigit():
                salary_to = int(salary_to)
            else:
                context["error"] = "Зарплата «до» должна быть числом"
                return render(request, 'create_vacancy.html', context)
        else:
            salary_to = None

        if salary_from is not None and salary_to is not None and salary_from > salary_to:
            context["error"] = "Зарплата «от» не может быть больше «до»"
            return render(request, 'create_vacancy.html', context)

        experience = data.get('experience', "").strip()

        if experience:
            if experience.isdigit():
                experience = int(experience)
            else:
                context["error"] = "Опыт должен быть числом или пустым"
                return render(request, 'create_vacancy.html', context)
        else:
            experience = 0

        Vacancy.objects.create(
            title = title,
            description = description,
            company = company,
            category = category,
            salary_from = salary_from,
            salary_to = salary_to,
            city = city,
            employment = employment,
            experience_required = experience
        )

        return redirect("my_vacancies")

    return render(request, 'create_vacancy.html', {"categories": categories, "employment_types": Vacancy.EMPLOYMENT_TYPE})







@login_required
@permission_required('job_portal.view_vacancy', raise_exception=True)
def my_vacancies(request):

 
    company = Company.objects.filter(owner = request.user).first()
    if company is None:
        return redirect('create_company')

    vacancies = Vacancy.objects.filter(company = company).annotate(
        total_apps = Count('applications'),
        pending = Count('applications', filter= Q(applications__status = 'pending'))
    ).order_by('-created_at')

    return render(request, 'my_vacancies.html', {'vacancies': vacancies, "company" : company})



@login_required
def vacancy_info(request, id):

    vacancy = get_object_or_404(Vacancy.objects.select_related('category', 'company'), pk =id)

    is_owner = vacancy.company.owner == request.user

    if not vacancy.is_active and not is_owner:
        return redirect('home')

    first_apply = False
    if is_condidate(request.user):
        first_apply = Applications.objects.filter(vacancy = vacancy,candidate = request.user).exists()

    can_apply = is_condidate(request.user) and vacancy.is_active and not first_apply
    is_favorite = False
    if is_condidate(request.user):
        is_favorite = Favorite.objects.filter(user = request.user, vacancy = vacancy).exists()

    context = {
        "vacancy": vacancy,
        "is_owner": is_owner,
        "already_applied": first_apply,
        "can_apply": can_apply,
        "applications_count": vacancy.applications.count() if is_owner else None,
        "is_favorite": is_favorite,
    }

    return render(request, 'vacancy_info.html', context)



@login_required
@permission_required('job_portal.close_vacancy', raise_exception=True)
def close_vacancy(request, id):

    vacancy = get_object_or_404(Vacancy.objects.select_related('company'), pk = id)

    if vacancy.company.owner != request.user:
        return redirect('home')

    if request.method == 'POST':
        vacancy.is_active = False
        vacancy.save()

    return redirect('my_vacancies')





@login_required
@permission_required('job_portal.add_applications', raise_exception=True)
def apply_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, pk = id)

    if not CandidateProfile.objects.filter(user = request.user).exists():
        return redirect('candidate_form')

    if Applications.objects.filter(candidate = request.user, vacancy = vacancy).exists():
        return render(request, 'apply_vacancy.html', {'vacancy': vacancy, 'error': "Вы уже откликались на эту вакансию"})

    if request.method == 'POST':
        letter = request.POST.get('letter', "")
        if not letter:
            return render(request, 'apply_vacancy.html', {'vacancy': vacancy, 'error': 'Введите сопроводительное письмо'})
        Applications.objects.create(
            vacancy = vacancy,
            candidate = request.user,
            letter = letter
        )

        return redirect('my_applications')

    return render(request, 'apply_vacancy.html', {'vacancy': vacancy})


@login_required
def my_applications(request):
    
    if not is_condidate(request.user):
        return redirect('home')

    applications = Applications.objects.filter(candidate = request.user).select_related('vacancy__company').order_by('-created_at')

    return render(request, 'my_applications.html', {"applications": applications})



@login_required
@permission_required('job_portal.view_applications', raise_exception = True)
def vacancy_applications(request, id):

    vacancy = get_object_or_404(Vacancy.objects.select_related('company'), pk = id)

    if vacancy.company.owner != request.user:
        return redirect('home')

    applications = vacancy.applications.select_related('candidate__candidateprofile').order_by('-created_at')

    status = request.GET.get('status', "").strip()


    if status in dict(Applications.STATUSES):
        applications = applications.filter(status = status)

    context = {
        'vacancy': vacancy,
        'applications': applications,
        'statuses': Applications.STATUSES,
        'current_status': status
    }

    return render(request, 'vacancy_applications.html', context)




@login_required
@permission_required('job_portal.can_change_status', raise_exception = True)
def edit_application(request, id):

    application = get_object_or_404(Applications.objects.select_related('vacancy__company'), pk = id)

    if application.vacancy.company.owner != request.user:
        return redirect('home')

    if request.method == "POST":
        status = request.POST.get('status', "")

        if status in ('accepted', 'rejected'):
            application.status = status
            application.save()

        
    return redirect('vacancy_applications', id = application.vacancy.id)




@login_required
@permission_required('job_portal.change_company', raise_exception = True)
def edit_company(request):

    company = Company.objects.filter(owner = request.user).first()

    if company is None:
        return redirect('create_company')

    if request.method == 'POST':
        data = request.POST
        name = data['name'].strip()
        description = data['description'].strip()
        city = data['city'].strip()

        logo = request.FILES.get('logo')

        company.name = name
        company.description = description
        company.city = city

        if logo:
            company.logo = logo


        company.save()

        return redirect('my_vacancies')

    return render(request, 'edit_company.html', {"company": company})




@login_required
@permission_required('job_portal.change_candidateprofile', raise_exception = True)
def edit_candidate_profile(request):

    profile = CandidateProfile.objects.filter(user = request.user).first()

    if profile is None:
        return redirect('candidate_form')

    if request.method == 'POST':
        data = request.POST
        experience = data.get('experience')

        if experience:
            if experience.isdigit():
                experience = int(data['experience'])
            else:
                return render(request, 'edit_candidate_profile.html', {"profile": profile, "error": "Вводите корректное число или оставьте пустым"})
        else:
            experience = 0

        if request.FILES.get('resume'):
            profile.resume = request.FILES['resume']
        

        profile.full_name = data['full_name']
        profile.city = data['city']
        profile.about = data['about'] 
        profile.skills = data['skills']
        profile.experience = experience

        profile.save()

        return redirect('home')

    return render(request, 'edit_candidate_profile.html', {"profile": profile})






@login_required
@permission_required('job_portal.change_vacancy', raise_exception = True)
def edit_vacancy(request, id):

    vacancy = get_object_or_404(Vacancy.objects.select_related('company'), pk = id)

    if vacancy.company.owner != request.user:
        return redirect('home')

    categories = Category.objects.filter(is_active = True)

    context = {
        "vacancy": vacancy,
        "categories": categories,
        "employment_types": Vacancy.EMPLOYMENT_TYPE
    }

    if request.method == "POST":
        data = request.POST

        title = data.get('title')
        description = data.get('description')
        city = data.get('city')


        category_id = data.get('category')
        category = None

        if category_id and category_id.isdigit():
            category = categories.filter(pk = category_id).first()

        if category is None:
            context["error"] = "Выберите категорию"
            return render(request, 'edit_vacancy.html', context)

        employment = data.get('employment')

        salary_from = data.get('salary_from')

        if salary_from:
            if salary_from.isdigit():
                salary_from = int(salary_from)
            else:
                context["error"] = "Зарплата «от» должна быть числом"
                return render(request, 'edit_vacancy.html', context)
        else:
            salary_from = None

        salary_to = data.get('salary_to')

        if salary_to:
            if salary_to.isdigit():
                salary_to = int(salary_to)
            else:
                context["error"] = "Зарплата «до» должна быть числом"
                return render(request, 'edit_vacancy.html', context)
        else:
            salary_to = None
           
        if salary_from is not None and salary_to is not None and salary_from > salary_to:
            context["error"] = "Зарплата «от» не может быть больше «до»"
            return render(request, 'edit_vacancy.html', context)

        experience = data.get('experience')

        if experience:
            if experience.isdigit():
                experience = int(experience)
            else:
                context["error"] = "Опыт должен быть числом или пустым"
                return render(request, 'edit_vacancy.html', context)
        else:
            experience = 0

        vacancy.category = category
        vacancy.employment = employment
        vacancy.salary_from = salary_from
        vacancy.salary_to = salary_to
        vacancy.title = title
        vacancy.description = description
        vacancy.city = city
        vacancy.experience_required = experience

        vacancy.save()

        return redirect("my_vacancies")
    
    return render(request, 'edit_vacancy.html', context)


@login_required
def add_favorite(request, vacancy_id):

    if not is_condidate(request.user):
        return redirect('home')

    vacancy = get_object_or_404(Vacancy, pk = vacancy_id)

    favorite = Favorite.objects.filter(
        user=request.user,
        vacancy=vacancy
    )

    if favorite.exists():
        favorite.delete()
    else:
        Favorite.objects.create(
            user = request.user,
            vacancy = vacancy
        )

    return redirect('vacancy_info', id = vacancy.id)



@login_required
def remove_favorite(request, favorite_id):

    if not is_condidate(request.user):
        return redirect('home')

    favorite = get_object_or_404(Favorite, id = favorite_id, user = request.user)

    favorite.delete()

    return redirect('my_favorites')



@login_required
def my_favorites(request):
    if not is_condidate(request.user):
        return redirect('home')

    favorites = Favorite.objects.filter(user=request.user).select_related('vacancy', 'vacancy__company',  'vacancy__category')

    return render(request, 'my_favorites.html', {'favorites': favorites})