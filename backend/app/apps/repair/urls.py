from django.urls import path

from .views import (
    ServerTimeView,
    StaffListView,
    TicketAcceptView,
    TicketCompleteView,
    TicketDetailView,
    TicketEscalateScanView,
    TicketEscalateView,
    TicketListCreateView,
)

urlpatterns = [
    path('repair/time/', ServerTimeView.as_view()),
    path('repair/staff/', StaffListView.as_view()),
    path('repair/tickets/escalate-overdue/', TicketEscalateScanView.as_view()),
    path('repair/tickets/', TicketListCreateView.as_view()),
    path('repair/tickets/<int:ticket_id>/', TicketDetailView.as_view()),
    path('repair/tickets/<int:ticket_id>/accept/', TicketAcceptView.as_view()),
    path('repair/tickets/<int:ticket_id>/complete/', TicketCompleteView.as_view()),
    path('repair/tickets/<int:ticket_id>/escalate/', TicketEscalateView.as_view()),
]
