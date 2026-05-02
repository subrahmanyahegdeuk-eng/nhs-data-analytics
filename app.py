import streamlit as st
import pandas as pd
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from narrative import generate_narrative
from datetime import datetime
import groq
import io

st.set_page_config(page_title="NHS Screening Report Generator", layout="wide")
st.title("NHS Lung Cancer Screening — Report Generator")
st.caption("Upload raw screening data to generate a full monthly performance report with AI narrative summary")

with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    uploaded = st.file_uploader("Upload NHS Screening CSV", type="csv")
    st.caption("Built for NHS Lung Cancer Screening Programme")

def load_and_clean(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    df['referral_date'] = pd.to_datetime(df['referral_date'], errors='coerce')
    df['screening_date'] = pd.to_datetime(df['screening_date'], errors='coerce')
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df['distance_km'] = pd.to_numeric(df['distance_km'], errors='coerce')
    return df

def run_analysis(conn):
    monthly = pd.read_sql("""
        SELECT strftime('%Y-%m', referral_date) as month,
            COUNT(*) as total_referred,
            SUM(CASE WHEN attended='Yes' THEN 1 ELSE 0 END) as attended,
            SUM(CASE WHEN attended='No' THEN 1 ELSE 0 END) as dna,
            ROUND(SUM(CASE WHEN attended='Yes' THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1) as completion_rate
        FROM screening WHERE referral_date IS NOT NULL
        GROUP BY month ORDER BY month
    """, conn)
    regional = pd.read_sql("""
        SELECT region, COUNT(*) as total_referred,
            SUM(CASE WHEN attended='Yes' THEN 1 ELSE 0 END) as attended,
            ROUND(SUM(CASE WHEN attended='Yes' THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1) as completion_rate,
            SUM(CASE WHEN outcome LIKE '%Positive%' THEN 1 ELSE 0 END) as positive_results
        FROM screening GROUP BY region ORDER BY completion_rate DESC
    """, conn)
    outcomes = pd.read_sql("""
        SELECT outcome, COUNT(*) as count,
            ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) as percentage
        FROM screening WHERE outcome IS NOT NULL
        GROUP BY outcome ORDER BY count DESC
    """, conn)
    dna_reasons = pd.read_sql("""
        SELECT dna_reason, COUNT(*) as count
        FROM screening WHERE attended='No' AND dna_reason IS NOT NULL
        GROUP BY dna_reason ORDER BY count DESC
    """, conn)
    age_groups = pd.read_sql("""
        SELECT CASE
            WHEN age BETWEEN 55 AND 59 THEN '55-59'
            WHEN age BETWEEN 60 AND 64 THEN '60-64'
            WHEN age BETWEEN 65 AND 69 THEN '65-69'
            WHEN age BETWEEN 70 AND 74 THEN '70-74'
            ELSE 'Other' END as age_group,
            COUNT(*) as total,
            ROUND(SUM(CASE WHEN attended='Yes' THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1) as completion_rate
        FROM screening GROUP BY age_group ORDER BY age_group
    """, conn)
    sites = pd.read_sql("""
        SELECT site_name, region, COUNT(*) as total,
            ROUND(SUM(CASE WHEN attended='Yes' THEN 1.0 ELSE 0.0 END)/COUNT(*)*100,1) as completion_rate
        FROM screening GROUP BY site_name ORDER BY completion_rate DESC
    """, conn)
    data_quality = pd.read_sql("""
        SELECT COUNT(*) as total_records,
            SUM(CASE WHEN patient_id IS NULL THEN 1 ELSE 0 END) as missing_id,
            SUM(CASE WHEN referral_date IS NULL THEN 1 ELSE 0 END) as missing_referral_date,
            SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) as missing_age,
            SUM(CASE WHEN region IS NULL THEN 1 ELSE 0 END) as missing_region,
            SUM(CASE WHEN age < 55 OR age > 74 THEN 1 ELSE 0 END) as out_of_range_age
        FROM screening
    """, conn)
    return monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality


def create_charts(monthly, regional, outcomes, age_groups):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('NHS Lung Cancer Screening — Performance Dashboard', fontsize=14, fontweight='bold')
    axes[0,0].plot(monthly['month'], monthly['completion_rate'], marker='o', linewidth=2, color='#1D9E75')
    axes[0,0].set_title('Monthly Completion Rate %')
    axes[0,0].set_ylabel('Completion Rate %')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].axhline(y=monthly['completion_rate'].mean(), color='red', linestyle='--', alpha=0.5, label='Average')
    axes[0,0].legend()
    colors = ['#1D9E75' if r > regional['completion_rate'].mean() else '#E24B4A' for r in regional['completion_rate']]
    axes[0,1].barh(regional['region'], regional['completion_rate'], color=colors)
    axes[0,1].set_title('Completion Rate by Region %')
    axes[0,1].set_xlabel('Completion Rate %')
    axes[0,1].axvline(x=regional['completion_rate'].mean(), color='black', linestyle='--', alpha=0.5, label='Average')
    axes[0,1].legend()
    if len(outcomes) > 0:
        axes[1,0].pie(outcomes['count'], labels=outcomes['outcome'], autopct='%1.1f%%',
                      colors=['#1D9E75','#FAC775','#E24B4A','#B5D4F4'])
        axes[1,0].set_title('Screening Outcomes')
    axes[1,1].bar(age_groups['age_group'], age_groups['completion_rate'], color='#0F6E56')
    axes[1,1].set_title('Completion Rate by Age Group %')
    axes[1,1].set_ylabel('Completion Rate %')
    axes[1,1].set_xlabel('Age Group')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

