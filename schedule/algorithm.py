import random
from ortools.sat.python import cp_model

from schedule.models import CourseRequirement, Room, Teacher


DAYS = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
HOURS_PER_DAY = 7

OFF_DAY_MAP = {
    '1': 'Pazartesi',
    '2': 'Salı',
    '3': 'Çarşamba',
    '4': 'Perşembe',
    '5': 'Cuma',
}


def build_requirements():

    requirements = {}
    teacher_load = {}

    for req in CourseRequirement.objects.filter(is_active=True, course__is_active=True, classroom__is_active=True):
        course = req.course
        classroom = req.classroom.name
        weekly_hours = req.weekly_hours

        eligible_teachers = list(
            Teacher.objects.filter(
                is_active=True, course__is_active=True, course=course)
            .values_list('name', flat=True)
        )

        if not eligible_teachers:
            print(
                f"UYARI: {classroom} - {course.name} için branşa uygun öğretmen yok, atlandı.")
            continue
        teacher = min(eligible_teachers, key=lambda t: teacher_load.get(t, 0))
        teacher_load[teacher] = teacher_load.get(teacher, 0) + weekly_hours
        

        if course.is_lab:
            rooms = list(course.allowed_rooms.values_list('name', flat=True))
        else:
            rooms = [classroom]

        if not rooms:
            print(f"UYARI: {course.name} için uygun oda bulunamadı, atlandı.")
            continue

        if classroom not in requirements:
            requirements[classroom] = []

        requirements[classroom].append(
            (course.name, teacher, rooms, weekly_hours)
        )

    return requirements


def build_teacher_off_day():
    teachers = {}
    for teacher in Teacher.objects.filter(is_active=True, course__is_active=True):
        teachers[teacher.name] = OFF_DAY_MAP.get(
            teacher.off_day, teacher.off_day)
    return teachers


def build_veriables(model, requirements):
    x = {}
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, _) in reqs:
            for room in rooms:
                for day in DAYS:
                    for hour in range(1, HOURS_PER_DAY + 1):
                        x[(classroom, course, teacher, room, day, hour)] = model.new_bool_var(
                            f'x_{classroom}_{course}_{teacher}_{room}_{day}_{hour}')
    return x


def build_schedule(self, x, requirements):
    schedule = {}
    for day in DAYS:
        schedule[day] = {}
        for hour in range(1, HOURS_PER_DAY + 1):
            schedule[day][hour] = []

    for (classroom, course, teacher, room, day, hour), var in x.items():
        if self.value(var) == 1:
            schedule[day][hour].append({
                'classroom': classroom,
                'course': course,
                'teacher': teacher,
                'room': room
            })
    return schedule


def daily_course_count(schedule, classroom, course, day):
    count = 0
    for hour in range(1, HOURS_PER_DAY + 1):
        if schedule[day][hour]:
            found = any(entry['classroom'] == classroom and entry['course'] ==
                        course for entry in schedule[day][hour])
            if found:
                count += 1
    return count


def has_gap_in_day(schedule, classroom, course, day):
    this_course = []
    for hour in range(1, HOURS_PER_DAY + 1):
        if schedule[day][hour]:
            found = any(entry['classroom'] == classroom and entry['course'] ==
                        course for entry in schedule[day][hour])
            if found:
                this_course.append(hour)

    this_course.sort()
    for i in range(1, len(this_course)):
        if this_course[i] - this_course[i - 1] > 1:
            return True
    return False


def calculate_fitness(schedule, requirements):
    soft_violation = 0
    for classroom, reqs in requirements.items():
        for (course, *_) in reqs:
            for day in DAYS:
                if daily_course_count(schedule, classroom, course, day) > 4:
                    soft_violation += 1
                if has_gap_in_day(schedule, classroom, course, day):
                    soft_violation += 1

    max_violation = sum(len(reqs)
                        for reqs in requirements.values()) * len(DAYS) * 2
    if max_violation == 0:
        return 100, 0
    fitness = max(0, 100 - int(soft_violation / max_violation * 100))
    return fitness, soft_violation


def add_weekly_hours_constraint(model, x, requirements):
    """Her (sınıf, ders, öğretmen) için haftalık toplam saat = weekly_hours"""
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, weekly_hours) in reqs:
            model.add(
                sum(
                    x[(classroom, course, teacher, room, day, hour)]
                    for day in DAYS
                    for hour in range(1, HOURS_PER_DAY + 1)
                    for room in rooms
                    if (classroom, course, teacher, room, day, hour) in x
                ) == weekly_hours
            )


def add_teacher_constraint(model, x, requirements):
    """Bir öğretmen aynı anda yalnızca bir yerde ders verebilir"""
    all_teachers = set(
        teacher
        for reqs in requirements.values()
        for (_, teacher, _, _) in reqs
    )

    for teacher in all_teachers:
        for day in DAYS:
            for hour in range(1, HOURS_PER_DAY + 1):
                model.add(
                    sum(
                        x[(classroom, course, teacher, room, day, hour)]
                        for classroom, reqs in requirements.items()
                        for (course, t, rooms, _) in reqs
                        if t == teacher
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour) in x
                    ) <= 1
                )


def add_room_constraint(model, x, requirements):
    
    all_rooms = set(
        room
        for reqs in requirements.values()
        for (_, _, rooms, _) in reqs
        for room in rooms
    )

    for room in all_rooms:
        for day in DAYS:
            for hour in range(1, HOURS_PER_DAY + 1):
                model.add(
                    sum(
                        x[(classroom, course, teacher, room, day, hour)]
                        for classroom, reqs in requirements.items()
                        for (course, teacher, rooms, _) in reqs
                        if room in rooms
                        if (classroom, course, teacher, room, day, hour) in x
                    ) <= 1
                )


