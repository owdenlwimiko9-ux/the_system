from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView
from accounts.views import RoleBasedLoginView # <-- import our custom view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # AUTH - CHANGED THIS LINE
    path('', RoleBasedLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # APPS
    path('', RedirectView.as_view(url='/dashboard/')),
    path('dashboard/', include('dashboard.urls')),  # main_dashboard.html
    path('students/', include('students.urls')),
    path('academics/', include('academics.urls')),
    path('finance/', include('finance.urls')),
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)