import streamlit as st
import pandas as pd
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import io

st.set_page_config(
    page_title="NHS Lung Cancer Screening",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0a1628; }
    section[data-testid="stSidebar"] { background-color: #003087 !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
    .nhs-header {
        background: linear-gradient(135deg, #003087 0%, #005EB8 100%);
        padding: 20px 28px; border-radius: 12px; margin-bottom: 24px;
        display: flex; align-items: center; gap: 16px;
    }
    .nhs-logo {
        background: white; color: #003087; font-size: 22px;
        font-weight: 900; padding: 6px 12px; border-radius: 6px; letter-spacing: 1px;
    }
    .nhs-title { color: white; font-size: 22px; font-weight: 600; margin: 0; }
    .nhs-sub { color: #AED6F1; font-size: 13px; margin: 0; }
    .metric-card {
        background: #112240; border: 1px solid #1a3a6b;
        border-radius: 10px; padding: 16px 20px; text-align: center;
    }
    .metric-value { font-size: 32px; font-weight: 700; color: #00A9CE; margin: 0; }
    .metric-label { font-size: 12px; color: #8899aa; text-transform: uppercase; letter-spacing: 1px; margin: 4px 0 0 0; }
    .section-header {
        color: #00A9CE; font-size: 16px; font-weight: 600;
        border-bottom: 2px solid #003087; padding-bottom: 8px; margin: 24px 0 16px 0;
    }
    .alert-box {
        background: #1a0a0a; border-left: 4px solid #ff4444;
        padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 8px;
    }
    .success-box {
        background: #0a1a0a; border-left: 4px solid #00c851;
        padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="nhs-header">
    <div class="nhs-logo">NHS</div>
    <div>
        <p class="nhs-title">Lung Cancer Screening Programme</p>
        <p class="nhs-sub">Performance Analytics and Reporting Dashboard</p>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Configuration")
    st.markdown("---")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.markdown("---")
    uploaded = st.file_uploader("Upload Screening Data CSV", type="csv")
    st.markdown("---")
    st.caption(f"Report generated: {datetime.now().strftime('%d %b %Y %H:%M')}")

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
            SUM(CASE WHEN referral_date IS NULL THEN 1 ELSE 0 END) as missing_date,
            SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) as missing_age,
            SUM(CASE WHEN age < 55 OR age > 74 THEN 1 ELSE 0 END) as out_of_range_age
        FROM screening
    """, conn)
    return monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality

def create_charts(monthly, regional, outcomes, age_groups):
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.patch.set_facecolor('#0a1628')
    for ax in axes.flat:
        ax.set_facecolor('#112240')
        ax.tick_params(colors='#8899aa')
        for spine in ax.spines.values():
            spine.set_edgecolor('#1a3a6b')

    axes[0,0].plot(monthly['month'], monthly['completion_rate'], marker='o', linewidth=2.5, color='#00A9CE')
    axes[0,0].fill_between(range(len(monthly)), monthly['completion_rate'], alpha=0.15, color='#00A9CE')
    axes[0,0].set_title('Monthly Completion Rate %', color='white', fontweight='bold')
    axes[0,0].set_ylabel('Rate %', color='#8899aa')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].set_xticks(range(len(monthly)))
    axes[0,0].set_xticklabels(monthly['month'], rotation=45, ha='right')
    axes[0,0].axhline(y=monthly['completion_rate'].mean(), color='#ff4444', linestyle='--', alpha=0.7)

    colors = ['#00c851' if r > regional['completion_rate'].mean() else '#ff4444' for r in regional['completion_rate']]
    axes[0,1].barh(regional['region'], regional['completion_rate'], color=colors)
    axes[0,1].set_title('Regional Performance %', color='white', fontweight='bold')
    axes[0,1].set_xlabel('Completion Rate %', color='#8899aa')

    if len(outcomes) > 0:
        axes[1,0].pie(outcomes['count'], labels=outcomes['outcome'], autopct='%1.1f%%',
                      colors=['#00c851','#FAC775','#ff4444','#00A9CE'],
                      textprops={'color': 'white'})
        axes[1,0].set_title('Screening Outcomes', color='white', fontweight='bold')

    axes[1,1].bar(age_groups['age_group'], age_groups['completion_rate'], color='#005EB8', edgecolor='#00A9CE')
    axes[1,1].set_title('Completion by Age Group %', color='white', fontweight='bold')
    axes[1,1].set_ylabel('Rate %', color='#8899aa')

    plt.tight_layout(pad=2.0)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0a1628')
    buf.seek(0)
    plt.close()
    return buf

def generate_narrative(monthly, regional, total, completion_rate, dna_rate, api_key):
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        best_region = regional.iloc[0]['region']
        best_rate = regional.iloc[0]['completion_rate']
        worst_region = regional.iloc[-1]['region']
        worst_rate = regional.iloc[-1]['completion_rate']
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"""
You are a senior NHS data analyst. Write a 4 paragraph executive summary.
Total referred: {total}, Completion: {completion_rate}%, DNA rate: {dna_rate}%
Best region: {best_region} ({best_rate}%), Worst: {worst_region} ({worst_rate}%)
Monthly trend: {monthly[['month','completion_rate']].to_string()}
Cover: overall performance, regional highlights, risks, recommendations.
Plain English, no bullet points, specific numbers only."""}],
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI summary unavailable: {str(e)}"

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

if uploaded:
    with st.spinner("Processing screening data..."):
        df = load_and_clean(uploaded)
        conn = sqlite3.connect(':memory:')
        df.to_sql('screening', conn, index=False)

    total = len(df)
    attended = len(df[df['attended'] == 'Yes'])
    dna = len(df[df['attended'] == 'No'])
    completion_rate = round(attended / total * 100, 1)
    dna_rate = round(dna / total * 100, 1)
    positive = len(df[df['outcome'].str.contains('Positive', na=False)])
    dq_issues = df.isnull().sum().sum()
    dq_score = max(0, round(100 - (dq_issues / (total * len(df.columns)) * 100), 0))

    cols = st.columns(6)
    metrics = [
        ("Total Referred", f"{total:,}", "👥"),
        ("Attended", f"{attended:,}", "✅"),
        ("Did Not Attend", f"{dna:,}", "❌"),
        ("Completion Rate", f"{completion_rate}%", "📊"),
        ("Positive Results", f"{positive:,}", "🔬"),
        ("Data Quality", f"{dq_score}%", "🛡️"),
    ]
    for col, (label, value, icon) in zip(cols, metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div style="font-size:20px">{icon}</div>
            <p class="metric-value">{value}</p>
            <p class="metric-label">{label}</p>
        </div>
        """, unsafe_allow_html=True)

    monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality = run_analysis(conn)

    st.markdown('<p class="section-header">Performance Alerts</p>', unsafe_allow_html=True)
    avg_rate = monthly['completion_rate'].mean()
    low_regions = regional[regional['completion_rate'] < avg_rate]
    if len(low_regions) > 0:
        for _, row in low_regions.iterrows():
            st.markdown(f"""
            <div class="alert-box">
                <strong style="color:#ff4444">Below Average:</strong>
                <span style="color:#cccccc"> {row['region']} — {row['completion_rate']}%
                ({avg_rate - row['completion_rate']:.1f}% below average)</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box"><span style="color:#00c851">All regions performing above average</span></div>', unsafe_allow_html=True)

    st.markdown('<p class="section-header">Performance Dashboard</p>', unsafe_allow_html=True)
    chart_buf = create_charts(monthly, regional, outcomes, age_groups)
    st.image(chart_buf, use_column_width=True)

    st.markdown('<p class="section-header">Detailed Analysis</p>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Monthly", "Regional", "Outcomes", "DNA Reasons", "Sites", "Data Quality"])
    with tab1: st.dataframe(monthly, use_container_width=True)
    with tab2: st.dataframe(regional, use_container_width=True)
    with tab3: st.dataframe(outcomes, use_container_width=True)
    with tab4: st.dataframe(dna_reasons, use_container_width=True)
    with tab5: st.dataframe(sites, use_container_width=True)
    with tab6: st.dataframe(data_quality, use_container_width=True)

    st.markdown('<p class="section-header">AI Executive Summary</p>', unsafe_allow_html=True)
    if api_key:
        with st.spinner("Generating AI narrative..."):
            narrative = generate_narrative(monthly, regional, total, completion_rate, dna_rate, api_key)
        st.markdown(f"""
        <div style="background:#112240;border-left:4px solid #005EB8;padding:20px;border-radius:0 10px 10px 0;color:#cccccc;line-height:1.8">
        {narrative}
        </div>
        """, unsafe_allow_html=True)
    else:
        narrative = "AI summary not generated"
        st.info("Add a Groq API key in the sidebar to generate the AI executive summary")

    st.markdown('<p class="section-header">Export Report</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        excel_buf = export_excel(monthly, regional, outcomes, dna_reasons, age_groups, sites, data_quality, narrative)
        st.download_button("Download Excel Report", data=excel_buf,
            file_name=f"nhs_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with col2:
        st.download_button("Download Executive Summary", data=narrative,
            file_name="executive_summary.txt", mime="text/plain",
            use_container_width=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#8899aa">
        <div style="font-size:64px;margin-bottom:16px">🏥</div>
        <h2 style="color:#00A9CE">Upload Screening Data to Begin</h2>
        <p>Upload your NHS Lung Cancer Screening CSV file using the sidebar</p>
    </div>
    """, unsafe_allow_html=True)
