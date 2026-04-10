from django.urls import path, include
from .views import ScheduleView
from .views import TeacherView, RoomView, CourseView, ScheduleEntryView, RequirementView, ClassroomView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('teachers', TeacherView)
router.register('rooms', RoomView)
router.register('courses', CourseView)
router.register('requirements', RequirementView)
router.register('schedule', ScheduleEntryView)
router.register('classrooms', ClassroomView)

urlpatterns = [
    path('', include(router.urls)),
    path('generate-schedule/', ScheduleView.as_view()),
]
