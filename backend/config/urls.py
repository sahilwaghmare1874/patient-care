from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.views.static import serve

def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'patientcare-backend'})

def serve_frontend(request, path=''):
    frontend_dir = (settings.BASE_DIR.parent / 'frontend').resolve()
    if not path or path == '/':
        path = 'index.html'
    target = (frontend_dir / path).resolve()
    if str(target).startswith(str(frontend_dir)) and target.is_file():
        return FileResponse(open(target, 'rb'))
    raise Http404("Page not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/auth/', include('accounts.urls')),
    path('api/patients/', include('patients.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/pathology/', include('pathology.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    path('api/government/', include('government.urls')),
    path('api/insurance/', include('insurance.urls')),
    path('api/funds/', include('funds.urls')),
    path('api/health-protection/', include('funds.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/notifications/', include('notifications.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^(?P<path>(pages/|css/|js/|images/|assets/|index\.html).*)$', serve_frontend, name='frontend_assets'),
    path('', serve_frontend, name='frontend_root'),
]
