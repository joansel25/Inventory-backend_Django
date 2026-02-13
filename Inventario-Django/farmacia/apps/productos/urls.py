

from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, PrincipioActivoViewSet, LaboratorioViewSet, 
    ProductoViewSet, UbicacionViewSet, LoteViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'principios-activos', PrincipioActivoViewSet)
router.register(r'laboratorios', LaboratorioViewSet)
router.register(r'ubicaciones', UbicacionViewSet, basename='ubicacion')
router.register(r'lotes', LoteViewSet, basename='lote')
router.register(r'', ProductoViewSet, basename='producto')

urlpatterns = router.urls