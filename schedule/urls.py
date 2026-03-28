from django.urls import path
from .views import ScheduleView

urlpatterns = [
     path('generate-schedule/', ScheduleView.as_view(), name='generate-schedule'),
]