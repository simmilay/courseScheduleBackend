from django.urls import path, include
from .views import ScheduleView
from .views import TeacherView, RoomView, CourseView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('teachers', TeacherView)
router.register('rooms', RoomView)
router.register('requirements', CourseView)

urlpatterns = [
    path('', include(router.urls)),
    path('generate-schedule/', ScheduleView.as_view()),
]