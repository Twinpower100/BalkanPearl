"""context_processors.py"""
from .models import SiteImage

def site_image(request):
    return {
        'site_image': SiteImage.objects.first()
    }