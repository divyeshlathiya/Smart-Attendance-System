from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse

from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import Student, Attendence
from .filters import AttendenceFilter

# from django.views.decorators import gzip

from .recognizer import Recognizer
from datetime import date
import cv2
import threading
import json

# Global variables for camera control
camera = None
camera_lock = threading.Lock()

class VideoCamera:
    def __init__(self):
        self.video = None
        self.recognizer = None
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.video = cv2.VideoCapture(0)
            self.is_running = True

    def stop(self):
        self.is_running = False
        if self.video:
            self.video.release()
            self.video = None

    def get_frame(self):
        if not self.video or not self.is_running:
            return None
        
        ret, frame = self.video.read()
        if not ret:
            return None
        
        if self.recognizer:
            # Process frame with recognizer
            frame = self.recognizer.process_frame(frame)
        
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def start_recognition(self, details):
        self.recognizer = Recognizer(details)

    def stop_recognition(self):
        recognized_students = []
        details = None
        if self.recognizer:
            recognized_students = self.recognizer.get_recognized_students()
            details = self.recognizer.get_details()
        self.recognizer = None
        return recognized_students, details

def get_camera():
    global camera
    if camera is None:
        with camera_lock:
            if camera is None:  # Double-check pattern
                camera = VideoCamera()
    return camera

def gen(camera):
    while camera.is_running:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@login_required(login_url='login')
def video_feed(request):
    camera = get_camera()
    return StreamingHttpResponse(gen(camera),
                    content_type='multipart/x-mixed-replace; boundary=frame')

@login_required(login_url='login')
def start_attendance(request):
    if request.method == 'POST':
        details = {
            'branch': request.POST['branch'],
            'year': request.POST['year'],
            'section': request.POST['section'],
            'period': request.POST['period'],
            'faculty': request.user.faculty
        }
        
        if Attendence.objects.filter(date=str(date.today()), 
                                  branch=details['branch'], 
                                  year=details['year'], 
                                  section=details['section'],
                                  period=details['period']).count() != 0:
            return JsonResponse({'error': 'Attendance already recorded.'})
        
        camera = get_camera()
        camera.start()
        camera.start_recognition(details)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request method'})

@login_required(login_url='login')
def stop_attendance(request):
    if request.method == 'POST':
        camera = get_camera()
        recognized_students, details = camera.stop_recognition()
        
        if details:  # Only create attendance records if we have details
            # Get all students in the class
            students = Student.objects.filter(
                branch=details['branch'],
                year=details['year'],
                section=details['section']
            )
            
            # Create attendance records for all students
            for student in students:
                attendance = Attendence(
                    Faculty_Name=details['faculty'],
                    Student_ID=str(student.registration_id),
                    period=details['period'],
                    branch=details['branch'],
                    year=details['year'],
                    section=details['section'],
                    status='Present' if str(student.registration_id) in recognized_students else 'Absent'
                )
                attendance.save()
                
        camera.stop()
        return JsonResponse({'recognized_students': recognized_students})
    return JsonResponse({'error': 'Invalid request method'})

@login_required(login_url = 'login')
def home(request):
    studentForm = CreateStudentForm()

    if request.method == 'POST':
        studentForm = CreateStudentForm(data = request.POST, files=request.FILES)
        # print(request.POST)
        stat = False 
        try:
            student = Student.objects.get(registration_id = request.POST['registration_id'])
            stat = True
        except:
            stat = False
        if studentForm.is_valid() and (stat == False):
            studentForm.save()
            name = studentForm.cleaned_data.get('firstname') +" " +studentForm.cleaned_data.get('lastname')
            messages.success(request, 'Student ' + name + ' was successfully added.')
            return redirect('home')
        else:
            messages.error(request, 'Student with Registration Id '+request.POST['registration_id']+' already exists.')
            return redirect('home')

    context = {'studentForm':studentForm}
    return render(request, 'attendence_sys/home.html', context)


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username or Password is incorrect')

    context = {}
    return render(request, 'attendence_sys/login.html', context)

@login_required(login_url = 'login')
def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url = 'login')
def updateStudentRedirect(request):
    context = {}
    if request.method == 'POST':
        try:
            reg_id = request.POST['reg_id']
            branch = request.POST['branch']
            student = Student.objects.get(registration_id = reg_id, branch = branch)
            updateStudentForm = CreateStudentForm(instance=student)
            context = {'form':updateStudentForm, 'prev_reg_id':reg_id, 'student':student}
        except:
            messages.error(request, 'Student Not Found')
            return redirect('home')
    return render(request, 'attendence_sys/student_update.html', context)

@login_required(login_url = 'login')
def updateStudent(request):
    if request.method == 'POST':
        context = {}
        try:
            student = Student.objects.get(registration_id = request.POST['prev_reg_id'])
            updateStudentForm = CreateStudentForm(data = request.POST, files=request.FILES, instance = student)
            if updateStudentForm.is_valid():
                updateStudentForm.save()
                messages.success(request, 'Updation Success')
                return redirect('home')
        except:
            messages.error(request, 'Updation Unsucessfull')
            return redirect('home')
    return render(request, 'attendence_sys/student_update.html', context)


@login_required(login_url='login')
def takeAttendence(request):
    if request.method == 'POST':
        details = {
            'branch': request.POST['branch'],
            'year': request.POST['year'],
            'section': request.POST['section'],
            'period': request.POST['period'],
            'faculty': request.user.faculty
        }
        
        if Attendence.objects.filter(date=str(date.today()),
                                  branch=details['branch'],
                                  year=details['year'],
                                  section=details['section'],
                                  period=details['period']).count() != 0:
            messages.error(request, "Attendance already recorded.")
            return redirect('home')
        
        students = Student.objects.filter(branch=details['branch'],
                                       year=details['year'],
                                       section=details['section'])
        
        context = {
            "students": students,
            "details": details,
            "ta": True
        }
        return render(request, 'attendence_sys/attendence.html', context)
    
    context = {}
    return render(request, 'attendence_sys/home.html', context)

def searchAttendence(request):
    attendences = Attendence.objects.all()
    myFilter = AttendenceFilter(request.GET, queryset=attendences)
    attendences = myFilter.qs
    context = {'myFilter':myFilter, 'attendences': attendences, 'ta':False}
    return render(request, 'attendence_sys/attendence.html', context)


def facultyProfile(request):
    faculty = request.user.faculty
    form = FacultyForm(instance = faculty)
    context = {'form':form}
    return render(request, 'attendence_sys/facultyForm.html', context)



# class VideoCamera(object):
#     def __init__(self):
#         self.video = cv2.VideoCapture(0)
#     def __del__(self):
#         self.video.release()

#     def get_frame(self):
#         ret,image = self.video.read()
#         ret,jpeg = cv2.imencode('.jpg',image)
#         return jpeg.tobytes()


# def gen(camera):
#     while True:
#         frame = camera.get_frame()
#         yield(b'--frame\r\n'
#         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# @gzip.gzip_page
# def videoFeed(request):
#     try:
#         return StreamingHttpResponse(gen(VideoCamera()),content_type="multipart/x-mixed-replace;boundary=frame")
#     except:
#         print("aborted")

# def getVideo(request):
#     return render(request, 'attendence_sys/videoFeed.html')