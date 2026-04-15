from ortools.sat.python import cp_model 
from ortools.sat.python.cp_model_helper import CpSolverStatus 


from schedule.models import CourseRequirement, Room, Teacher, Classroom, Course


DAYS = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
HOURS_PER_DAY = 8

OFF_DAY_MAP = {
    '1': 'Pazartesi',
    '2': 'Salı',
    '3': 'Çarşamba',
    '4': 'Perşembe',
    '5': 'Cuma',
}


def build_requirements():
    requirements = {}

    for req in CourseRequirement.objects.filter(is_active=True, teacher__is_active=True, course__is_active=True):
        course = req.course
        teacher = req.teacher
        classroom = req.classroom.name
        weekly_hours = req.weekly_hours
        if course.is_lab:
            rooms = list(course.allowed_rooms.values_list('name', flat=True))
        else:
            rooms = list(Room.objects.filter(
                room_type='normal').values_list('name', flat=True))

        if classroom not in requirements:
            requirements[classroom] = []

        requirements[classroom].append(
            (course.name, teacher.name, rooms, weekly_hours))
    return requirements


def build_teacher_off_day():
    teachers = {}

    for teacher in Teacher.objects.filter(is_active=True):
        teachers[teacher.name] = OFF_DAY_MAP.get(
            teacher.off_day, teacher.off_day)
    return teachers


def build_veriables(model, requirements):
    x = {}
    for classroom, req in requirements.items():
        for (course, teacher, rooms, weekly_hours) in req:
            for room in rooms:
                for day in DAYS:
                    for hour in range(1, HOURS_PER_DAY+1):
                        x[(classroom, course, teacher, room, day, hour)] = model.new_bool_var(
                            f'x_{classroom}_{course}_{teacher}_{room}_{day}_{hour}')

    return x


def build_schedule(self, x, requirements):
    schedule = {}
    for day in DAYS:
        schedule[day] = {}
        for hour in range(1, HOURS_PER_DAY+1):
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

    for hour in range(1, HOURS_PER_DAY+1):
        if schedule[day][hour]:
            found = any(entry['classroom'] == classroom and entry['course'] ==
                        course for entry in schedule[day][hour])
            if found:
                count += 1
    return count


def has_gap_in_day(schedule, classroom, course, day):
    this_course = []

    for hour in range(1, HOURS_PER_DAY+1):
        if schedule[day][hour]:
            found = any(entry['classroom'] == classroom and entry['course'] ==
                        course for entry in schedule[day][hour])
            if found:
                this_course.append(hour)

    this_course.sort()

    for i in range(1, len(this_course)):
        if this_course[i] - this_course[i-1] > 1:
            return True

    return False


def calculate_fitness(schedule, requirements):
    soft_violation = 0

    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, weekly_hours) in reqs:
            for day in DAYS:
                if daily_course_count(schedule, classroom, course, day) > 4:
                    soft_violation += 1
                if has_gap_in_day(schedule, classroom, course, day):
                    soft_violation += 1
    max_violation = len(requirements) * len(DAYS) * 2
    if max_violation == 0:
        return 100, 0
    fitness = max(0, 100 - int(soft_violation / max_violation * 100))
    return fitness, soft_violation


def add_weekly_hours_constraint(model, x, requirements):
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, weekly_hours) in reqs:
            model.add(
                sum(
                    x[(classroom, course, teacher, room, day, hour)]
                    for day in DAYS
                    for hour in range(1, HOURS_PER_DAY+1)
                    for room in rooms
                    if (classroom, course, teacher, room, day, hour) in x
                ) == weekly_hours
            )


def add_teacher_constraint(model, x, requirements):
    teachers = list(Teacher.objects.filter(
        is_active=True).values_list('name', flat=True))

    for teacher in teachers:
        for day in DAYS:
            for hour in range(1, HOURS_PER_DAY+1):
                model.add(
                    sum(
                        x[(classroom, course, t, room, day, hour)]
                        for classroom, reqs in requirements.items()
                        for (course, t, rooms, _) in reqs
                        if t == teacher
                        for room in rooms
                        if (classroom, course, t, room, day, hour) in x

                    ) <= 1
                )


