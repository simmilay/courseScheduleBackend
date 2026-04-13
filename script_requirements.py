from schedule.models import Classroom, Teacher, Course, CourseRequirement
from django.db.models import Sum

weekly_hours = {
    "Türkçe":               {5: 6, 6: 6, 7: 5, 8: 5},
    "Matematik":            {5: 5, 6: 5, 7: 5, 8: 5},
    "Fen Bilimleri":        {5: 4, 6: 4, 7: 4, 8: 4},
    "Sosyal Bilgiler":      {5: 3, 6: 3, 7: 3, 8: 0},
    "T.C. İnkılap Tarihi":  {5: 0, 6: 0, 7: 0, 8: 2},
    "İngilizce":            {5: 4, 6: 4, 7: 4, 8: 4},
    "Din Kültürü":          {5: 2, 6: 2, 7: 2, 8: 2},
    "Beden Eğitimi":        {5: 2, 6: 2, 7: 2, 8: 2},
    "Görsel Sanatlar":      {5: 1, 6: 1, 7: 1, 8: 1},
    "Müzik":                {5: 1, 6: 1, 7: 1, 8: 1},
    "Bilişim ve Yazılım":   {5: 2, 6: 2, 7: 2, 8: 2},
}

teacher_assignment = {
    "Türkçe": ["Türkçe Öğretmeni 1", "Türkçe Öğretmeni 2", "Türkçe Öğretmeni 3", "Türkçe Öğretmeni 4"],
    "Matematik": ["Matematik Öğretmeni 1", "Matematik Öğretmeni 2", "Matematik Öğretmeni 3", "Matematik Öğretmeni 4"],
    "Fen Bilimleri": ["Fen Bilimleri Öğretmeni 1", "Fen Bilimleri Öğretmeni 2", "Fen Bilimleri Öğretmeni 3"],
    "Sosyal Bilgiler": ["Sosyal Bilgiler Öğretmeni 1", "Sosyal Bilgiler Öğretmeni 2"],
    "T.C. İnkılap Tarihi": ["İnkılap Tarihi Öğretmeni 1"],
    "İngilizce": ["İngilizce Öğretmeni 1", "İngilizce Öğretmeni 2", "İngilizce Öğretmeni 3"],
    "Din Kültürü": ["Din Kültürü Öğretmeni 1", "Din Kültürü Öğretmeni 2"],
    "Beden Eğitimi": ["Beden Eğitimi Öğretmeni 1", "Beden Eğitimi Öğretmeni 2"],
    "Görsel Sanatlar": ["Görsel Sanatlar Öğretmeni 1"],
    "Müzik": ["Müzik Öğretmeni 1"],
    "Bilişim ve Yazılım": ["Bilişim Öğretmeni 1", "Bilişim Öğretmeni 2"],
}

classrooms = []
for grade in [5, 6, 7, 8]:
    for section in ['A', 'B', 'C']:
        classrooms.append(Classroom.objects.get(name=f"{grade}-{section}"))

created_count = 0
skipped_count = 0

for course_name, teacher_names in teacher_assignment.items():
    course = Course.objects.get(name=course_name)
    teacher_count = len(teacher_names)
    for idx, classroom in enumerate(classrooms):
        grade = int(classroom.name.split('-')[0])
        hours = weekly_hours[course_name][grade]
        if hours == 0:
            continue
        teacher_name = teacher_names[idx % teacher_count]
        teacher = Teacher.objects.get(name=teacher_name)
        req, created = CourseRequirement.objects.get_or_create(
            classroom=classroom,
            course=course,
            defaults={"teacher": teacher, "weekly_hours": hours}
        )
        if created:
            created_count += 1
            print(f"[+] {classroom.name} | {course_name} | {teacher_name} | {hours}s/hafta")
        else:
            skipped_count += 1
            print(f"[~] Zaten var: {classroom.name} | {course_name}")

print(f"\nToplam {created_count} yeni gereksinim oluşturuldu, {skipped_count} atlandı.")

print("\n--- Öğretmen Yük Özeti ---")
for course_name, teacher_names in teacher_assignment.items():
    for tname in teacher_names:
        teacher = Teacher.objects.get(name=tname)
        total = CourseRequirement.objects.filter(teacher=teacher).aggregate(total=Sum('weekly_hours'))['total'] or 0
        print(f"{tname}: {total} saat/hafta")