def export_excel(monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality, narrative):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        monthly.to_excel(writer, sheet_name='Monthly Summary', index=False)
        regional.to_excel(writer, sheet_name='Regional Breakdown', index=False)
        outcomes.to_excel(writer, sheet_name='Outcomes', index=False)
        dna_reasons.to_excel(writer, sheet_name='DNA Reasons', index=False)
        age_groups.to_excel(writer, sheet_name='Age Groups', index=False)
        sites.to_excel(writer, sheet_name='Site Performance', index=False)
        data_quality.to_excel(writer, sheet_name='Data Quality', index=False)
        pd.DataFrame({'Executive Summary': [narrative]}).to_excel(writer, sheet_name='Executive Summary', index=False)
    buf.seek(0)
    return buf

if uploaded and api_key:
    with st.spinner("Loading and cleaning data..."):
        df = load_and_clean(uploaded)
        conn = sqlite3.connect(':memory:')
        df.to_sql('screening', conn, index=False)

    total = len(df)
    attended = len(df[df['attended'] == 'Yes'])
    dna = len(df[df['attended'] == 'No'])
    completion_rate = round(attended / total * 100, 1)
    dna_rate = round(dna / total * 100, 1)
    positive = len(df[df['outcome'].str.contains('Positive', na=False)])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Referred", f"{total:,}")
    col2.metric("Attended", f"{attended:,}")
    col3.metric("Did Not Attend", f"{dna:,}")
    col4.metric("Completion Rate", f"{completion_rate}%")
    col5.metric("Positive Results", f"{positive:,}")
    st.markdown("---")

    monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality = run_analysis(conn)

    st.subheader("Performance Dashboard")
    chart_buf = create_charts(monthly, regional, outcomes, age_groups)
    st.image(chart_buf, width='stretch')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Monthly Performance")
        st.dataframe(monthly, width='stretch')
    with col2:
        st.subheader("Regional Breakdown")
        st.dataframe(regional, width='stretch')

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Screening Outcomes")
        st.dataframe(outcomes, width='stretch')
    with col4:
        st.subheader("DNA Reasons")
        st.dataframe(dna_reasons, width='stretch')

    st.subheader("Site Performance")
    st.dataframe(sites, width='stretch')
    st.subheader("Data Quality Check")
    st.dataframe(data_quality, width='stretch')
    st.markdown("---")

    st.subheader("AI Executive Summary")
    with st.spinner("Generating AI narrative... takes 10-15 seconds"):
        try:
            narrative = generate_narrative(monthly, regional, total, completion_rate, dna_rate, api_key)
            st.info(narrative)
        except Exception as e:
            st.error(f"AI summary failed: {str(e)}")
            narrative = "AI summary unavailable"

    st.markdown("---")
    st.subheader("Export Report")
    col1, col2 = st.columns(2)
    with col1:
        excel_buf = export_excel(monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality, narrative)
        st.download_button("Download Full Excel Report", data=excel_buf,
            file_name=f"nhs_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col2:
        st.download_button("Download Executive Summary", data=narrative,
            file_name="executive_summary.txt", mime="text/plain")

else:
    if not api_key:
        st.info("Enter your Google Gemini API key in the sidebar to get started.")
    elif not uploaded:
        st.info("Upload your NHS screening CSV in the sidebar to get started.")
    with st.expander("What this tool does"):
        st.markdown("""
**NHS Lung Cancer Screening Report Generator**

Upload any screening CSV and get instantly:
- Key performance metrics dashboard
- Monthly completion rate trend chart
- Regional performance breakdown
- Screening outcomes analysis
- DNA reasons breakdown
- Age group performance
- Site level performance table
- Automated data quality check
- AI generated executive summary in plain English
- Full 8 tab Excel report download

**Reduces monthly reporting from hours to seconds**
""")
