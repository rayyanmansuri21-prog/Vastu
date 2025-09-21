from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from main.models import Project, UserProfile
from .forms import ProjectForm
from django.http import JsonResponse
import base64
from django.http import HttpResponse,JsonResponse
from fpdf import FPDF
from io import BytesIO
from PIL import Image
from django.views.decorators.csrf import csrf_exempt
import random
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
import math
import json
from .utils import calculate_directional_areas
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io,base64
from django.db.models import Count,OuterRef,Subquery    
from docx import Document
from docx.shared import Inches,Pt, RGBColor
from django.core.files.base import ContentFile
import traceback
from .models import Project
from docx.enum.style import WD_STYLE_TYPE
import os
from datetime import datetime
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn



def generate_otp():
    return str(random.randint(1000, 9999))  # 4-digit OTP

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        if username and email:
            otp = generate_otp()

            # ✨ HTML message for email
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: #f9f9f9;">
                <h2 style="color: #4A00E0;">🔮 Cosmo-Vastu OTP Verification</h2>
                <p>Hi <strong>{username}</strong>,</p>
                <p>Thank you for signing up at <strong>Cosmo Vastu</strong>!<br>
                Use the following OTP to complete your verification:</p>
                <div style="font-size: 24px; font-weight: bold; color: #4A00E0; margin: 20px 0; letter-spacing: 5px;">
                    {otp}
                </div>
                <p>This OTP is valid for a limited time only. Please do not share it with anyone.</p>
                <br>
                <p style="font-size: 13px; color: #777;">© {username} | Cosmo Vastu Team</p>
            </div>
            """

            send_mail(
                subject='Your Cosmo-Vastu OTP',
                message=f'Hello {username}, your OTP is: {otp}',  # fallback plain text
                from_email='your_email@gmail.com',
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message
            )

            request.session['otp'] = otp
            request.session['email'] = email
            request.session['username'] = username

            return redirect('verify_otp')
        else:
            return render(request, 'login.html', {'error': 'All fields are required.'})

    return render(request, 'login.html')


def verify_otp(request):
    # 1️⃣  Handle POST – जब यूज़र ने 4 डिजिट लिखकर सबमिट किया
    if request.method == "POST":
        # 4 textbox values → एक स्ट्रिंग
        otp_digits = [request.POST.get(f'otp{i}') for i in range(1, 5)]
        if None in otp_digits:                          # कोई बॉक्स खाली है?
            return render(request, "verify_otp.html",
                          {"error": "OTP incomplete."})

        user_otp = "".join(otp_digits)                  # e.g. "5739"

        # 2️⃣  Mail भेजते वक़्त जो चीज़ें सेशन में रखी थीं, निकाल लो
        session_otp = request.session.get("otp")
        email       = request.session.get("email")
        username    = request.session.get("username")

        # 3️⃣  OTP मैच करता है?
        if user_otp == session_otp:
            #  ⬇️ auth_user में यूज़र ढूँढो या नया बना दो
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            if created:
                user.set_unusable_password()   # हम OTP लॉग‑इन कर रहे हैं
                user.save()

            # 4️⃣  लॉग‑इन कर दो (session auth)
            login(request, user)

            # 5️⃣  Email को फिर से session में डाल दो (आगे काम आयेगा)
            request.session["email"] = user.email

            return redirect("dashboard")

        # ❌ OTP ग़लत
        return render(request, "verify_otp.html",
                      {"error": "Invalid OTP. Try again."})

    # GET request – सिर्फ़ पेज दिखा दो
    return render(request, "verify_otp.html")



@login_required
def dashboard_view(request):
    user = request.user
    recent_projects = Project.objects.filter(user=user).order_by('-created_at')[:3]

    # Fetch project limit from user profile
    try:
        user_profile = UserProfile.objects.get(user=user)
        project_limit = user_profile.project_limit
    except UserProfile.DoesNotExist:
        project_limit = 5  # fallback in case profile not found

    current_project_count = Project.objects.filter(user=user).count()
    limit_reached = current_project_count >= project_limit

    all_projects = Project.objects.filter(user=user).order_by('-created_at')

    return render(request, 'dashboard.html', {
        'recent_projects': recent_projects,
        'limit_reached': limit_reached,
        'user_profile': user,
        'all_projects': all_projects,
        'project_count': current_project_count,
        'project_limit': project_limit
    })

def success_view(request):
    return render(request, 'success.html')

def project_success(request):
    return render(request, 'blueprint_workspace.html')


# @login_required
# def create_project(request):
#     if request.method == 'POST':
#         user = request.user
#         user_profile = request.user.userprofile
#         user_projects = Project.objects.filter(user=request.user).count()
        
#         if user_projects >= user_profile.project_limit:
#             messages.error(request, "You have reached your project creation limit.")
#             return redirect('dashboard')
            
#         name = request.POST.get('projectName')
#         description = request.POST.get('description')
#         status = request.POST.get('status')
#         category = request.POST.get('category')
#         blueprint = request.FILES.get('blueprint')

#         if not all([name, description, status, category, blueprint]):
#             messages.error(request, "All fields are required.")
#             return redirect('dashboard')

#         Project.objects.create(
#             user=user,
#             name=name,
#             description=description,
#             status=status,
#             category=category,
#             blueprint=blueprint,
#         )

#         return redirect('blueprint_workspace', project_id=project.id)

#     return redirect('dashboard')

#old function 3 project creation limit
@login_required
def create_project(request):
    if request.method == 'POST':
        user = request.user  
        user_profile = UserProfile.objects.get(user=request.user)
        project_count = Project.objects.filter(user=request.user).count()
        if project_count >= user_profile.project_limit:
            messages.error(request, "You have reached your project creation limit.")
            return redirect('dashboard')

        # --- grab the fields that came from the form ---
        name        = request.POST.get('projectName')
        description = request.POST.get('description')
        status      = request.POST.get('status')
        category    = request.POST.get('category')
        blueprint   = request.FILES.get('blueprint')

        if not all([name, description, status, category, blueprint]):
            messages.error(request, "All fields are required.")
            return redirect('dashboard')

        project = Project.objects.create(
            user        = user,                 # 🔗 who owns it
            name        = name,
            description = description,
            status      = status,
            category    = category,
            blueprint   = blueprint,
        )
        return redirect('blueprint_workspace', project_id=project.id)

    # GET
    return redirect('dashboard')


def blueprint_workspace(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    return render(request, 'blueprint_workspace.html', {'project': project})

# def blueprint_workspace(request, blueprint_path):
#     return render(request, 'blueprint_workspace.html', {'blueprint_path': blueprint_path})

# @login_required
def increase_project_limit(request, user_id):
    if request.method == "POST":
        extra_limit = int(request.POST.get("extra_limit", 0))
        
        user_to_update = get_object_or_404(User, id=user_id)
        
        user_profile, created = UserProfile.objects.get_or_create(user=user_to_update)

        # Limit ko badhayein
        user_profile.project_limit += extra_limit
        user_profile.save()

        # User ko email bhejein
        email_context = {
            'username': user_to_update.username,
            'extra_limit': extra_limit,
            'new_limit': user_profile.project_limit,
        }

        # Step 3: HTML template ko render karein
        # 'emails/project_limit_increased.html' path se template ko load karein aur context ke saath render karein.
        html_message = render_to_string('emails/project_limit_increased.html', email_context)
        
        # Step 4: HTML message ka plain text version banayein
        # Yeh un email clients ke liye fallback hai jo HTML support nahi karte.
        plain_message = strip_tags(html_message)

        # Step 5: User ko naye design wala email bhejein
        try:
            send_mail(
                subject="🚀 Project Limit Increased",
                message=plain_message,  # Plain text message (fallback ke liye)
                from_email="your_admin_email@example.com",  # Apna email yahan daalein
                recipient_list=[user_to_update.email],
                fail_silently=False,
                html_message=html_message,  # HTML version yahan pass karein
            )
            messages.success(request, f"{user_to_update.username}'s project limit has been increased successfully.")
        except Exception as e:
            messages.warning(request, f"Limit was increased for {user_to_update.username}, but failed to send email. Error: {e}")

        # Apne admin dashboard ke URL name par redirect karein
        return redirect("admin_dashboard") 

    # Agar POST request nahi hai, to bhi dashboard par bhej dein
    return redirect("admin_dashboard")  


# @csrf_exempt
# def download_blueprint(request):
#     if request.method == "POST":
#         # 1. Image
#         image_data = request.POST.get("image_data", "").split(",")[-1]
#         blueprint_img = base64.b64decode(image_data)

#         # 2. Session values
#         grid_points = request.session.get("grid_points", [])
#         compass_center = request.session.get("compass_center", [0, 0])
#         divisions = request.session.get("divisions", 8)

#         # 3. Calculate direction-wise area
#         direction_counts = calculate_directional_areas(
#             [tuple(p) for p in grid_points], tuple(compass_center), divisions
#         )
#         zones = divisions
#         values = list(direction_counts.values())

#         if zones > 0 and values:
#             total = sum(values)
#             avg = total / zones
#             max_line = (avg + max(values)) / 2
#             min_line = (avg + min(values)) / 2
#         else:
#             total = avg = max_line = min_line = 0

#         # 4. Assign zone-based color scheme
#         color_map = {}
#         if divisions == 8:
#             color_map = {
#                 "N": "blue", "NE": "blue", "E": "green", "SE": "red",
#                 "S": "red", "SW": "yellow", "W": "grey", "NW": "grey"
#             }
#         elif divisions == 16:
#             for d in direction_counts:
#                 if d in ["NNW", "N", "NNE", "NE"]:
#                     color_map[d] = "blue"
#                 elif d in ["ENE", "E", "ESE"]:
#                     color_map[d] = "green"
#                 elif d in ["SE", "SSE", "S"]:
#                     color_map[d] = "red"
#                 elif d in ["SW", "SSW"]:
#                     color_map[d] = "yellow"
#                 elif d in ["WSW", "W", "WNW", "NW"]:
#                     color_map[d] = "grey"
#                 else:
#                     color_map[d] = "black"
#         elif divisions == 32:
#             for d in direction_counts:
#                 if d in ["N5", "N6", "N7", "N8", "E1", "N2", "N3", "N4"]:
#                     color_map[d] = "blue"
#                 elif d in ["E2", "E3", "E4", "E5", "E6", "E7"]:
#                     color_map[d] = "green"
#                 elif d in ["E8", "S1", "S2", "S3", "S4", "S5"]:
#                     color_map[d] = "red"
#                 elif d in ["S6", "S7", "S8", "W1"]:
#                     color_map[d] = "yellow"
#                 elif d in ["W2", "W3", "W4", "W5", "W6", "W7", "W8", "N1"]:
#                     color_map[d] = "grey"
#                 else:
#                     color_map[d] = "black"


#         bar_colors = [color_map.get(k, "black") for k in direction_counts.keys()]

#         # 5. Plot Graph
#         fig, ax = plt.subplots(figsize=(10, 4))
#         ax.bar(direction_counts.keys(), direction_counts.values(), color=bar_colors)
#         ax.axhline(avg, color='red', linestyle='--', label='AVG AREA')
#         ax.axhline(max_line, color='purple', linestyle='--', label='MAX LINE')
#         ax.axhline(min_line, color='green', linestyle='--', label='MIN LINE')
#         ax.set_title("Zone-wise Area Distribution with Threshold Indicators")
#         ax.set_xlabel("Zone")
#         ax.set_ylabel("Area (sq units)")
#         ax.legend()
#         ax.grid(True)
#         plt.xticks(rotation=45)
#         plt.tight_layout()

#         graph_buffer = io.BytesIO()
#         plt.savefig(graph_buffer, format='PNG')
#         graph_buffer.seek(0)

#         # 6. Create PDF
#         pdf_buffer = io.BytesIO()
#         p = canvas.Canvas(pdf_buffer, pagesize=A4)

#         # First page - Blueprint
#         p.drawString(50, 800, "Cosmo Vastu - Blueprint Analysis")
#         blueprint_reader = ImageReader(io.BytesIO(blueprint_img))
#         p.drawImage(blueprint_reader, 50, 200, width=500, preserveAspectRatio=True, mask='auto')

#         p.setFont("Helvetica", 10)
#         p.drawString(50, 180, f"Total Area: {total}")
#         p.drawString(200, 180, f"Zones: {zones}")
#         p.drawString(50, 160, f"Avg Area: {round(avg, 2)}")
#         p.drawString(200, 160, f"Max Line: {round(max_line, 2)}")
#         p.drawString(350, 160, f"Min Line: {round(min_line, 2)}")

#         p.showPage()

#         # Second page - Graph
#         p.drawImage(ImageReader(graph_buffer), 50, 250, width=500, preserveAspectRatio=True, mask='auto')
#         p.showPage()

#         p.save()
#         pdf_buffer.seek(0)
#         return HttpResponse(pdf_buffer, content_type="application/pdf")

def save_project_image(request, project_id):
    if request.method == 'POST':
        try:
            project = get_object_or_404(Project, pk=project_id)
            data = json.loads(request.body)
            
            image_data_b64 = data.get('image_data')
            image_type = data.get('image_type') # e.g., 'centroid', 'compass'

            if not image_data_b64 or not image_type:
                return JsonResponse({"status": "error", "message": "Missing data"}, status=400)

            # Base64 डेटा को डीकोड करें
            format, imgstr = image_data_b64.split(';base64,') 
            ext = format.split('/')[-1] 
            image_file = ContentFile(base64.b64decode(imgstr), name=f'{project_id}_{image_type}.{ext}')

            # सही फ़ील्ड में सेव करें
            if image_type == 'centroid':
                project.centroid_image = image_file
            elif image_type == 'compass':
                project.compass_image = image_file
            elif image_type == 'divided_8':
                project.divided_8_image = image_file
            elif image_type == 'divided_16':
                project.divided_16_image = image_file
            elif image_type == 'divided_32':
                project.divided_32_image = image_file
            
            project.save()
            return JsonResponse({"status": "success", "message": f"{image_type} image saved."})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


# @csrf_exempt
# def download_blueprint(request):
#     if request.method == "POST":
        
#         grid_points = request.session.get("grid_points", [])
#         compass_center = request.session.get("compass_center", [0, 0])
#         divisions = request.session.get("divisions", 8)
#         compass_rotation = request.session.get("compass_rotation", 0)

#         # 3. Calculate direction-wise area (Aapka code - Koi badlaav nahi)
#         direction_counts = calculate_directional_areas(
#             [tuple(p) for p in grid_points], tuple(compass_center), divisions, compass_rotation
#         )
#         zones = divisions
#         values = list(direction_counts.values())

#         if zones > 0 and values:
#             total = sum(values)
#             avg = total / zones
#             max_line = (avg + max(values)) / 2
#             min_line = (avg + min(values)) / 2
#         else:
#             total = avg = max_line = min_line = 0

#         # 4. Assign zone-based color scheme (Aapka code - Koi badlaav nahi)
#         color_map = {}
#         if divisions == 8:
#             color_map = {
#                 "N": "blue", "NE": "blue", "E": "green", "SE": "red",
#                 "S": "red", "SW": "yellow", "W": "grey", "NW": "grey"
#             }
#         elif divisions == 16:
#             for d in direction_counts:
#                 if d in ["NNW", "N", "NNE", "NE"]:
#                     color_map[d] = "blue"
#                 elif d in ["ENE", "E", "ESE"]:
#                     color_map[d] = "green"
#                 elif d in ["SE", "SSE", "S"]:
#                     color_map[d] = "red"
#                 elif d in ["SW", "SSW"]:
#                     color_map[d] = "yellow"
#                 elif d in ["WSW", "W", "WNW", "NW"]:
#                     color_map[d] = "grey"
#                 else:
#                     color_map[d] = "black"
#         elif divisions == 32:
#             for d in direction_counts:
#                 if d in ["N5", "N6", "N7", "N8", "E1", "N2", "N3", "N4"]:
#                     color_map[d] = "blue"
#                 elif d in ["E2", "E3", "E4", "E5", "E6", "E7"]:
#                     color_map[d] = "green"
#                 elif d in ["E8", "S1", "S2", "S3", "S4", "S5"]:
#                     color_map[d] = "red"
#                 elif d in ["S6", "S7", "S8", "W1"]:
#                     color_map[d] = "yellow"
#                 elif d in ["W2", "W3", "W4", "W5", "W6", "W7", "W8", "N1"]:
#                     color_map[d] = "grey"
#                 else:
#                     color_map[d] = "black"
#             pass
#         bar_colors = [color_map.get(k, "black") for k in direction_counts.keys()]

#         # 5. Plot Graph (Aapka code - Koi badlaav nahi)
#         fig, ax = plt.subplots(figsize=(10, 4))
#         ax.bar(direction_counts.keys(), direction_counts.values(), color=bar_colors)
#         ax.axhline(avg, color='red', linestyle='--', label='AVG AREA')
#         ax.axhline(max_line, color='purple', linestyle='--', label='MAX LINE')
#         ax.axhline(min_line, color='green', linestyle='--', label='MIN LINE')
#         ax.set_title("Zone-wise Area Distribution with Threshold Indicators")
#         ax.set_xlabel("Zone")
#         ax.set_ylabel("Area (sq units)")
#         ax.legend()
#         ax.grid(True, linestyle='--', alpha=0.6)
#         plt.xticks(rotation=45, ha="right")
#         plt.tight_layout()

#         graph_buffer = io.BytesIO()
#         plt.savefig(graph_buffer, format='PNG')
#         graph_buffer.seek(0)
#         plt.close(fig) # Graph banane ke baad figure ko close karna achhi practice hai

#         return HttpResponse(graph_buffer, content_type="image/png")

#     # Agar POST request na ho to yeh message dikhana
#     return HttpResponse("This endpoint requires a POST request.", status=405)

@csrf_exempt
def download_blueprint(request):
    """
    Generates a zone-wise area bar chart image (PNG) using session grid_points and centroid info.

    Behavior:
    - Reads grid_points (flexible formats), compass_center, divisions, compass_rotation from session.
    - Uses session['centroid_radius'] if present to only count points within that radius from compass_center.
      Otherwise counts all grid_points.
    - Maps points to sectors with 0° = North (clockwise), applies compass_rotation offset.
    - Uses exact label orders you requested for 8 / 16 / 32.
    - Returns PNG image of the bar chart.
    """
    try:
        if request.method != "POST":
            return HttpResponse("This endpoint requires a POST request.", status=405)

        grid_points = request.session.get("grid_points", [])
        compass_center = request.session.get("compass_center", [0, 0])
        divisions = int(request.session.get("divisions", 8))
        compass_rotation = float(request.session.get("compass_rotation", 0))
        # Optional: radius up to which to count boxes (in same units as grid_points coords)
        centroid_radius = request.session.get("centroid_radius", None)

        # ensure compass_center numeric tuple
        cx, cy = float(compass_center[0]), float(compass_center[1])

        # --- Normalize grid_points into list of (x, y, inside_flag) ---
        normalized = []
        for p in grid_points:
            # support different formats:
            # tuple/list: (x,y) or (x,y,inside)
            # dict: {"x":..,"y":.., "inside": True/False (optional)}
            if isinstance(p, dict):
                x = float(p.get("x", p.get("0", 0)))
                y = float(p.get("y", p.get("1", 0)))
                inside = p.get("inside", True)
            elif isinstance(p, (list, tuple)):
                if len(p) >= 3:
                    x, y, inside = float(p[0]), float(p[1]), bool(p[2])
                else:
                    x, y, inside = float(p[0]), float(p[1]), True
            else:
                # can't parse: skip
                continue
            normalized.append((x, y, inside))

        # If no points available, still return an empty chart
        if not normalized:
            direction_counts = {}
            labels = []
        else:
            # --- decide radius cutoff ---
            if centroid_radius is not None:
                try:
                    cutoff = float(centroid_radius)
                except Exception:
                    cutoff = None
            else:
                cutoff = None

            # if cutoff not provided, include all points (or optionally compute max)
            # We'll include all points if cutoff is None.

            # --- label sequences as requested by user ---
            labels_8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            labels_16 = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
            labels_32 = [
                "N5","N6","N7","N8",
                "E1","E2","E3","E4","E5","E6","E7","E8",
                "S1","S2","S3","S4","S5","S6","S7","S8",
                "W1","W2","W3","W4","W5","W6","W7","W8",
                "N1","N2","N3","N4"
            ]

            if divisions == 8:
                labels = labels_8
            elif divisions == 16:
                labels = labels_16
            elif divisions == 32:
                labels = labels_32
            else:
                # fallback: generate generic labels
                sector_size = 360.0 / divisions
                labels = [f"S{i+1}" for i in range(divisions)]

            # initialize counts
            direction_counts = {lab: 0 for lab in labels}

            # helper: compute angle where 0 = North, increasing clockwise
            import math
            def angle_from_center(x, y):
                dx = x - cx
                dy = y - cy
                # atan2 returns angle from x-axis (east) with positive counterclockwise.
                # We want 0 = North and clockwise positive.
                # One way: compute bearing = (90 - math.degrees(atan2(dy, dx))) % 360
                # But to ensure 0 = North and clockwise:
                bearing = (90.0 - math.degrees(math.atan2(dy, dx))) % 360.0
                return bearing

            sector_size = 360.0 / float(divisions)

            for (x, y, inside) in normalized:
                if not inside:
                    continue
                # apply cutoff radius if given
                if cutoff is not None:
                    dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
                    if dist > cutoff:
                        continue

                ang = angle_from_center(x, y)
                # apply compass rotation offset (positive rotates clockwise)
                ang = (ang + float(compass_rotation)) % 360.0

                # center sectors around principal bearings: add half-sector to align
                # so that label at index 0 corresponds to angle near 0
                idx = int(((ang + sector_size / 2.0) % 360.0) // sector_size) % divisions

                # map idx -> label (for provided label lists)
                if idx < len(labels):
                    lab = labels[idx]
                else:
                    lab = labels[idx % len(labels)]
                direction_counts[lab] = direction_counts.get(lab, 0) + 1

        # --- Prepare color mapping similar to your rules (keeps style) ---
        bar_colors = []
        # for 8 / 16 / 32 keep mapping you specified
        if divisions == 8:
            color_map = {"N":"blue","NE":"blue","E":"green","SE":"red","S":"red","SW":"yellow","W":"grey","NW":"grey"}
        elif divisions == 16:
            color_map = {}
            for d in labels:
                if d in ["NNW","N","NNE","NE"]:
                    color_map[d] = "blue"
                elif d in ["ENE","E","ESE"]:
                    color_map[d] = "green"
                elif d in ["SE","SSE","S"]:
                    color_map[d] = "red"
                elif d in ["SW","SSW"]:
                    color_map[d] = "yellow"
                elif d in ["WSW","W","WNW","NW"]:
                    color_map[d] = "grey"
                else:
                    color_map[d] = "black"
        elif divisions == 32:
            color_map = {}
            for d in labels:
                if d in ["N5","N6","N7","N8","E1","N2","N3","N4"]:
                    color_map[d] = "blue"
                elif d in ["E2","E3","E4","E5","E6","E7"]:
                    color_map[d] = "green"
                elif d in ["E8","S1","S2","S3","S4","S5"]:
                    color_map[d] = "red"
                elif d in ["S6","S7","S8","W1"]:
                    color_map[d] = "yellow"
                elif d in ["W2","W3","W4","W5","W6","W7","W8","N1"]:
                    color_map[d] = "grey"
                else:
                    color_map[d] = "black"
        else:
            color_map = {lab: "blue" if i % 2 == 0 else "grey" for i, lab in enumerate(labels)}

        bar_colors = [color_map.get(k, "black") for k in direction_counts.keys()]

        # --- compute some threshold lines for nicer plot (optional) ---
        values = list(direction_counts.values())
        if values:
            total = sum(values)
            zones = len(values)
            avg = total / zones if zones else 0
            max_line = (avg + max(values)) / 2.0
            min_line = (avg + min(values)) / 2.0
        else:
            avg = max_line = min_line = 0

        # --- plot using matplotlib ---
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 4))
        keys = list(direction_counts.keys())
        vals = [direction_counts[k] for k in keys]
        ax.bar(keys, vals, color=bar_colors)
        if any(values):
            ax.axhline(avg, color='red', linestyle='--', label='AVG')
            ax.axhline(max_line, color='purple', linestyle='--', label='MAX-LINE')
            ax.axhline(min_line, color='green', linestyle='--', label='MIN-LINE')
            ax.legend()
        ax.set_title("Zone-wise Box Count Distribution")
        ax.set_xlabel("Zone")
        ax.set_ylabel("Count")
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        graph_buffer = io.BytesIO()
        plt.savefig(graph_buffer, format='PNG', dpi=150)
        graph_buffer.seek(0)
        plt.close(fig)

        return HttpResponse(graph_buffer.getvalue(), content_type="image/png")
    except Exception:
        # log on server console (helpful)
        print("ERROR generating graph:")
        print(traceback.format_exc())
        return HttpResponse(status=500)


@csrf_exempt
def generate_graph_data_view(request, project_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            divisions = data.get('divisions')

            if not divisions:
                return JsonResponse({'error': 'Divisions not provided'}, status=400)

            compass_rotation = request.session.get("compass_rotation", 0)
            grid_points = request.session.get("grid_points", [])
            compass_center = request.session.get("compass_center", [])

            if not grid_points or not compass_center:
                return JsonResponse({'error': 'Grid or compass data not found in session. Please recalculate.'}, status=400)

            image_bytes_io = generate_graph_image(grid_points, compass_center, divisions, compass_rotation)
            

            if image_bytes_io:
                image_base64 = base64.b64encode(image_bytes_io.read()).decode('utf-8')
                
                return JsonResponse({
                    'graph_image_base64': image_base64
                })
            else:
                return JsonResponse({'error': 'The generate_graph_image function failed and returned None.'}, status=500)

        except Exception as e:
            print(f"ERROR in generate_graph_data_view: {e}") 
            return JsonResponse({'error': f'An unexpected error occurred on the server: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def generate_graph_image(grid_points, compass_center, divisions, compass_rotation):
    try:
        direction_counts = calculate_directional_areas(
            [tuple(p) for p in grid_points], tuple(compass_center), divisions, compass_rotation
        )
        
        values = list(direction_counts.values())
        if divisions > 0 and values:
            total = sum(values)
            avg = total / divisions
            max_line = (avg + max(values)) / 2
            min_line = (avg + min(values)) / 2
        else:
            avg, max_line, min_line = 0, 0, 0

        color_map = {}

        if divisions == 8:
            color_map = { "N": "blue", "NE": "blue", "E": "green", "SE": "red", "S": "red", "SW": "yellow", "W": "grey", "NW": "grey" }
        elif divisions == 16:
            for d in direction_counts:
                if d in ["NNW", "N", "NNE", "NE"]: color_map[d] = "blue"
                elif d in ["ENE", "E", "ESE"]: color_map[d] = "green"
                elif d in ["SE", "SSE", "S"]: color_map[d] = "red"
                elif d in ["SW", "SSW"]: color_map[d] = "yellow"
                else: color_map[d] = "grey"
        elif divisions == 32:
            for d in direction_counts:
                if d in ["N5", "N6", "N7", "N8", "E1", "N2", "N3", "N4"]: color_map[d] = "blue"
                elif d in ["E2", "E3", "E4", "E5", "E6", "E7"]: color_map[d] = "green"
                elif d in ["E8", "S1", "S2", "S3", "S4", "S5"]: color_map[d] = "red"
                elif d in ["S6", "S7", "S8", "W1"]: color_map[d] = "yellow"
                else: color_map[d] = "grey"

        bar_colors = [color_map.get(k, "black") for k in direction_counts.keys()]


        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(direction_counts.keys(), direction_counts.values(), color=bar_colors)
        ax.axhline(avg, color='red', linestyle='--', label='AVG AREA')
        ax.axhline(max_line, color='purple', linestyle='--', label='MAX LINE')
        ax.axhline(min_line, color='green', linestyle='--', label='MIN LINE')
        ax.set_title(f"Zone-wise Area Distribution ({divisions} Parts)")
        ax.set_xlabel("Zone")
        ax.set_ylabel("Area (sq units)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        graph_buffer = io.BytesIO()
        plt.savefig(graph_buffer, format='PNG')
        graph_buffer.seek(0)
        plt.close(fig)
        return graph_buffer
    except Exception as e:
        print(f"Error generating graph for {divisions} divisions: {e}")
        return None

# def download_word_blueprint(request, project_id):
#     try:
#         data = {}
#         compass_degree = 'N/A'
#         degree_north = 'N/A'
#         degree_east = 'N/A'
#         degree_south = 'N/A'
#         degree_west = 'N/A'
#         if request.body:
#             try:
#                 data = json.loads(request.body)
#                 value = data.get('compass_degree')
#                 degree_north = data.get('degree_north', 'N/A')
#                 degree_east = data.get('degree_east', 'N/A')
#                 degree_south = data.get('degree_south', 'N/A')
#                 degree_west = data.get('degree_west', 'N/A')
#                 if value is not None and str(value).strip():
#                     compass_degree = value
#             except json.JSONDecodeError:
#                 print("No valid JSON in request body. Using defaults.")
        
#         project = get_object_or_404(Project, pk=project_id)
        
#         user_name = request.user.username
#         user_email = request.user.email

#         document = Document()
        
#         document.add_heading('User and Project Details', level=1)

#         user_table = document.add_table(rows=2, cols=2)
#         user_table.style = 'Table Grid'
#         user_table.cell(0, 0).text = 'Username'
#         user_table.cell(0, 1).text = user_name
#         user_table.cell(1, 0).text = 'Email'
#         user_table.cell(1, 1).text = user_email
      
#         for row in user_table.rows:
#             row.cells[0].paragraphs[0].runs[0].font.bold = True
        
#         document.add_paragraph() 

#         project_table = document.add_table(rows=4, cols=2)
#         project_table.style = 'Table Grid'
#         project_table.cell(0, 0).text = 'Project Name'
#         project_table.cell(0, 1).text = project.name
#         project_table.cell(1, 0).text = 'Description'
#         project_table.cell(1, 1).text = project.description
#         project_table.cell(2, 0).text = 'Category'
#         project_table.cell(2, 1).text = project.category
#         project_table.cell(3, 0).text = 'Status'
#         project_table.cell(3, 1).text = project.status
      
#         for row in project_table.rows:
#             row.cells[0].paragraphs[0].runs[0].font.bold = True
        
#         document.add_page_break()

#         document.add_heading('Blueprint Analysis Report', level=1)   

#         # Fetch session data
#         compass_rotation = request.session.get("compass_rotation", 0)
#         grid_points = request.session.get("grid_points", [])
#         compass_center = request.session.get("compass_center", [0, 0])

#         def add_image_to_doc(doc, heading, image_field, add_page_break_after=True):
#             doc.add_heading(heading, level=2)
#             if image_field and hasattr(image_field, 'path'):
#                 try:
#                     doc.add_picture(image_field.path, width=Inches(6.0))
#                 except Exception:
#                     doc.add_paragraph(f"Image file not found or is invalid.")
#             else:
#                 doc.add_paragraph("Image not available.")
            
#             if add_page_break_after:
#                 doc.add_page_break()

#         add_image_to_doc(document, 'Original Blueprint', project.blueprint)
#         add_image_to_doc(document, 'Centroid Calculated Image', project.centroid_image)

#         add_image_to_doc(document, 'Compass Set Image', project.compass_image, add_page_break_after=False)
#         document.add_paragraph()
#         compass_table = document.add_table(rows=1, cols=2)
#         compass_table.style = 'Table Grid'
        
#         hdr_cells = compass_table.rows[0].cells
#         hdr_cells[0].text = 'Direction'
#         hdr_cells[1].text = 'Stopped At Degree'
        
#         for cell in hdr_cells:
#             cell.paragraphs[0].runs[0].font.bold = True
        
#         row_cells = compass_table.add_row().cells
#         row_cells[0].text = "North"
#         row_cells[1].text = f"{degree_north}°"
#         document.add_page_break()
        
#         # --- 8 Parts ---
#         add_image_to_doc(document, 'Image Divided into 8 Parts', project.divided_8_image, add_page_break_after=False)
#         graph8 = generate_graph_image(grid_points, compass_center, 8, compass_rotation)
#         if graph8:
#             document.add_paragraph("Graph for 8 Parts:")
#             document.add_picture(graph8, width=Inches(6.0))
#         document.add_page_break()

#         # --- 16 Parts ---
#         add_image_to_doc(document, 'Image Divided into 16 Parts', project.divided_16_image, add_page_break_after=False)
#         graph16 = generate_graph_image(grid_points, compass_center, 16, compass_rotation)
#         if graph16:
#             document.add_paragraph("Graph for 16 Parts:")
#             document.add_picture(graph16, width=Inches(6.0))
#         document.add_page_break()

#         # --- 32 Parts (અહીં છેલ્લો પેજ બ્રેક નહીં આવે) ---
#         add_image_to_doc(document, 'Image Divided into 32 Parts', project.divided_32_image, add_page_break_after=False)
#         graph32 = generate_graph_image(grid_points, compass_center, 32, compass_rotation)
#         if graph32:
#             document.add_paragraph("Graph for 32 Parts:")
#             document.add_picture(graph32, width=Inches(6.0))

#         # Save Word file in memory
#         doc_io = io.BytesIO()
#         document.save(doc_io)
#         doc_io.seek(0)

#         response = HttpResponse(
#             doc_io.read(),
#             content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
#         )
#         response['Content-Disposition'] = f'attachment; filename="analysis_{project.id}.docx"'
#         return response

#     except Exception as e:
#         print("ERROR IN WORD GENERATION:")
#         print(traceback.format_exc())
#         return HttpResponse(f"<h1>An Error Occurred</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>", status=500)

#new function-----------------------------------------------------------------------------------
def download_word_blueprint(request, project_id):
    try:
        # ---------- read payload (degrees) ----------
        data = {}
        compass_degree = 'N/A'
        degree_north = degree_east = degree_south = degree_west = 'N/A'

        if request.body:
            try:
                data = json.loads(request.body)
                value = data.get('compass_degree')
                degree_north = data.get('degree_north', 'N/A')
                degree_east  = data.get('degree_east',  'N/A')
                degree_south = data.get('degree_south', 'N/A')
                degree_west  = data.get('degree_west',  'N/A')
                if value is not None and str(value).strip():
                    compass_degree = value
            except json.JSONDecodeError:
                pass

        project = get_object_or_404(Project, pk=project_id)
        user_name = request.user.username

        # ---------- doc start ----------
        document = Document()

        # ---------- Custom styles ----------
        styles = document.styles
        if 'CustomHeading1' not in [s.name for s in styles]:
            h = styles.add_style('CustomHeading1', WD_STYLE_TYPE.PARAGRAPH)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after  = Pt(12)
            h.paragraph_format.alignment    = WD_ALIGN_PARAGRAPH.CENTER
            h.font.name = 'Arial Black'
            h.font.size = Pt(28)
            h.font.bold = True
            h.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

        if 'CustomNormal' not in [s.name for s in styles]:
            n = styles.add_style('CustomNormal', WD_STYLE_TYPE.PARAGRAPH)
            n.paragraph_format.space_before = Pt(6)
            n.paragraph_format.space_after  = Pt(6)
            n.font.name = 'Calibri'
            n.font.size = Pt(12)
            n.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

        # ---------- page setup ----------
        section = document.sections[0]
        section.page_width  = Inches(8.5)
        section.page_height = Inches(11)
        section.left_margin   = Inches(0.7)
        section.right_margin  = Inches(0.7)
        section.top_margin    = Inches(0.7)
        section.bottom_margin = Inches(0.7)

        # ---------- border for all pages ----------
        sectPr = section._sectPr
        pgBorders = OxmlElement('w:pgBorders')
        for border_name in ['top', 'left', 'bottom', 'right']:
            border_el = OxmlElement(f"w:{border_name}")
            border_el.set(qn('w:val'), 'single')
            border_el.set(qn('w:sz'), '12')   # thickness
            border_el.set(qn('w:space'), '24')
            border_el.set(qn('w:color'), '4F81BD')  # blue border
            pgBorders.append(border_el)
        sectPr.append(pgBorders)

        # ---------- footer with pagination ----------
        footer = section.footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Page ")
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        instrText = OxmlElement('w:instrText')
        instrText.text = "PAGE"
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)
        run.add_text(" of ")
        fldChar3 = OxmlElement('w:fldChar')
        fldChar3.set(qn('w:fldCharType'), 'begin')
        instrText2 = OxmlElement('w:instrText')
        instrText2.text = "NUMPAGES"
        fldChar4 = OxmlElement('w:fldChar')
        fldChar4.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar3)
        run._r.append(instrText2)
        run._r.append(fldChar4)

        # ---------- COVER PAGE ----------
        document.add_paragraph("Blueprint Analysis Report", style='CustomHeading1')

        title = document.add_paragraph(project.name)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if title.runs:
            title.runs[0].font.size = Pt(34)
            title.runs[0].font.bold = True
            title.runs[0].font.color.rgb = RGBColor(0x2F, 0x54, 0x96)

        document.add_paragraph(f"Prepared for: {user_name}", style='CustomNormal')
        document.add_paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", style='CustomNormal')

        document.add_paragraph()
        subhead = document.add_paragraph("Project Details")
        subhead.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if subhead.runs:
            subhead.runs[0].font.bold = True
            subhead.runs[0].font.size = Pt(14)

        document.add_paragraph(f"Project Name: {project.name}", style='CustomNormal')
        document.add_paragraph(f"Description: {project.description}", style='CustomNormal')
        document.add_paragraph(f"Category: {project.category}", style='CustomNormal')
        document.add_paragraph(f"Status: {project.status}", style='CustomNormal')

        document.add_page_break()

        # ---------- session data ----------
        compass_rotation = request.session.get("compass_rotation", 0)
        grid_points      = request.session.get("grid_points", [])
        compass_center   = request.session.get("compass_center", [0, 0])

        # ---------- image helper ----------
        def add_image_to_doc(doc, heading, image_field, add_page_break_after=True):
            doc.add_heading(heading, level=2)
            if image_field and hasattr(image_field, 'path'):
                try:
                    doc.add_picture(image_field.path, width=Inches(6.5))  # bigger image
                except Exception:
                    doc.add_paragraph("Image file not found or is invalid.")
            else:
                doc.add_paragraph("Image not available.")
            if add_page_break_after:
                doc.add_page_break()

        # blueprint, centroid, compass images
        add_image_to_doc(document, 'Original Blueprint',        project.blueprint)
        add_image_to_doc(document, 'Centroid Calculated Image', project.centroid_image)
        add_image_to_doc(document, 'Compass Set Image', project.compass_image, add_page_break_after=False)
        document.add_paragraph()

        # ---------- styled compass table ----------
        compass_table = document.add_table(rows=1, cols=2)
        compass_table.style = "Light Shading Accent 1"
        hdr = compass_table.rows[0].cells
        hdr[0].text = 'Direction'
        hdr[1].text = 'Stopped At Degree'
        for c in hdr:
            for r in c.paragraphs[0].runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        row = compass_table.add_row().cells
        row[0].text = "North"; row[1].text = f"{degree_north}°"
        for r in row[0].paragraphs[0].runs:
            r.font.bold = True

        document.add_page_break()

        # ---------- 8 / 16 / 32 parts ----------
        add_image_to_doc(document, 'Image Divided into 8 Parts',  project.divided_8_image,  add_page_break_after=False)
        document.add_page_break()
        graph8 = generate_graph_image(grid_points, compass_center, 8, compass_rotation)
        if graph8:
            document.add_paragraph("Graph for 8 Parts:")
            document.add_picture(graph8, width=Inches(6.5))
        document.add_page_break()

        add_image_to_doc(document, 'Image Divided into 16 Parts', project.divided_16_image, add_page_break_after=False)
        document.add_page_break()
        graph16 = generate_graph_image(grid_points, compass_center, 16, compass_rotation)
        if graph16:
            document.add_paragraph("Graph for 16 Parts:")
            document.add_picture(graph16, width=Inches(6.5))
        document.add_page_break()

        add_image_to_doc(document, 'Image Divided into 32 Parts', project.divided_32_image, add_page_break_after=False)
        document.add_page_break()
        graph32 = generate_graph_image(grid_points, compass_center, 32, compass_rotation)
        if graph32:
            document.add_paragraph("Graph for 32 Parts:")
            document.add_picture(graph32, width=Inches(6.5))

        # ---------- return .docx ----------
        doc_io = io.BytesIO()
        document.save(doc_io)
        doc_io.seek(0)
        resp = HttpResponse(
            doc_io.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        resp['Content-Disposition'] = f'attachment; filename="analysis_{project.id}.docx"'
        return resp

    except Exception as e:
        print("ERROR IN WORD GENERATION:")
        print(traceback.format_exc())
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'error': str(e)}, status=500)
        return HttpResponse(f"<h1>An Error Occurred</h1><p>{e}</p>", status=500)





@login_required
def ajax_load_projects(request):
    # get projects of logged in users only
    projects = Project.objects.filter(user=request.user)

    # 1. search by name
    search_term = request.GET.get('search', '').strip()
    if search_term:
        projects = projects.filter(name__icontains=search_term)

    # 2. filter by status & category
    status = request.GET.get('status', '')
    if status:
        projects = projects.filter(status=status)

    category = request.GET.get('category', '')
    if category:
        projects = projects.filter(category=category)

    # 3. sorting
    sort_by = request.GET.get('sort', 'date_new')
    if sort_by == 'date_new':
        projects = projects.order_by('-created_at') # 'created_at' model field
    elif sort_by == 'date_old':
        projects = projects.order_by('created_at')
    elif sort_by == 'name_asc':
        projects = projects.order_by('name')
    elif sort_by == 'name_desc':
        projects = projects.order_by('-name')
    project_list = list(projects.values('id', 'name', 'description', 'status', 'category'))
    
    return JsonResponse({'projects': project_list})


@login_required
def ajax_delete_projects(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_ids = data.get('project_ids', [])

            if not project_ids:
                return JsonResponse({'status': 'error', 'message': 'No project IDs provided'}, status=400)

            projects_to_delete = Project.objects.filter(user=request.user, id__in=project_ids)
            count = projects_to_delete.count()
            projects_to_delete.delete()

            return JsonResponse({'status': 'success', 'message': f'{count} projects deleted successfully.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def logout_view(request):
    logout(request)
    request.session.flush()  
    return redirect('login')

@csrf_exempt
def analyze_grid(request):
    if request.method == "POST":
        data = json.loads(request.body)

        grid_points = data.get("grid_data", [])
        center = data.get("compass_center", [0, 0])
        divisions = int(data.get("divisions", 8))
        compass_rotation = float(data.get("compass_rotation", 0))

        # Save to session for later (download)
        request.session["grid_points"] = grid_points
        request.session["compass_center"] = center
        request.session["divisions"] = divisions  # ✅ Store this
        request.session["compass_rotation"] = compass_rotation


        direction_counts = calculate_directional_areas(
            [tuple(p) for p in grid_points],
            tuple(center),
            divisions,
            compass_rotation
        )

        # logging
        print("\n🔍 Direction-wise Block Counts:")
        for k, v in direction_counts.items():
            print(f"{k}: {v}")

        return JsonResponse(direction_counts)


# admin page
# ✅ Static admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin11'

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session['admin_logged_in'] = True
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'admin_login.html')

def admin_dashboard(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')

    # Subquery to get project_limit from UserProfile for each user
    project_limit_subquery = UserProfile.objects.filter(user=OuterRef('pk')).values('project_limit')[:1]

    # Annotate each user with their project_count and project_limit
    users = User.objects.annotate(
        project_count=Count('project'),
        project_limit=Subquery(project_limit_subquery)
    )

    # projects = Project.object.select_related('user')
    total_users = users.count()
    

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'total_users': total_users
    })


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')

@csrf_exempt
def delete_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            user.delete()
        except Users.DoesNotExist:
            pass
    return redirect('admin_dashboard')

# def admin_dashboard(request):
#     users = User.objects.annotate(project_count=Count('project'))  # 'project' is the related_name or lowercase model name if not set
#     total_users = users.count()
#     total_experts = User.objects.filter(is_staff=True).count()
#     monthly_visitors = 1500  # Dummy or real stat if available

#     return render(request, 'admin_dashboard.html', {
#         'users': users,
#         'total_users': total_users,
#         'total_experts': total_experts,
#         'monthly_visitors': monthly_visitors
#     })