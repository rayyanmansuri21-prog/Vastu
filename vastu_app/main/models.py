from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    STATUS_CHOICES = [
        ('Planned', 'Planned'),
        ('In Progress', 'In Progress'),
    ]

    CATEGORY_CHOICES = [
        ('Residential', 'Residential'),
        ('Commercial', 'Commercial'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    blueprint = models.ImageField(upload_to='blueprints/')
    centroid_image = models.ImageField(upload_to='project_images/', null=True, blank=True)
    compass_image = models.ImageField(upload_to='project_images/', null=True, blank=True)
    divided_8_image = models.ImageField(upload_to='project_images/', null=True, blank=True)
    divided_16_image = models.ImageField(upload_to='project_images/', null=True, blank=True)
    divided_32_image = models.ImageField(upload_to='project_images/', null=True, blank=True)

    divided_8_dxf = models.FileField(upload_to='divided_8_dxf/', blank=True, null=True)
    divided_16_dxf = models.FileField(upload_to='divided_16_dxf/', blank=True, null=True)
    divided_32_dxf = models.FileField(upload_to='divided_32_dxf/', blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'main_project'

    def __str__(self):
        return self.name

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     project_limit = models.IntegerField(default=3)
#
#     def __str__(self):
#         return self.user.username
# models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    project_limit = models.IntegerField(default=3)  # default 3 projects
    extra_projects = models.IntegerField(default=0)

    def total_limit(self):
        return self.project_limit + self.extra_projects

    def __str__(self):
        return f"{self.user.username} — limit: {self.total_limit()}"


class PaymentOrder(models.Model):
    PLAN_CHOICES = [
        ('basic', '1 Extra Project - ₹49'),
        ('standard', '2 Extra Projects - ₹299'),
        ('premium', '7 Extra Projects - ₹499'),
    ]
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.IntegerField()  # in paise (49 rupees = 4900 paise)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    extra_projects_granted = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan} - {self.status}"


 # new model for generating ai generated report
class VastuReport(models.Model):
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='vastu_report')
    vastu_score = models.IntegerField(default=0)          # 0-100
    overall_summary = models.TextField(blank=True)
    zone_analysis = models.JSONField(default=dict)        # per-direction analysis
    recommendations = models.JSONField(default=list)      # list of tips
    positive_aspects = models.JSONField(default=list)
    doshas = models.JSONField(default=list)               # Vastu defects found
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Vastu Report - {self.project} (Score: {self.vastu_score})"