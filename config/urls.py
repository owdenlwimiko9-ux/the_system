from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from accounts.views import RoleBasedLoginView
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. PUBLIC WEBSITE - /
    path('', include('website.urls')),
    # redirect old /academics/ public link
    path('academics/', RedirectView.as_view(url='/programs/', permanent=True)),
    
    # 2. AUTH
    path('login/', RoleBasedLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # 3. PRIVATE SYSTEM - all under school-management/
    path('school-management/', include('dashboard.urls')),
    path('school-management/students/', include('students.urls')),
    path('school-management/academics/', include('academics.urls')),
    path('school-management/finance/', include('finance.urls')),
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)