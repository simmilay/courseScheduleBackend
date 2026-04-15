from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view
from .algorithm import solve
from .models import Teacher, Room, CourseRequirement, ScheduleEntry, Course, Classroom
from .serializers import TeacherSerializer, RoomSerializer, CourseSerializer, ScheduleSerializer, RequirementsSerializer, ClassroomSerializer

# Create your views here.


class ScheduleView(APIView):
    def post(self, request):

        solved_schedule = solve()
        if solved_schedule is None:
            return Response({'message': 'No schedule found'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(solved_schedule, status=status.HTTP_200_OK)


class TeacherView(ModelViewSet):
    queryset = Teacher.objects.filter(is_active=True).order_by('name')
    serializer_class = TeacherSerializer

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        teacher = self.get_object()
        courses = teacher.course.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='off-day-choices')
    def off_day_choices(self, request):
        return Response({
            'off_days': [
                {'value': value, 'title': title}
                for value, title in Teacher.OffDay.choices
            ]
        })


class RoomView(ModelViewSet):
    queryset = Room.objects.filter(is_active=True).order_by('room_type', 'name')
    serializer_class = RoomSerializer

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        self.queryset = Room.objects.filter(is_active=True)
        room_type = self.request.query_params.get('room_type')
        if room_type is not None:
            self.queryset = self.queryset.filter(room_type=room_type)
        return self.queryset


class CourseView(ModelViewSet):
    queryset = Course.objects.filter(is_active=True).order_by('name')
    serializer_class = CourseSerializer

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RequirementView(ModelViewSet):
    queryset = CourseRequirement.objects.filter(
        is_active=True).order_by('classroom__name')
    serializer_class = RequirementsSerializer

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ScheduleEntryView(ModelViewSet):
    queryset = ScheduleEntry.objects.filter(is_active=True)
    serializer_class = ScheduleSerializer


class ClassroomView(ModelViewSet):
    queryset = Classroom.objects.filter(is_active=True).order_by('name')
    serializer_class = ClassroomSerializer

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
