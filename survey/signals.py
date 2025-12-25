from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Company, UserProfile

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if not hasattr(instance, 'userprofile'):
        company, _ = Company.objects.get_or_create(
            name=f"{instance.username}'s Company",
            industry="General"
        )
        UserProfile.objects.create(user=instance, company=company)
