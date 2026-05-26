from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, BasePermission
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Rule, CertaintyFactor, DatasetRow
from .serializers import RuleSerializer, CertaintyFactorSerializer, DatasetRowSerializer
from .services import recalculate_rules_and_cf

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'admin'

class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CertaintyFactorViewSet(viewsets.ModelViewSet):
    queryset = CertaintyFactor.objects.all()
    serializer_class = CertaintyFactorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

from rest_framework.pagination import PageNumberPagination

class DatasetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class DatasetRowViewSet(viewsets.ModelViewSet):
    queryset = DatasetRow.objects.all().order_by('-id')
    serializer_class = DatasetRowSerializer
    permission_classes = [IsAdminRole]
    pagination_class = DatasetPagination

class TrainSystemView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        try:
            recalculate_rules_and_cf()
            count = DatasetRow.objects.count()
            return Response({
                'message': f'System training completed successfully based on {count} cases.',
                'dataset_count': count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CertaintyFactorMatrixView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        cfs = CertaintyFactor.objects.select_related('disease', 'symptom').all()
        matrix_data = [{
            'disease_code': cf.disease.code,
            'disease_name': cf.disease.name,
            'symptom_code': cf.symptom.code,
            'symptom_name': cf.symptom.name,
            'expert_cf': cf.expert_cf
        } for cf in cfs]
        
        rules = Rule.objects.select_related('disease').all()
        rules_data = []
        for r in rules:
            s_list = [rs.symptom.name for rs in r.rule_symptoms.select_related('symptom').all()]
            rules_data.append({
                'code': r.code,
                'disease_name': r.disease.name,
                'symptoms': s_list
            })
            
        return Response({
            'matrix': matrix_data,
            'rules': rules_data
        }, status=status.HTTP_200_OK)
