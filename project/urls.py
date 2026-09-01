from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def redirect_to_admin(request):
    return redirect('/admin/')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path("", redirect_to_admin),

  
    path('api/',include("apps.user.urls")),
    path('api/',include("apps.nclex.urls")),

    path('api/', include("apps.new_nclex.urls")),

    path('api/',include("apps.flashcard.urls")),

    path('api/', include("apps.sub.urls")),
    path('api/', include("apps.core_learning.urls")),
    path('api/', include("apps.notification.urls")),
    path('api/', include("apps.ecg_mastery.urls")),
    path('api/', include("apps.faq.urls")),
    path('api/', include("apps.my_lession.urls")),
    path('api/', include("apps.procedure_lockup.urls")),
    path('api/', include("apps.notes_flashcard.urls")),
    path('api/', include("apps.my_tutor.urls")),
    path('api/', include("apps.concept_map.urls")),
    path('api/', include("apps.drugcards.urls")),
    path('api/', include("apps.careplans.urls")),
    path('api/', include("apps.cms.urls")),

    path("ckeditor5/", include("django_ckeditor_5.urls")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



