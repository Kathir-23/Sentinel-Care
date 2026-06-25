from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import *
from .filters import PatientFilter
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import random


# ─── AUTO DEMO DATA CREATOR ───────────────────────────────────────────────────

def initialize_demo_data():
    """Populates doctors and beds if the database is empty to ensure a beautiful out-of-box experience."""
    if Doctor.objects.count() == 0:
        doctors = [
            "Dr. Ramesh Thareja (Cardiology)",
            "Dr. Arti Despande (Neurology)",
            "Dr. G. T. Thampi (Pediatrics)",
            "Dr. Harshad Mehta (Orthopedics)",
            "Dr. Rajesh Ravi (General Medicine)",
            "Dr. Priya Sharma (Emergency Care)"
        ]
        for doc in doctors:
            Doctor.objects.create(name=doc)

    if Bed.objects.count() == 0:
        # Create a nice set of beds across Wards A, B, C, D
        for ward in ['A', 'B', 'C', 'D']:
            for num in range(1, 11):
                bed_id = f"{ward}{num}"
                # Pre-occupy a few beds randomly for a realistic dashboard
                occupied = random.choice([True, False])
                Bed.objects.create(bed_number=bed_id, occupied=occupied)


# ─── AUTH VIEWS ──────────────────────────────────────────────────────────────

