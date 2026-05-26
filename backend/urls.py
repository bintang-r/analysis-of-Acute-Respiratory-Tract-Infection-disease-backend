# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include
# pyrefly: ignore [missing-import]
from rest_framework.routers import DefaultRouter
# pyrefly: ignore [missing-import]
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.symptoms.views import SymptomViewSet
from apps.diseases.views import DiseaseViewSet
from apps.rules.views import RuleViewSet, CertaintyFactorViewSet
from apps.experts.views import HealthExpertViewSet
from apps.consultations.views import ConsultationViewSet, StatisticsView, TestimonialListCreateView
from apps.authentication.views import RegisterView, ProfileView

router = DefaultRouter()
router.register(r'symptoms', SymptomViewSet)
router.register(r'diseases', DiseaseViewSet)
router.register(r'rules', RuleViewSet)
router.register(r'certainty-factors', CertaintyFactorViewSet)
router.register(r'experts', HealthExpertViewSet)
router.register(r'consultations', ConsultationViewSet, basename='consultation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/statistics/', StatisticsView.as_view(), name='statistics'),
    path('api/testimonials/', TestimonialListCreateView.as_view(), name='testimonials'),
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='auth_profile'),
]

# Serve media files in development
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