def add_classroom_constraint(model, x, requirements):
    """Bir sınıfta aynı anda yalnızca bir ders yapılabilir"""
    for classroom in requirements.keys():
        for day in DAYS:
            for hour in range(1, HOURS_PER_DAY + 1):
                model.add(
                    sum(
                        x[(classroom, course, teacher, room, day, hour)]
                        for (course, teacher, rooms, _) in requirements[classroom]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour) in x
                    ) <= 1
                )


def add_off_day_constraint(model, x, requirements):
    """Öğretmenin izin günü ders atanamaz"""
    teacher_off_day = build_teacher_off_day()

    for teacher, off_day in teacher_off_day.items():
        if off_day not in DAYS:
            continue
        for hour in range(1, HOURS_PER_DAY + 1):
            model.add(
                sum(
                    x[(classroom, course, teacher, room, off_day, hour)]
                    for classroom, reqs in requirements.items()
                    for (course, t, rooms, _) in reqs
                    if t == teacher
                    for room in rooms
                    if (classroom, course, teacher, room, off_day, hour) in x
                ) == 0
            )


def add_penalty(model, x, requirements):
    penalties = []

    # Günlük 4'ten fazla ders olmamalı
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, _) in reqs:
            for day in DAYS:
                daily_count = sum(
                    x[(classroom, course, teacher, room, day, hour)]
                    for hour in range(1, HOURS_PER_DAY + 1)
                    for room in rooms
                    if (classroom, course, teacher, room, day, hour) in x
                )
                excess = model.new_int_var(
                    0, HOURS_PER_DAY, f'excess_{classroom}_{course}_{day}')
                model.add_max_equality(excess, [daily_count - 4, 0])
                penalties.append(excess)

    for classroom in requirements.keys():
        for day in DAYS:
            daily_total = sum(
                x[(classroom, course, teacher, room, day, hour)]
                for _, reqs in requirements.items()
                if _ == classroom
                for (course, teacher, rooms, _) in reqs
                for room in rooms
                for hour in range(1, HOURS_PER_DAY+1)
            )
            is_empty = model.new_bool_var(f'is_empty_{classroom}_{day}')
            model.add(daily_total == 0).only_enforce_if(is_empty)
            model.add(daily_total > 0).only_enforce_if(is_empty.Not())
            penalties.append(is_empty)
    # Gap (boşluk) cezası
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, _) in reqs:
            for day in DAYS:
                for hour in range(2, HOURS_PER_DAY + 1):
                    curr = sum(
                        x[(classroom, course, teacher, room, day, hour)]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour) in x
                    )
                    prev = sum(
                        x[(classroom, course, teacher, room, day, hour - 1)]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour - 1) in x
                    )
                    nxt_terms = [
                        x[(classroom, course, teacher, room, day, hour + 1)]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour + 1) in x
                    ]
                    nxt = sum(nxt_terms) if nxt_terms else 0

                    gap = model.new_bool_var(
                        f'gap_{classroom}_{course}_{day}_{hour}')
                    model.add(prev >= 1).only_enforce_if(gap)
                    model.add(curr == 0).only_enforce_if(gap)
                    model.add(nxt >= 1).only_enforce_if(gap)
                    model.add(gap >= prev + (1 - curr) + nxt - 2)
                    penalties.append(gap)

    return penalties


class ScheduleCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, x, requirements, max_solutions=5):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.x = x
        self.requirements = requirements
        self.max_solutions = max_solutions
        self.solutions = []

    def on_solution_callback(self):
        print(f"Çözüm bulundu: {len(self.solutions) + 1}")
        if len(self.solutions) < self.max_solutions:
            schedule = build_schedule(self, self.x, self.requirements)
            fitness, soft_violation = calculate_fitness(
                schedule, self.requirements)
            self.solutions.append({
                'schedule': schedule,
                'fitness': fitness,
                'soft_violation': soft_violation
            })
            if len(self.solutions) == self.max_solutions:
                self.stop_search()


def _build_model(requirements):
    model = cp_model.CpModel()
    x = build_veriables(model, requirements)
    add_weekly_hours_constraint(model, x, requirements)
    add_teacher_constraint(model, x, requirements)
    add_room_constraint(model, x, requirements)
    add_classroom_constraint(model, x, requirements)
    add_off_day_constraint(model, x, requirements)
    return model, x


def find_optimal(requirements):
    model, x = _build_model(requirements)
    solver = cp_model.CpSolver()

    penalties = add_penalty(model, x, requirements)
    total = model.new_int_var(0, 100000, 'total')
    model.add(total == sum(penalties))
    model.minimize(total)

    solver.parameters.num_search_workers = 4
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.solve(model)
    print(f"Optimal status: {solver.status_name(status)}")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return int(solver.objective_value)
    return None


def solve():
    requirements = build_requirements()
    print(f"Gereksinim sayısı: {sum(len(v) for v in requirements.values())}")

    optimal = find_optimal(requirements)
    print(f"Optimal: {optimal}")

    model, x = _build_model(requirements)
    solver = cp_model.CpSolver()

    penalties = add_penalty(model, x, requirements)
    total = model.new_int_var(0, 100000, 'total2')
    model.add(total == sum(penalties))

    if optimal is not None:
        slack = max(5, int(optimal * 0.1))
        model.add(total <= optimal + slack)
        print(f"Slack ile üst sınır: {optimal + slack}")

    callback = ScheduleCallback(x, requirements)
    solver.parameters.num_search_workers = 4
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.max_time_in_seconds = 120.0

    solver.solve(model, callback)

    if callback.solutions:
        return sorted(callback.solutions, key=lambda s: s['fitness'], reverse=True)
    return None
