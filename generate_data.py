import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

regions = [
    'North West', 'North East', 'Yorkshire',
    'East Midlands', 'West Midlands', 'East of England',
    'London', 'South East', 'South West'
]

sites = {
    'North West': ['Manchester Royal', 'Liverpool Chest', 'Salford General'],
    'North East': ['Newcastle Freeman', 'Sunderland Royal', 'Durham County'],
    'Yorkshire': ['Leeds General', 'Sheffield Hallamshire', 'Bradford Royal'],
    'East Midlands': ['Nottingham City', 'Leicester Royal', 'Derby Royal'],
    'West Midlands': ['Birmingham Queen Elizabeth', 'Coventry University', 'Wolverhampton New Cross'],
    'East of England': ['Cambridge Addenbrookes', 'Norwich Norfolk', 'Ipswich Hospital'],
    'London': ['Kings College', 'St Thomas', 'Royal London'],
    'South East': ['Brighton Royal Sussex', 'Oxford John Radcliffe', 'Southampton General'],
    'South West': ['Bristol Southmead', 'Plymouth Derriford', 'Exeter Royal Devon']
}

referral_sources = ['GP', 'Community Pharmacy', 'Self-referral', 'Hospital Outpatient']
outcomes = ['Negative', 'Positive - Low Risk', 'Positive - High Risk', 'Inconclusive']
dna_reasons = ['Did Not Attend', 'Cancelled by Patient', 'Cancelled by Hospital', None]

records = []
start_date = datetime(2024, 1, 1)

for i in range(2000):
    region = random.choice(regions)
    site = random.choice(sites[region])
    referral_date = start_date + timedelta(days=random.randint(0, 365))
    age = random.randint(55, 74)
    gender = random.choice(['Male', 'Female'])
    referral_source = random.choice(referral_sources)
    distance_km = round(random.uniform(0.5, 45), 1)
    prev_dna = random.choices([0, 1, 2, 3], weights=[70, 20, 7, 3])[0]

    dna_probability = 0.15
    if prev_dna > 0:
        dna_probability += 0.1 * prev_dna
    if distance_km > 30:
        dna_probability += 0.1
    if age > 70:
        dna_probability += 0.05
    if referral_source == 'Self-referral':
        dna_probability -= 0.05

    attended = random.random() > dna_probability
    screening_date = referral_date + timedelta(days=random.randint(14, 60)) if attended else None
    outcome = random.choices(outcomes, weights=[65, 20, 10, 5])[0] if attended else None
    dna_reason = None if attended else random.choice(dna_reasons[:-1])
    follow_up = random.choice(['Yes', 'No']) if outcome and 'Positive' in outcome else None

    records.append({
        'patient_id': f'NHS{100000 + i}',
        'age': age,
        'gender': gender,
        'region': region,
        'site_name': site,
        'referral_source': referral_source,
        'referral_date': referral_date.strftime('%Y-%m-%d'),
        'screening_date': screening_date.strftime('%Y-%m-%d') if screening_date else None,
        'distance_km': distance_km,
        'previous_dna_count': prev_dna,
        'attended': 'Yes' if attended else 'No',
        'outcome': outcome,
        'dna_reason': dna_reason,
        'follow_up_required': follow_up,
        'appointment_hour': random.randint(8, 17) if attended else None
    })

df = pd.DataFrame(records)
df.to_csv('nhs_screening_data.csv', index=False)
print(f"Generated {len(df)} patient records")
print(f"Attended: {df['attended'].value_counts()['Yes']}")
print(f"Did not attend: {df['attended'].value_counts()['No']}")
