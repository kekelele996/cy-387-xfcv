from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve
from app.apps.properties.views import PropertyListView
from app.apps.booking.views import BookingCreateView
from app.apps.contract.views import ContractListView
from app.apps.repair.views import (
    RepairAcceptView,
    RepairCompleteView,
    RepairEscalateView,
    RepairStaffListView,
    RepairTicketDetailView,
    RepairTicketListCreateView,
)

urlpatterns = [
    path('api/properties/', PropertyListView.as_view()),
    path('api/bookings/', BookingCreateView.as_view()),
    path('api/contracts/', ContractListView.as_view()),
    path('api/repairs/', RepairTicketListCreateView.as_view()),
    path('api/repairs/<int:ticket_id>/', RepairTicketDetailView.as_view()),
    path('api/repairs/<int:ticket_id>/accept/', RepairAcceptView.as_view()),
    path('api/repairs/<int:ticket_id>/escalate/', RepairEscalateView.as_view()),
    path('api/repairs/<int:ticket_id>/complete/', RepairCompleteView.as_view()),
    path('api/repair-staff/', RepairStaffListView.as_view()),
    re_path(r'^media/(?P<path>.*)$', serve, kwargs={'document_root': settings.MEDIA_ROOT}),
]
