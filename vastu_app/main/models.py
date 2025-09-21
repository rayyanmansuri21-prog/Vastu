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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'main_project'

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    project_limit = models.IntegerField(default=3)

    def __str__(self):
        return self.user.username