def add_room_constraint(model, x, requirements):
    all_rooms = list(Room.objects.filter(
        is_active=True).values_list('name', flat=True))
    for room in all_rooms:
        for day in DAYS:
            for hour in range(1, HOURS_PER_DAY+1):
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
    classrooms = list(Classroom.objects.filter(
        is_active=True).values_list('name', flat=True))

    for classroom in classrooms:
        for day in DAYS:
            for hour in range(1, HOURS_PER_DAY+1):
                model.add(
                    sum(
                        x[(classroom, course, teacher, room, day, hour)]
                        for cr, reqs in requirements.items()
                        for (course, teacher, rooms, _) in reqs
                        for room in rooms
                        if cr == classroom
                        if (classroom, course, teacher, room, day, hour) in x
                    ) <= 1
                )


def add_off_day_constraint(model, x, requirements):
    teacher_off_day = build_teacher_off_day()

    for teacher, off_day in teacher_off_day.items():
        for hour in range(1, HOURS_PER_DAY+1):
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
    
    #dört ders üst üste olmamalı
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, weekly_hours) in reqs:
            for day in DAYS:
                daily_count = sum(
                    x[(classroom, course, teacher, room, day, hour)]
                    for hour in range(1, HOURS_PER_DAY+1)
                    for room in rooms
                )
                excess = model.new_int_var(
                    0, HOURS_PER_DAY, f'excess_{classroom}_{course}_{day}')
                model.add_max_equality(
                    excess, [daily_count - 4, 0])
                penalties.append(excess)
                
    # # boş gün olmasın
    # for classroom in requirements.keys():
    #     for day in DAYS:
    #         daily_total = sum(
    #             x[(classroom, course, teacher, room, day, hour)]
    #             for _, reqs in requirements.items()
    #             if _ == classroom
    #             for (course, teacher, rooms, _) in reqs
    #             for room in rooms
    #             for hour in range(1, HOURS_PER_DAY+1)
    #         )
    #         is_empty = model.new_bool_var(f'is_empty_{classroom}_{day}')
    #         model.add(daily_total == 0).only_enforce_if(is_empty)
    #         model.add(daily_total > 0).only_enforce_if(is_empty.Not())
    #         penalties.append(is_empty)
            
    #gap kontrolü         
    for classroom, reqs in requirements.items():
        for (course, teacher, rooms, weekly_hours) in reqs:
            for day in DAYS:
                for hour in range(2, HOURS_PER_DAY+1):
                    curr = sum(
                        x[(classroom, course, teacher,room, day,hour)]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour) in x
                    )
                    
                    prev = sum(
                        x[(classroom, course, teacher, room, day, hour-1)]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour-1) in x
                    )
                    
                    nxt = sum(
                        x[(classroom, course, teacher, room, day, hour+1)]
                        for room in rooms
                        if (classroom, course, teacher, room, day, hour+1) in x
                    )
                    
                    gap = model.new_bool_var(f'gap_{classroom}_{course}_{day}_{hour}')
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


def find_optimal(requirements):
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()

    x = build_veriables(model, requirements)
    add_weekly_hours_constraint(model, x, requirements)
    add_teacher_constraint(model, x, requirements)
    add_room_constraint(model, x, requirements)
    add_classroom_constraint(model, x, requirements)
    add_off_day_constraint(model, x, requirements)

    penalties = add_penalty(model, x, requirements)

    total = model.new_int_var(0, 100000, 'total')
    model.add(total == sum(penalties))
    model.minimize(total)

    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.solve(model)
    print(f"Optimal status: {solver.status_name(status)}")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return int(solver.objective_value)
    return None


def solve():
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()

    requirements = build_requirements()
    optimal = find_optimal(requirements)
    print(f"Optimal: {optimal}")

    x = build_veriables(model, requirements)
    add_weekly_hours_constraint(model, x, requirements)
    add_teacher_constraint(model, x, requirements)
    add_room_constraint(model, x, requirements)
    add_classroom_constraint(model, x, requirements)
    add_off_day_constraint(model, x, requirements)

    penalties = add_penalty(model, x, requirements)
    total = model.new_int_var(0, 100000, 'total2')
    model.add(total == sum(penalties))

    if optimal is not None:
        slack = max(5, int(optimal * 0.1))
        model.add(total <= optimal + slack)
        print(f"Slack ile üst sınır: {optimal + slack}")

    callback = ScheduleCallback(x, requirements)
    solver.parameters.num_search_workers = 1
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.max_time_in_seconds = 120.0

    solver.solve(model, callback)

    if callback.solutions:
        return sorted(callback.solutions, key=lambda x: x['fitness'], reverse=True)
    else:
        return None
