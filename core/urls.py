from django.contrib import admin
from django.urls import path
from core.views import home, upload_resume, signup_view, chat_bot_view  # ✅ Import chatbot view
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('upload/', upload_resume, name='upload_resume'),
    path('signup/', signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('chat/', chat_bot_view, name='chat_bot'),  # ✅ Add this line
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
