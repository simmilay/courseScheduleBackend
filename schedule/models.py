from django.db import models
from core.models import BaseModel

# Create your models here.


class Teacher(BaseModel):
    class OffDay(models.TextChoices):
        PAZARTESI = 'Pazartesi', 'Pazartesi'
        SALI = 'Sali', 'Salı'
        CARSAMBA = 'Carsamba', 'Çarşamba'
        PERSEMBE = 'Persembe', 'Perşembe'
        CUMA = 'Cuma', 'Cuma'
    name = models.CharField(max_length=100)
    course = models.ManyToManyField("schedule.Course")
    off_day = models.CharField(max_length=100, choices=OffDay.choices)

    def __str__(self):
        return f"{self.name} - {self.course} - {self.off_day}"


class Room(BaseModel):
    class RoomType(models.TextChoices):
        NORMAL = 'Normal', 'normal'
        LAB = 'Laboratuvar', 'lab'
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.room_type}"


class Course(BaseModel):
    name = models.CharField(max_length=100)
    is_lab = models.BooleanField(default=False)
    allowed_rooms = models.ManyToManyField("schedule.Room", blank=True)

    def __str__(self):
        return f"{self.name}"


class CourseRequirement(BaseModel):
    classroom = models.ForeignKey(
        "schedule.Classroom", on_delete=models.CASCADE, null=True)
    teacher = models.ForeignKey(
        "schedule.Teacher", on_delete=models.CASCADE, null=True)
    course = models.ForeignKey("schedule.Course", on_delete=models.CASCADE)
    weekly_hours = models.IntegerField()

    def __str__(self):
        return f"{self.classroom} - {self.weekly_hours} - {self.course}"


class Classroom(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class ScheduleEntry(BaseModel):
    schedule = models.JSONField(default=list)

    def __str__(self):
        return f"{self.schedule}"
