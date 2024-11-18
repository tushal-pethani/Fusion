from rest_framework.views import APIView
from rest_framework.response import Response

from django.shortcuts import get_object_or_404, redirect, render

from rest_framework import status,permissions
from django.contrib.auth.models import User
from django.http import JsonResponse,HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from ..models import *
from applications.academic_information.models import Student
from .serializers import PlacementScheduleSerializer, NotifyStudentSerializer
import json

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.utils.decorators import method_decorator
from applications.globals.models import ExtraInfo
from applications.academic_information.api.serializers import StudentSerializers
import datetime
import io
from reportlab.pdfgen import canvas
from django.views.decorators.csrf import csrf_exempt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,ListFlowable,ListItem
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Line,Drawing

class PlacementScheduleView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        combined_data = []

        notify_students = NotifyStudent.objects.all()
        for notify in notify_students:
            placements = PlacementSchedule.objects.filter(notify_id=notify.id)
            placement_serializer = PlacementScheduleSerializer(placements, many=True)
            notify_data = NotifyStudentSerializer(notify).data

            for placement in placement_serializer.data:
                combined_entry = {**notify_data, **placement}
                combined_data.append(combined_entry)

        return Response(combined_data)

    def post(self, request):
        placement_type = request.data.get("placement_type")
        company_name = request.data.get("company_name")
        ctc = request.data.get("ctc")
        description = request.data.get("description")
        schedule_at = request.data.get("schedule_at")
        date = request.data.get("placement_date")
        location = request.data.get("location")
        role = request.data.get("role")
        resume = request.FILES.get("resume")

        try:
            role_create, _ = Role.objects.get_or_create(role=role)
            notify = NotifyStudent.objects.create(
                placement_type=placement_type,
                company_name=company_name,
                description=description,
                ctc=ctc,
                timestamp=schedule_at,
            )

            schedule = PlacementSchedule.objects.create(
                notify_id=notify,
                title=company_name,
                description=description,
                placement_date=date,
                attached_file=resume,
                role=role_create,
                location=location,
                time=schedule_at,
            )


            return redirect('placement')

            return JsonResponse({"message": "Successfully Added Schedule"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)




@csrf_exempt
def placement_schedule_save(request):
    permission_classes = [permissions.AllowAny]
    if request.method != "POST":
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    placement_type = request.POST.get("placement_type")
    company_name = request.POST.get("company_name")
    ctc = request.POST.get("ctc")
    description = request.POST.get("description")
    timestamp = request.POST.get("time_stamp")
    title = request.POST.get("title")
    location = request.POST.get("location")
    role = request.POST.get("role")
    
    resume = request.FILES.get("resume")
    schedule_at = request.POST.get("schedule_at")
    date = request.POST.get("placement_date")

    try:
        role_create, _ = Role.objects.get_or_create(role=role)
        
        notify = NotifyStudent.objects.create(
            placement_type=placement_type,
            company_name=company_name,
            description=description,
            ctc=ctc,
            timestamp=timestamp
        )

        schedule = PlacementSchedule.objects.create(
            notify_id=notify,
            title=company_name,
            description=description,
            placement_date=date,
            attached_file=resume,
            role=role_create,
            location=location,
            time=schedule_at
        )

        return JsonResponse({"message": "Successfully Added Schedule"}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



class BatchStatisticsView(APIView):

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        combined_data = []
        student_records = StudentRecord.objects.all()

        if not student_records.exists():
            return Response({"error": "No student records found"}, status=status.HTTP_404_NOT_FOUND)

        for student in student_records:
            try:

                cur_student = Student.objects.get(id_id=student.unique_id_id)
                cur_placement = PlacementRecord.objects.get(id=student.record_id_id)
                user = User.objects.get(username=student.unique_id_id)

                combined_entry = {
                    "branch": cur_student.specialization, 
                    "batch" : cur_placement.year, 

                    "placement_name": cur_placement.name,  
                    "ctc": cur_placement.ctc, 
                    "year": cur_placement.year, 
                    "first_name": user.first_name 
                }

                combined_data.append(combined_entry)

            except Student.DoesNotExist:
                return Response({"error": f"Student with id {student.unique_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            except PlacementRecord.DoesNotExist:
                return Response({"error": f"Placement record with id {student.record_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            except User.DoesNotExist:
                return Response({"error": f"User with id {student.unique_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not combined_data:
            return Response({"message": "No combined data found"}, status=status.HTTP_204_NO_CONTENT)

        return Response(combined_data, status=status.HTTP_200_OK)


    def post(self,request):
        placement_type=request.POST.get("placement_type")
        company_name=request.POST.get("company_name")
        roll_no = request.POST.get("roll_no")
        ctc=request.POST.get("ctc")
        year=request.POST.get("year")
        test_type=request.POST.get("test_type")
        test_score=request.POST.get("test_score")

        try:
            p2 = PlacementRecord.objects.create(
                placement_type = placement_type,
                name = company_name,
                ctc = ctc,
                year = year,
                test_score = test_score,
                test_type = test_type,
            )
            p1 = StudentRecord.objects.create(
                record_id = p2,
                unique_id_id = roll_no,
            )
            return JsonResponse({"message": "Successfully Added"}, status=201)
    
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            

    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def generate_cv(request):
    fields = request.data
    user = request.user

    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=401)

    profile = get_object_or_404(Student, id__user=user)

    # Initialize PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=20,
        leftMargin=30,  # Reduced left margin
        rightMargin=30,  # Reduced right margin
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="Title",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=10,
        alignment=1,  # Center alignment
    )
    section_header_style = ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceAfter=4,  # Reduce space after section header
        textColor=colors.HexColor("#c43119"),  # Custom color
    )
    body_style = styles["BodyText"]
    body_style.fontSize = 11
    body_style.leading = 14

    # Helper to format dates
    def format_date(date):
        return date.strftime("%d %B %Y") if date else "Ongoing"

    # Content container
    content = []

    # Add dynamic sections with optional bullet points
    def add_section(title, queryset, formatter, bullet_points=False):
        content.append(Paragraph(title, section_header_style))
        # Add a horizontal line under the section header
        line = Line(0, 0, 500, 0, strokeColor=colors.HexColor("#c43119"))  # Adjust line length
        drawing = Drawing(500, 1)  # Adjust drawing width
        drawing.add(line)
        content.append(drawing)
        content.append(Spacer(1, 4))  # Reduce space between header and content

        if bullet_points:
            # Add items as a bulleted list
            items = [Paragraph(formatter(obj), body_style) for obj in queryset]
            content.append(ListFlowable(
                [ListItem(i) for i in items],
                bulletType="bullet",  # Use bullets
                start="circle",  # Specify bullet style
                leftIndent=10,  # Indent for bullets
                bulletFontSize=8,  # Decrease bullet size
                bulletOffset=10,  # Increase space between bullet and text
            ))
        else:
            # Add items normally
            for obj in queryset:
                content.append(Paragraph(formatter(obj), body_style))
        content.append(Spacer(1, 8))  # Reduce space between sections

    # Title
    content.append(Paragraph(f"{user.get_full_name()}", title_style))
    content.append(Spacer(1, 8))  # Reduce space after title

    # Dynamic Sections
    if fields.get("achievements", False):
        achievements = Achievement.objects.filter(unique_id=profile)
        add_section(
            "Achievements",
            achievements,
            lambda a: f"{a.achievement} ({a.achievement_type}) - {a.issuer} ({format_date(a.date_earned)})",
            bullet_points=True,
        )

    if fields.get("education", False):
        education = Education.objects.filter(unique_id=profile)
        add_section(
            "Education",
            education,
            lambda e: f"{e.degree} in {e.stream or 'General'} from {e.institute}, Grade: {e.grade} ({format_date(e.sdate)} - {format_date(e.edate)})"
        )

    if fields.get("skills", False):
        skills = Has.objects.filter(unique_id=profile)
        add_section(
            "Skills",
            skills,
            lambda s: f"{s.skill_id.skill} (Rating: {s.skill_rating}%)",
            bullet_points=True,
        )

    if fields.get("experience", False):
        experience = Experience.objects.filter(unique_id=profile)
        add_section(
            "Experience",
            experience,
            lambda e: f"<b>{e.title}</b> at {e.company} ({format_date(e.sdate)} - {format_date(e.edate)})<br/>{e.description or 'No description'}"
        )

    if fields.get("projects", False):
        projects = Project.objects.filter(unique_id=profile)
        add_section(
            "Projects",
            projects,
            lambda p: f"<b>{p.project_name}</b><br/>{p.summary or 'No description'} (Status: {p.project_status})",
            bullet_points=True,
        )

    if fields.get("courses", False):
        courses = Course.objects.filter(unique_id=profile)
        add_section(
            "Courses",
            courses,
            lambda c: f"{c.course_name} - {c.description or 'No description'} (License: {c.license_no or 'N/A'})",
            bullet_points=True,
        )

    # Build the PDF
    doc.build(content)
    buffer.seek(0)

    # Response
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="resume.pdf"'
    return response








