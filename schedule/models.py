from django.db import models

# Create your models here.


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    off_day = models.CharField(max_length=100)
    
    def __str__(self):
         return f"{self.name} - {self.course} - {self.off_day}"

class Room(models.Model):
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100)
    
    def __str__(self):
         return f"{self.name} - {self.room_type}"


class CourseRequirement(models.Model):
    classroom = models.CharField(max_length=100)
    weekly_hours = models.IntegerField()
    course = models.CharField(max_length=100)
    
    def __str__(self):
         return f"{self.classroom} - {self.weekly_hours} - {self.course}"


class ScheduleEntry(models.Model):
    classroom = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    teacher = models.CharField(max_length=100)
    room = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.classroom} - {self.course} - {self.teacher} - {self.room}"