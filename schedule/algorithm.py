from dataclasses import dataclass
import random

DAYS = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
HOURS_PER_DAY = 8
LAB_COURSES = {'Programlama', 'Kimya'}


@dataclass
class TeacherData:
    name: str
    course: list[str]
    off_day: str


@dataclass
class RoomData:
    name: str
    room_type: str


@dataclass
class CourseRequirement:
    classroom: str
    weekly_hours: int
    course: str


@dataclass
class ScheduleEntry:
    classroom: str
    course: str
    teacher: str
    room: str


def empty_schedule():
    return {
        day: {
            hour: [] for hour in range(1, HOURS_PER_DAY + 1)
        }
        for day in DAYS
    }


def is_lab_course(course_name):
    return course_name in LAB_COURSES


def find_teacher(course_name, teachers):
    for teacher in teachers:
        if course_name in teacher.course:
            return teacher
    return None


def teacher_available(teacher_name, schedule, day, hour):
    for entry in schedule[day][hour]:
        if entry.teacher == teacher_name:
            return False
    return True


def room_available(room_name, schedule, day, hour):
    for entry in schedule[day][hour]:
        if entry.room == room_name:
            return False
    return True


def classroom_available(classroom_name, schedule, day, hour):
    for entry in schedule[day][hour]:
        if entry.classroom == classroom_name:
            return False
    return True


def is_teacher_off_day(off_day, day):
    return off_day == day


def find_free_room(rooms, schedule, day, hour, room_type):
    for room in rooms:
        if room.room_type == room_type:
            if room_available(room.name, schedule, day, hour):
                return room
    return None


def check_teacher_assignment(schedule, day, hour, classroom, course, teacher):
    for entry in schedule[day][hour]:
        if entry.classroom == classroom and entry.course == course and entry.teacher != teacher:
            return False

    return True


def can_place(schedule, day, hour, req, teacher, rooms):
    if is_teacher_off_day(teacher.off_day, day):
        return None

    if not teacher_available(teacher.name, schedule, day, hour):
        return None

    if not classroom_available(req.classroom, schedule, day, hour):
        return None

    if not check_teacher_assignment(schedule, day, hour, req.classroom, req.course, teacher.name):
        return None

    room_type = "lab" if is_lab_course(req.course) else "normal"
    room = find_free_room(rooms, schedule, day, hour, room_type)

    if room is None:
        return None

    return room


def solve(teachers, reqs, rooms, max_solutions=5):
    solutions = []
    count = 0
    while count <=  5:
        rng = random.Random()
        schedule = empty_schedule()
        soft_violations = 0
        hard_violations = 0
        missing = []

        req_order = list(reqs)
        rng.shuffle(req_order)

        for req in req_order:
            teacher = find_teacher(req.course, teachers)
            if teacher is None:
                missing.append(
                    f"{req.classroom} - {req.course}: öğretmen bulunamadı")
                hard_violations += 1
                continue

            placed = 0
            day_order = DAYS[:]
            rng.shuffle(day_order)

            for day in day_order:
                if placed >= req.weekly_hours:
                    break

                hour_order = list(range(1, HOURS_PER_DAY + 1))
                rng.shuffle(hour_order)

                for hour in hour_order:
                    if placed >= req.weekly_hours:
                        break

                    room = can_place(schedule, day, hour, req, teacher, rooms)
                    if room is not None:
                        schedule[day][hour].append(
                            ScheduleEntry(req.classroom, req.course,
                                          teacher.name, room.name)
                        )

                        placed += 1

            if placed < req.weekly_hours:
                missing.append(
                    f"{req.classroom} - {req.course}: {placed}/{req.weekly_hours} saat yerleştirilebildi"
                )
                hard_violations += (req.weekly_hours - placed)
            for day in DAYS:
                if daily_course_count(schedule, day, req.classroom, req.course) > 4:
                    soft_violations += 1
                if has_gap_in_day(schedule, day, req.classroom, req.course):
                    soft_violations += 2

        is_complete = len(missing) == 0 and hard_violations == 0
        if is_complete:
            fitness = 100 - (soft_violations * 3)
        else:
            fitness = 100 - (hard_violations * 10) - (soft_violations * 3)
        fitness = max(0, fitness)
        if fitness >= 80:
            count += 1

        solutions.append({
            'schedule': schedule,
            'fitness': fitness,
            'is_complete': is_complete,
            'missing_slot': missing,
            'soft_violations': soft_violations,
            'hard_violations': hard_violations
        })

    solutions.sort(key=lambda x: x['fitness'], reverse=True)
    return solutions[:max_solutions]


def daily_course_count(schedule, day, classroom, course):
    count = 0
    for hour in range(1, HOURS_PER_DAY + 1):
        found = any(entry.classroom == classroom and entry.course == course
                    for entry in schedule[day][hour])
        if found:
            count += 1
    return count


def has_gap_in_day(schedule, day, classroom, course):
    count = 0
    this_lesson = []
    for hour in range(1, HOURS_PER_DAY + 1):
        found = any(entry.classroom == classroom and entry.course == course
                    for entry in schedule[day][hour])
        if found:
            this_lesson.append(hour)
    this_lesson.sort()

    for i in range(1, len(this_lesson)):
        if this_lesson[i] - this_lesson[i-1] > 1:
            return True
    return False
