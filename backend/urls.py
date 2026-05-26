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
from apps.rules.views import RuleViewSet, CertaintyFactorViewSet, DatasetRowViewSet, TrainSystemView, CertaintyFactorMatrixView
from apps.experts.views import HealthExpertViewSet
from apps.consultations.views import ConsultationViewSet, StatisticsView, TestimonialListCreateView, ChatView, ChatContactsView
from apps.authentication.views import RegisterView, ProfileView, AdminUserListView

router = DefaultRouter()
router.register(r'symptoms', SymptomViewSet)
router.register(r'diseases', DiseaseViewSet)
router.register(r'rules/dataset', DatasetRowViewSet, basename='datasetrow')
router.register(r'rules', RuleViewSet)
router.register(r'certainty-factors', CertaintyFactorViewSet)
router.register(r'experts', HealthExpertViewSet)
router.register(r'consultations', ConsultationViewSet, basename='consultation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/statistics/', StatisticsView.as_view(), name='statistics'),
    path('api/testimonials/', TestimonialListCreateView.as_view(), name='testimonials'),
    
    # Admin Custom API
    path('api/admin/users/', AdminUserListView.as_view(), name='admin_users'),
    
    # Chat API
    path('api/chats/', ChatView.as_view(), name='chats'),
    path('api/chats/contacts/', ChatContactsView.as_view(), name='chat_contacts'),
    
    # Rules / Train API
    path('api/rules/train/', TrainSystemView.as_view(), name='rules_train'),
    path('api/rules/matrix/', CertaintyFactorMatrixView.as_view(), name='rules_matrix'),
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='auth_profile'),
    
    # Router catch-all (placed last to prevent conflicts with specific routes)
    path('api/', include(router.urls)),
]

# Serve media files in development
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
