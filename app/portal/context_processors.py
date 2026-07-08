from django.conf import settings


def environment(request):
    return {
        "environment_name": settings.ENVIRONMENT_NAME,
        "application_name": settings.APPLICATION_NAME,
        "application_version": settings.APPLICATION_VERSION
    }