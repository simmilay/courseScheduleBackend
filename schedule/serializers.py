from .models import Teacher, Room, CourseRequirement, ScheduleEntry, Course, Classroom
from rest_framework import serializers


class TeacherSerializer(serializers.ModelSerializer):
    course_names = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = '__all__'

    def get_course_names(self, obj):
        return list(obj.course.values_list('name', flat=True))




class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class RequirementsSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(
        source='classroom.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = CourseRequirement
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    allowed_rooms_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_allowed_rooms_name(self, obj):
        return list(obj.allowed_rooms.values_list('name', flat=True))


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'
