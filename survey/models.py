from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    CATEGORY_CHOICES = [
        ('PR', 'Pricing & Revenue'),
        ('PC', 'Procurement & COGS'),
        ('OP', 'Operational Productivity'),
        ('WC', 'Working Capital'),
        ('SGA', 'SG&A'),
    ]

    text = models.CharField(max_length=500)
    category = models.CharField(max_length=5, choices=CATEGORY_CHOICES)
    ideal_index = models.IntegerField()  # 0–3

    def __str__(self):
        return self.text



class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        related_name='choices',
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    index = models.IntegerField()  # 0–3

    def __str__(self):
        return f"{self.text} ({self.index})"

class Company(models.Model):
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"

class SurveyResponse(models.Model):
    session_id = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    is_submitted = models.BooleanField(default=False)

#class IndustryBenchmark(models.Model):
   # industry = models.CharField(max_length=100)
    #category = models.CharField(max_length=10)
    #avg_score = models.FloatField()

# force_migration_refresh

from django.contrib.auth.models import User

def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "company": Company.objects.create(
                name=f"{user.username} Company",
                industry="General"
            )
        }
    )
    return profile
