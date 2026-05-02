<div align="center">

# 🏥 NHS Lung Cancer Screening
### AI-Powered Performance Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_LLaMA-F55036?style=for-the-badge&logo=groq&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-Report-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white)
![Free](https://img.shields.io/badge/API-100%25%20Free-00c851?style=for-the-badge)

**Upload raw screening CSV → Get full performance report + AI executive summary in seconds**

[🚀 Live Demo](#) · [📂 View Code](https://github.com/subrahmanyahegdeuk-eng/nhs-data-analytics) · [🐛 Report Bug](#)

</div>

---

## 🎯 The Problem This Solves
❌ Before: NHS analysts spend hours every month manually
cleaning data, running queries, building charts,
and writing narrative summaries✅ After:  Upload a CSV → Complete report in 30 seconds
---

## ✨ What You Get Instantly

| Output | Description |
|--------|-------------|
| 📊 **6 Key Metrics** | Total referred, attended, DNA, completion rate, positive results, data quality score |
| ⚠️ **Performance Alerts** | Automatic red flags for regions below average |
| 📈 **4 Charts** | Monthly trend, regional breakdown, outcomes pie, age group bar |
| 📋 **6 Data Tables** | Monthly, regional, outcomes, DNA reasons, sites, data quality |
| 🤖 **AI Summary** | 4-paragraph plain English executive summary via Groq LLaMA |
| 📥 **Excel Export** | Full 8-tab formatted report download |
| 📄 **Text Export** | Executive summary as downloadable text file |

---

## 🏗️ How it works
📂 Upload NHS Screening CSV
↓
🧹 Data cleaning & validation (pandas)
↓
🗄️ Load into SQLite in-memory database
↓
🔍 Run 7 SQL analytical queries
↓
📊 Generate 4 performance charts (matplotlib)
↓
⚠️ Detect underperforming regions automatically
↓
🤖 Groq LLaMA writes plain English executive summary
↓
📥 Export 8-tab Excel report + text summary
---

## 🔍 SQL Skills Demonstrated

```sql
-- Monthly completion rate trend
SELECT strftime('%Y-%m', referral_date) as month,
    COUNT(*) as total_referred,
    ROUND(SUM(CASE WHEN attended='Yes'
        THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1)
        as completion_rate
FROM screening
GROUP BY month ORDER BY month

-- Regional performance ranking
SELECT region,
    ROUND(SUM(CASE WHEN attended='Yes'
        THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1)
        as completion_rate
FROM screening
GROUP BY region ORDER BY completion_rate DESC

-- Data quality validation
SELECT COUNT(*) as total_records,
    SUM(CASE WHEN patient_id IS NULL
        THEN 1 ELSE 0 END) as missing_id,
    SUM(CASE WHEN age < 55 OR age > 74
        THEN 1 ELSE 0 END) as out_of_range_age
FROM screening

-- DNA rate by region
SELECT region,
    ROUND(SUM(CASE WHEN attended='No'
        THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1)
        as dna_rate
FROM screening
GROUP BY region ORDER BY dna_rate DESC
```

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|-------|-----------|
| 🖥️ Frontend | Streamlit |
| 🗄️ Database | SQLite (in-memory) |
| 📊 Data Processing | pandas |
| 📈 Charts | matplotlib |
| 📥 Excel Export | openpyxl |
| 🤖 AI Narrative | Groq LLaMA 3.3 70b |
| 🐍 Language | Python 3.9+ |

</div>

---

## 📊 Skills Demonstrated
✅ SQL           7 queries — aggregation, CASE statements,
window functions, date functions, validation
✅ Excel         8-tab formatted report with openpyxl
✅ Data cleaning  Null handling, type conversion,
range validation, date parsing
✅ Visualisation  4 chart types in a dashboard layout
✅ AI integration LLM-generated narrative for
non-technical stakeholders
✅ Python         pandas, SQLite, matplotlib, Streamlit
✅ GitHub         Version controlled with documentation
---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/subrahmanyahegdeuk-eng/nhs-data-analytics.git
cd nhs-data-analytics

# Install dependencies
pip install -r requirements.txt

# Generate sample dataset
python generate_data.py

# Run the app
streamlit run app.py
```

> Get your **free** Groq API key at [console.groq.com](https://console.groq.com)

---

## 📋 Usage
Run generate_data.py to create a sample NHS dataset
Enter your Groq API key in the sidebar (optional)
Upload nhs_screening_data.csv
View the full performance dashboard
Read the AI executive summary
Download the Excel report
---

## 🗂️ Dataset

The sample dataset contains **2,000 synthetic patient records** designed
to mirror real NHS lung cancer screening data including:
👥 Demographics    Age 55-74, gender, distance from site
🏥 Sites           9 NHS regions, 27 screening sites
📅 Dates           Referral and screening dates
✅ Attendance      Attended / Did Not Attend status
🔬 Outcomes        Negative, Positive Low/High Risk, Inconclusive
📋 DNA reasons     Did Not Attend, Cancelled by Patient/Hospital
> No real patient data is used. Synthetic data reflects
> realistic attendance patterns based on age, distance,
> and previous DNA history.

---

## 📁 Project Structure
nhs-data-analytics/
├── app.py                  ← Main Streamlit dashboard
├── generate_data.py        ← Synthetic dataset generator
├── requirements.txt        ← Python dependencies
└── README.md              ← This file
---

## 🏥 Why This Matters
📌 Data accuracy in cancer screening directly affects
patient outcomes
📌 Late detection of lung cancer significantly reduces
survival rates
📌 This tool helps screening programmes:
→ Identify underperforming regions before month-end
→ Flag data quality issues before they affect reporting
→ Give managers instant insight without analyst delays
→ Reduce routine reporting time from hours to seconds
---

<div align="center">

## 👨‍💻 Author

**Subrahmanya Anant Hegde**

MSc Computer Science · University of Strathclyde

[![GitHub](https://img.shields.io/badge/GitHub-subrahmanyahegdeuk--eng-181717?style=for-the-badge&logo=github)](https://github.com/subrahmanyahegdeuk-eng)
[![Email](https://img.shields.io/badge/Email-subrahmanyahegdeuk%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:subrahmanyahegdeuk@gmail.com)

*Built to demonstrate NHS data analyst skills —
directly addressing the reporting requirements
of NHS screening programmes*

</div>
