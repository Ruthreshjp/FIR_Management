from app.agents.section_corrector import correct_sections

# Simulate a robbery complaint
facts = {
    'accused_count': 4,
    'weapon_used': 'knife',
    'victim_status': 'injured',
    'accused_fled': True,
    'premeditated': True,
    'minor_involved': False,
    'complaint_text': 'Ramesh stabbed my brother with a knife and fled in a car along with three others'
}

raw = [
    {'act': 'BNS', 'section_number': '309', 'offense': 'Robbery', 'confidence': 0.8, 'primary': True},
    {'act': 'IPC', 'section_number': '392', 'offense': 'Robbery', 'confidence': 0.8, 'primary': False},
]

result = correct_sections(raw, facts)
print('Output sections:')
for s in result:
    print(f'  {s["act"]} {s["section_number"]} - {s["offense"]}')
print()
print('Corrector log above shows what rules fired')