def login(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, 'main/login.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        username   = request.POST.get('username', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        if not all([first_name, last_name, email, username, password1, password2]):
            messages.error(request, 'All fields are required.')
            return redirect('signup')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken. Please choose another.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            password=password1,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.save()
        messages.success(request, f'Account created for {username}! Please log in.')
        return redirect('login')
    return render(request, 'main/signup.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('/')


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@login_required(login_url='login')
def dashboard(request):
    # Initialize demo data if DB is completely fresh
    initialize_demo_data()

    patients = Patient.objects.all()
    patient_count = patients.count()
    recovered_count = Patient.objects.filter(status="Recovered").count()
    deceased_count  = Patient.objects.filter(status="Deceased").count()
    
    beds = Bed.objects.all()
    total_beds = beds.count()
    beds_available = Bed.objects.filter(occupied=False).count()
    beds_occupied = Bed.objects.filter(occupied=True).count()

    # Calculate Bed Occupancy %
    occupancy_percentage = round((beds_occupied / total_beds * 100)) if total_beds > 0 else 0

    # Critical Alerts (Patients with status "Critical")
    critical_patients = Patient.objects.filter(status="Critical")

    # Patient List Preview (Next 5 patients)
    patient_preview = Patient.objects.all().order_by('-id')[:5]

    # Mock Roster for Staff on Duty
    staff_on_duty = [
        {"name": "Dr. Ramesh Thareja", "role": "Senior Cardiologist", "status": "Busy", "status_color": "danger"},
        {"name": "Dr. Arti Despande", "role": "Neurologist", "status": "Available", "status_color": "success"},
        {"name": "Nurse Sarah Jenkins", "role": "ICU Head Nurse", "status": "On Break", "status_color": "warning"},
        {"name": "Dr. G. T. Thampi", "role": "Pediatrician", "status": "Available", "status_color": "success"},
        {"name": "Nurse Michael Chang", "role": "Emergency Care", "status": "Busy", "status_color": "danger"},
    ]

    # Mock Upcoming Appointments
    appointments = [
        {"doctor": "Dr. Ramesh Thareja", "patient": "John Miller", "time": "10:30 AM", "room": "ICU-2", "type": "Checkup", "type_color": "primary"},
        {"doctor": "Dr. Harshad Mehta", "patient": "Alice Smith", "time": "11:15 AM", "room": "Ortho-B", "type": "Surgery", "type_color": "danger"},
        {"doctor": "Dr. Arti Despande", "patient": "David Johnson", "time": "01:00 PM", "room": "Neuro-A", "type": "Follow-up", "type_color": "success"},
        {"doctor": "Dr. Rajesh Ravi", "patient": "Robert Brown", "time": "02:30 PM", "room": "Gen-104", "type": "Checkup", "type_color": "primary"},
    ]

    context = {
        'patient_count':        patient_count,
        'recovered_count':      recovered_count,
        'beds_available':       beds_available,
        'beds_occupied':        beds_occupied,
        'deceased_count':       deceased_count,
        'beds':                 beds,
        'occupancy_percentage': occupancy_percentage,
        'critical_patients':    critical_patients,
        'patient_preview':      patient_preview,
        'staff_on_duty':        staff_on_duty,
        'appointments':         appointments,
        'current_time':         timezone.now(),
    }
    return render(request, 'main/dashboard.html', context)


# ─── ADD PATIENT ─────────────────────────────────────────────────────────────

@login_required(login_url='login')
def add_patient(request):
    initialize_demo_data()
    beds    = Bed.objects.filter(occupied=False)
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        name                    = request.POST.get('name', '').strip()
        phone_num               = request.POST.get('phone_num', '').strip()
        patient_relative_name   = request.POST.get('patient_relative_name', '').strip()
        patient_relative_contact= request.POST.get('patient_relative_contact', '').strip()
        address                 = request.POST.get('address', '').strip()
        symptoms_list           = request.POST.getlist('symptoms')
        prior_ailments          = request.POST.get('prior_ailments', '').strip()
        bed_num_sent            = request.POST.get('bed_num', '')
        dob                     = request.POST.get('dob', '')
        status                  = request.POST.get('status', '')
        doctor_name             = request.POST.get('doctor', '')

        if not name:
            messages.error(request, 'Patient name is required.')
            return render(request, 'main/add_patient.html', {'beds': beds, 'doctors': doctors})

        try:
            bed_obj = Bed.objects.get(bed_number=bed_num_sent)
        except Bed.DoesNotExist:
            messages.error(request, f'Bed "{bed_num_sent}" not found.')
            return render(request, 'main/add_patient.html', {'beds': beds, 'doctors': doctors})

        try:
            doctor_obj = Doctor.objects.get(name=doctor_name)
        except Doctor.DoesNotExist:
            messages.error(request, f'Doctor "{doctor_name}" not found.')
            return render(request, 'main/add_patient.html', {'beds': beds, 'doctors': doctors})

        symptoms_value = ','.join(symptoms_list) if symptoms_list else ''

        patient_obj = Patient.objects.create(
            name=name,
            phone_num=phone_num,
            patient_relative_name=patient_relative_name,
            patient_relative_contact=patient_relative_contact,
            address=address,
            symptoms=symptoms_value,
            prior_ailments=prior_ailments,
            bed_num=bed_obj,
            dob=dob if dob else None,
            doctor=doctor_obj,
            status=status,
        )

        bed_obj.occupied = True
        bed_obj.save()

        messages.success(request, f'Patient "{name}" added successfully.')
        return redirect('patient', pk=patient_obj.id)

    context = {'beds': beds, 'doctors': doctors}
    return render(request, 'main/add_patient.html', context)


# ─── PATIENT DETAIL / UPDATE ─────────────────────────────────────────────────

@login_required(login_url='login')
def patient(request, pk):
    patient_obj = get_object_or_404(Patient, id=pk)
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        doctor_name  = request.POST.get('doctor', '').strip()
        doctor_time  = request.POST.get('doctor_time', '').strip()
        doctor_notes = request.POST.get('doctor_notes', '').strip()
        mobile       = request.POST.get('mobile', '').strip()
        mobile2      = request.POST.get('mobile2', '').strip()
        relative_name= request.POST.get('relativeName', '').strip()
        address      = request.POST.get('location', '').strip()
        status       = request.POST.get('status', '').strip()

        try:
            doctor_obj = Doctor.objects.get(name=doctor_name)
        except Doctor.DoesNotExist:
            messages.error(request, f'Doctor "{doctor_name}" not found.')
            return render(request, 'main/patient.html',
                          {'patient': patient_obj, 'doctors': doctors})

        # If the patient status was critical but is now recovered, free the bed
        old_status = patient_obj.status
        patient_obj.phone_num               = mobile
        patient_obj.patient_relative_contact= mobile2
        patient_obj.patient_relative_name   = relative_name
        patient_obj.address                 = address
        patient_obj.doctor                  = doctor_obj
        patient_obj.doctors_visiting_time   = doctor_time
        patient_obj.doctors_notes           = doctor_notes
        patient_obj.status                  = status
        patient_obj.save()

        # Update bed occupancy if recovered/deceased
        if status in ['Recovered', 'Deceased'] and old_status not in ['Recovered', 'Deceased']:
            bed = patient_obj.bed_num
            bed.occupied = False
            bed.save()
        elif status not in ['Recovered', 'Deceased'] and old_status in ['Recovered', 'Deceased']:
            bed = patient_obj.bed_num
            bed.occupied = True
            bed.save()

        messages.success(request, f'Patient "{patient_obj.name}" updated successfully.')
        return redirect('patient', pk=pk)

    context = {'patient': patient_obj, 'doctors': doctors}
    return render(request, 'main/patient.html', context)


# ─── PATIENT LIST ─────────────────────────────────────────────────────────────

@login_required(login_url='login')
def patient_list(request):
    initialize_demo_data()
    patients = Patient.objects.all().select_related('bed_num', 'doctor')
    myFilter = PatientFilter(request.GET, queryset=patients)
    patients = myFilter.qs
    context = {
        'patients': patients,
        'myFilter': myFilter,
    }
    return render(request, 'main/patient_list.html', context)


# ─── AUTOCOMPLETE ─────────────────────────────────────────────────────────────

def autosuggest(request):
    term = request.GET.get('term', '')
    if not term:
        return JsonResponse([], safe=False)
    queryset = Patient.objects.filter(name__icontains=term)
    return JsonResponse([x.name for x in queryset], safe=False)


def autodoctor(request):
    term = request.GET.get('term', '')
    if not term:
        return JsonResponse([], safe=False)
    queryset = Doctor.objects.filter(name__icontains=term)
    return JsonResponse([x.name for x in queryset], safe=False)


# ─── INFO PAGE ────────────────────────────────────────────────────────────────

def info(request):
    return render(request, 'main/info.html')