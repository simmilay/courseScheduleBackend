from django.db import models
from core.models import BaseModel

# Create your models here.


class Teacher(BaseModel):
    name = models.CharField(max_length=100)
    course = models.JSONField(default=list)
    off_day = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.course} - {self.off_day}"


class Room(BaseModel):
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.room_type}"


class CourseRequirement(BaseModel):
    classroom = models.CharField(max_length=100)
    weekly_hours = models.IntegerField()
    course = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.classroom} - {self.weekly_hours} - {self.course}"


class ScheduleEntry(BaseModel):
    schedule = models.JSONField(default=list)

    def __str__(self):
        return f"{self.schedule}"
