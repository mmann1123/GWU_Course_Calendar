import json
from collections import defaultdict

data = json.load(open('courses_data.json'))

# Group by building and room
room_schedule = defaultdict(list)

for course in data:
    building = course.get('building', 'Not specified')
    room = course.get('room', 'Not specified')

    if building != 'Not specified' and room != 'Not specified':
        key = f'{building}|{room}'
        room_schedule[key].append({
            'course': course['course_number'],
            'title': course['title'][:40],
            'days': course.get('days', ''),
            'time': course.get('time', {}).get('raw', ''),
            'instructor': course.get('instructor', '')
        })

# Show rooms with multiple courses
print('Rooms with multiple courses scheduled:')
print('=' * 80)
for room_key, courses in sorted(room_schedule.items()):
    if len(courses) >= 2:
        building, room_num = room_key.split('|')
        print(f'\n{building} {room_num} ({len(courses)} courses):')
        for c in courses:
            print(f"  - {c['course']:15} {c['days']:5} {c['time']:20} {c['instructor']}")
