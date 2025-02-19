import streamlit as st
import pandas as pd
import plotly.express as px

# Function to calculate average severity
def calculate_average_severity(df):
    total_cost = (df['Severity'] * df['Volume']).sum()
    total_claims = df['Volume'].sum()
    return total_cost / total_claims if total_claims > 0 else 0

# Function to decompose the change in average severity
def decompose_severity_change(df_y1, df_y2):
    # Calculate average severity for Year 1 and Year 2
    avg_sev_y1 = calculate_average_severity(df_y1)
    avg_sev_y2 = calculate_average_severity(df_y2)
    
    # Intermediate scenarios
    # Severity_Y2, Mix_Y1: Year 2 severities with Year 1 volumes
    df_sev_y2_mix_y1 = df_y1.copy()
    df_sev_y2_mix_y1['Severity'] = df_y2['Severity']
    avg_sev_sev_y2_mix_y1 = calculate_average_severity(df_sev_y2_mix_y1)
    
    # Severity_Y1, Mix_Y2: Year 1 severities with Year 2 volumes
    df_sev_y1_mix_y2 = df_y2.copy()
    df_sev_y1_mix_y2['Severity'] = df_y1['Severity']
    avg_sev_sev_y1_mix_y2 = calculate_average_severity(df_sev_y1_mix_y2)
    
    # Order 1: Severity first, then Mix
    severity_effect_order1 = avg_sev_sev_y2_mix_y1 - avg_sev_y1
    mix_effect_order1 = avg_sev_y2 - avg_sev_sev_y2_mix_y1
    
    # Order 2: Mix first, then Severity
    mix_effect_order2 = avg_sev_sev_y1_mix_y2 - avg_sev_y1
    severity_effect_order2 = avg_sev_y2 - avg_sev_sev_y1_mix_y2
    
    # Average the effects (Shapley value)
    severity_effect = (severity_effect_order1 + severity_effect_order2) / 2
    mix_effect = (mix_effect_order1 + mix_effect_order2) / 2
    
    return severity_effect, mix_effect, avg_sev_y1, avg_sev_y2

# Streamlit dashboard setup
st.title("Insurance Claim Severity Decomposition Dashboard")

# Sample data for Year 1
data_y1 = {
    'Category': ['Auto', 'Home', 'Health'],
    'Severity': [1000, 5000, 2000],
    'Volume': [100, 20, 50]
}
df_y1 = pd.DataFrame(data_y1)

# Sample data for Year 2 (with mix change)
data_y2 = {
    'Category': ['Auto', 'Home', 'Health'],
    'Severity': [1100, 5500, 2200],
    'Volume': [120, 20, 50]
}
df_y2 = pd.DataFrame(data_y2)

# Display input data
st.subheader("Input Data")
col1, col2 = st.columns(2)
with col1:
    st.write("**Year 1 Data**")
    st.dataframe(df_y1)
with col2:
    st.write("**Year 2 Data**")
    st.dataframe(df_y2)

# Perform decomposition
severity_effect, mix_effect, avg_sev_y1, avg_sev_y2 = decompose_severity_change(df_y1, df_y2)
total_change = avg_sev_y2 - avg_sev_y1

# Display decomposition results
st.subheader("Decomposition Results")
st.write(f"**Average Severity Year 1:** ${avg_sev_y1:.2f}")
st.write(f"**Average Severity Year 2:** ${avg_sev_y2:.2f}")
st.write(f"**Total Change:** ${total_change:.2f}")
st.write(f"**Severity Effect:** ${severity_effect:.2f}")
st.write(f"**Mix Effect:** ${mix_effect:.2f}")

# Visualization
st.subheader("Visualization")
effects = ['Severity Effect', 'Mix Effect']
values = [severity_effect, mix_effect]
fig = px.bar(
    x=effects,
    y=values,
    title="Decomposition of Change in Average Severity",
    labels={'x': 'Effect', 'y': 'Contribution to Change ($)'},
    color=effects,
    color_discrete_map={'Severity Effect': '#1f77b4', 'Mix Effect': '#2ca02c'}
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig)

# Explanation
st.subheader("How It Works")
st.markdown("""
This dashboard decomposes the change in **average claim severity** between two periods into:

- **Severity Effect**: The contribution from changes in severity (cost per claim) within each category, assuming the mix of claims stays constant.
- **Mix Effect**: The contribution from changes in the proportion of claims across categories, assuming severity within categories stays constant.

### Methodology
- **Data**: Two periods with claim categories, severities, and volumes.
- **Average Severity**: Calculated as Total Cost / Total Claims.
- **Decomposition**: Uses the Shapley value approach by averaging the effects across all possible orders of applying changes (Severity then Mix, and Mix then Severity).
- **Visualization**: A bar chart shows each effect's contribution to the total change.

In this example:
- Severity increased by 10% in each category.
- Volume increased only for Auto (from 100 to 120), shifting the mix toward a lower-severity category, resulting in a negative Mix Effect.
""")
