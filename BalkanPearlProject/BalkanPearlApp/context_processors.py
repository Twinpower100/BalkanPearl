from .models import SiteImage

def site_image(request):
    image = SiteImage.objects.first()  # Берём первое изображение
    return {'site_image': image}