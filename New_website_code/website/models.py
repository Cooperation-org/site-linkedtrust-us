from django.db import models
from django.utils.text import Truncator

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='team/')
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Hourly rate in USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def truncated_description(self):
        return Truncator(self.description).words(15, truncate='...')

    def formatted_hourly_rate(self):
        return int(self.hourly_rate)

    def __str__(self):
        return self.name