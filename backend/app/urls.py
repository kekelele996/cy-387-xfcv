from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from app.apps.properties.views import PropertyListView
from app.apps.booking.views import BookingCreateView
from app.apps.contract.views import ContractListView

urlpatterns = [
    path('api/properties/', PropertyListView.as_view()),
    path('api/bookings/', BookingCreateView.as_view()),
    path('api/contracts/', ContractListView.as_view()),
    path('api/', include('app.apps.repair.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
