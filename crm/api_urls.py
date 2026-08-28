from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, SupplierViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"suppliers", SupplierViewSet)

urlpatterns = router.urls
