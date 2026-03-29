from .models import Teacher,Room, CourseRequirement
from rest_framework import serializers 

class TeacherSerializer(serializers.ModelSerializer):
     class Meta:
          model = Teacher
          fields= '__all__'
          
class RoomSerializer(serializers.ModelSerializer):
     class Meta:
          model = Room
          fields = '__all__'
          
class CourseSerializer(serializers.ModelSerializer):
     class Meta:
          model = CourseRequirement
          fields = '__all__'
          
