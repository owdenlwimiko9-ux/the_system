from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from accounts.views import RoleBasedLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. PUBLIC WEBSITE - This must be FIRST at root /
    path('', include('website.urls')),
    
    # 2. AUTH - Move login to /login/ not /
    path('login/', RoleBasedLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # 3. PRIVATE SYSTEM APPS
    path('dashboard/', include('dashboard.urls')),
    path('students/', include('students.urls')),
    path('academics/', include('academics.urls')),
    path('finance/', include('finance.urls')),
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)