from groq import Groq

def generate_narrative(monthly, regional, total, completion_rate, dna_rate, api_key):
    client = Groq(api_key=api_key)
    best_region = regional.iloc[0]['region']
    best_rate = regional.iloc[0]['completion_rate']
    worst_region = regional.iloc[-1]['region']
    worst_rate = regional.iloc[-1]['completion_rate']

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""
You are a senior NHS data analyst writing an executive summary
for the Lung Cancer Screening Programme monthly performance report.

Key statistics:
- Total patients referred: {total}
- Overall completion rate: {completion_rate}%
- DNA (Did Not Attend) rate: {dna_rate}%
- Best performing region: {best_region} ({best_rate}%)
- Lowest performing region: {worst_region} ({worst_rate}%)
- Monthly trend: {monthly[['month','completion_rate']].to_string()}

Write a professional 4 paragraph executive summary covering:
Paragraph 1: Overall performance summary
Paragraph 2: Regional highlights and concerns
Paragraph 3: Key risks and anomalies to flag
Paragraph 4: Recommended actions for next month

Write in plain English for a non-technical Programme Director.
Be specific with numbers. Be direct about problems.
Do not use bullet points. Write in prose only.
"""
        }],
        max_tokens=1000
    )
    return response.choices[0].message.content
