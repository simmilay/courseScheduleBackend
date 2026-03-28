from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .algorithm import TeacherData, RoomData, CourseRequirement, solve

# Create your views here.


class ScheduleView(APIView):
    def post(self, request):
        data = request.data

        teachers = [
            TeacherData(
                name=t['name'],
                course=t['course'],
                off_day=t['off_day'])
            for t in data['teachers']]

        rooms = [
            RoomData(
                name=r['name'],
                room_type=r['room_type']
            )
            for r in data['rooms']
        ]

        requirement = [
            CourseRequirement(
                classroom=cr['classroom'],
                weekly_hours=cr['weekly_hours'],
                course=cr['course']
            )
            for cr in data['requirements']
        ]

        solutions = solve(
            teachers=teachers,
            reqs=requirement,
            rooms=rooms
        )

        output = []
        for sol in solutions:
            schedule_out = {}
            for day in sol['schedule']:
                schedule_out[day] = {}
                for hour in sol['schedule'][day]:
                    schedule_out[day][str(hour)] = [
                        {
                            'classroom': e.classroom,
                            'course': e.course,
                            'teacher': e.teacher,
                            'room': e.room
                        } for e in sol['schedule'][day][hour]
                    ]
            output.append({
                'schedule': schedule_out,
                'fitness': sol['fitness'],
                'is_complete': sol['is_complete'],
                'missing_slot': sol['missing_slot'],
                'soft_violations': sol['soft_violations']
            })

        return Response(output, status=status.HTTP_200_OK)