import streamlit as st
import pandas as pd
import plotly.express as px

# Define the claim categories
categories = ["Bodily Injury", "Collision", "PDL", "Med Pay", "Comprehensive"]

# Pre-filled data for Year 1 (The Past)
data_y1 = {
    "Category": categories,
    "Volume": [50, 100, 75, 20, 30],
    "Severity": [1000, 500, 300, 2000, 800]
}
df_y1 = pd.DataFrame(data_y1)

# Pre-filled data for Year 2 (The Present)
data_y2 = {
    "Category": categories,
    "Volume": [45, 110, 80, 25, 35],
    "Severity": [1100, 550, 320, 2100, 850]
}
df_y2 = pd.DataFrame(data_y2)

# Function to calculate average severity
def calculate_average_severity(df):
    total_cost = (df['Severity'] * df['Volume']).sum()
    total_claims = df['Volume'].sum()
    return total_cost / total_claims if total_claims > 0 else 0

# Function to decompose severity change into Severity and Mix effects
def decompose_severity_change(df_y1, df_y2):
    avg_sev_y1 = calculate_average_severity(df_y1)
    avg_sev_y2 = calculate_average_severity(df_y2)
    
    # Scenario 1: Year 2 severities with Year 1 volumes
    df_sev_y2_mix_y1 = df_y1.copy()
    df_sev_y2_mix_y1['Severity'] = df_y2['Severity']
    avg_sev_sev_y2_mix_y1 = calculate_average_severity(df_sev_y2_mix_y1)
    
    # Scenario 2: Year 1 severities with Year 2 volumes
    df_sev_y1_mix_y2 = df_y2.copy()
    df_sev_y1_mix_y2['Severity'] = df_y1['Severity']
    avg_sev_sev_y1_mix_y2 = calculate_average_severity(df_sev_y1_mix_y2)
    
    # Calculate effects in two orders (Shapley value approach)
    severity_effect_order1 = avg_sev_sev_y2_mix_y1 - avg_sev_y1
    mix_effect_order1 = avg_sev_y2 - avg_sev_sev_y2_mix_y1
    mix_effect_order2 = avg_sev_sev_y1_mix_y2 - avg_sev_y1
    severity_effect_order2 = avg_sev_y2 - avg_sev_sev_y1_mix_y2
    
    # Average the effects
    severity_effect = (severity_effect_order1 + severity_effect_order2) / 2
    mix_effect = (mix_effect_order1 + mix_effect_order2) / 2
    
    return severity_effect, mix_effect, avg_sev_y1, avg_sev_y2

# Streamlit app setup
st.title("🚗 Claim Severity Playground 🚨")
st.write("**Instructions**: Edit the tables below to tweak your claim data. See the magic happen live!")

# Display tables side by side
col1, col2 = st.columns(2)

with col1:
    st.write("**Year 1: The Past**")
    edited_df_y1 = st.data_editor(
        df_y1,
        column_config={
            "Category": st.column_config.TextColumn(disabled=True),
            "Volume": st.column_config.NumberColumn(min_value=0, step=1),
            "Severity": st.column_config.NumberColumn(min_value=0.0, step=0.01)
        },
        hide_index=True
    )

with col2:
    st.write("**Year 2: The Present**")
    edited_df_y2 = st.data_editor(
        df_y2,
        column_config={
            "Category": st.column_config.TextColumn(disabled=True),
            "Volume": st.column_config.NumberColumn(min_value=0, step=1),
            "Severity": st.column_config.NumberColumn(min_value=0.0, step=0.01)
        },
        hide_index=True
    )

# Check for valid input
if edited_df_y1['Volume'].sum() == 0 or edited_df_y2['Volume'].sum() == 0:
    st.error("Oops! You need at least one claim in each period to play. Add some volumes!")
else:
    # Calculate and decompose severity change
    severity_effect, mix_effect, avg_sev_y1, avg_sev_y2 = decompose_severity_change(edited_df_y1, edited_df_y2)
    total_change = avg_sev_y2 - avg_sev_y1

    # Display results
    st.subheader("🎉 The Big Reveal 🎉")
    st.write(f"**Year 1 Average Severity:** ${avg_sev_y1:.2f}")
    st.write(f"**Year 2 Average Severity:** ${avg_sev_y2:.2f}")
    st.write(f"**Total Change:** ${total_change:.2f}")
    st.write(f"**Severity Effect:** ${severity_effect:.2f} (Cost changes)")
    st.write(f"**Mix Effect:** ${mix_effect:.2f} (Category shifts)")

    # Bar chart visualization
    st.subheader("📊 See It in Action")
    effects = ['Severity Effect', 'Mix Effect']
    values = [severity_effect, mix_effect]
    fig = px.bar(
        x=effects,
        y=values,
        title="What’s Driving the Change?",
        labels={'x': 'Effect', 'y': 'Change in Severity ($)'},
        color=effects,
        color_discrete_map={'Severity Effect': '#ff6347', 'Mix Effect': '#4682b4'}
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig)

    # Fun explanation
    st.subheader("🤓 How This Magic Happens")
    st.markdown("""
    - **Severity Effect**: Shows how much claim cost changes (severity) affect the total, assuming the mix stays the same.
    - **Mix Effect**: Reveals the impact of shifting claim types (e.g., more Collision, less Bodily Injury), assuming costs don’t change.
    - **Math Trick**: We split the total change fairly between these effects using the Shapley value method.

    **Play Around**: 
    - Increase Collision severity in Year 2—see the Severity Effect jump!
    - Add more Med Pay claims in Year 2—watch the Mix Effect shift!
    """)
