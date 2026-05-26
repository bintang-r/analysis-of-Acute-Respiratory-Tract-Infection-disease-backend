from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.symptoms.views import SymptomViewSet
from apps.diseases.views import DiseaseViewSet
from apps.rules.views import RuleViewSet, CertaintyFactorViewSet
from apps.experts.views import HealthExpertViewSet
from apps.consultations.views import ConsultationViewSet
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
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='auth_profile'),
]
