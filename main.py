import streamlit as st
import pandas as pd
import plotly.express as px

# Our fun claim categories
categories = ["Bodily Injury", "Collision", "PDL", "Med Pay", "Comprehensive"]

# Calculate average severity (total cost / total claims)
def calculate_average_severity(df):
    total_cost = (df['Severity'] * df['Volume']).sum()
    total_claims = df['Volume'].sum()
    return total_cost / total_claims if total_claims > 0 else 0

# Break down the change into Severity and Mix effects
def decompose_severity_change(df_y1, df_y2):
    avg_sev_y1 = calculate_average_severity(df_y1)
    avg_sev_y2 = calculate_average_severity(df_y2)
    
    # Mix Period 1’s volumes with Period 2’s severities
    df_sev_y2_mix_y1 = df_y1.copy()
    df_sev_y2_mix_y1['Severity'] = df_y2['Severity']
    avg_sev_sev_y2_mix_y1 = calculate_average_severity(df_sev_y2_mix_y1)
    
    # Mix Period 2’s volumes with Period 1’s severities
    df_sev_y1_mix_y2 = df_y2.copy()
    df_sev_y1_mix_y2['Severity'] = df_y1['Severity']
    avg_sev_sev_y1_mix_y2 = calculate_average_severity(df_sev_y1_mix_y2)
    
    # Two ways to calculate effects (we’ll average them for fairness)
    # Order 1: Severity changes first
    severity_effect_order1 = avg_sev_sev_y2_mix_y1 - avg_sev_y1
    mix_effect_order1 = avg_sev_y2 - avg_sev_sev_y2_mix_y1
    
    # Order 2: Mix changes first
    mix_effect_order2 = avg_sev_sev_y1_mix_y2 - avg_sev_y1
    severity_effect_order2 = avg_sev_y2 - avg_sev_sev_y1_mix_y2
    
    # Average the two orders (Shapley value style)
    severity_effect = (severity_effect_order1 + severity_effect_order2) / 2
    mix_effect = (mix_effect_order1 + mix_effect_order2) / 2
    
    return severity_effect, mix_effect, avg_sev_y1, avg_sev_y2

# Set up the Streamlit party
st.title("🚗 Claim Severity Playground 🚨")
st.write("Play with claim volumes and severities to see how Severity and Mix effects shake up the average severity!")

# Split the screen for two periods
st.subheader("Enter Your Claim Data")
col1, col2 = st.columns(2)

# Period 1: The "Before" Scene
with col1:
    st.write("**Year 1: The Past**")
    data_y1 = {}
    for category in categories:
        st.write(f"**{category}**")
        volume = st.number_input(f"Claims for {category}", min_value=0, step=1, key=f"y1_vol_{category}")
        severity = st.number_input(f"Cost per Claim ($)", min_value=0.0, step=0.01, key=f"y1_sev_{category}")
        data_y1[category] = {'Volume': volume, 'Severity': severity}

# Period 2: The "After" Scene
with col2:
    st.write("**Year 2: The Present**")
    data_y2 = {}
    for category in categories:
        st.write(f"**{category}**")
        volume = st.number_input(f"Claims for {category}", min_value=0, step=1, key=f"y2_vol_{category}")
        severity = st.number_input(f"Cost per Claim ($)", min_value=0.0, step=0.01, key=f"y2_sev_{category}")
        data_y2[category] = {'Volume': volume, 'Severity': severity}

# Turn inputs into DataFrames
df_y1 = pd.DataFrame.from_dict(data_y1, orient='index')
df_y2 = pd.DataFrame.from_dict(data_y2, orient='index')

# Check for zero volumes (no claims = no fun!)
if df_y1['Volume'].sum() == 0 or df_y2['Volume'].sum() == 0:
    st.error("Oops! You need at least one claim in each period to play. Add some volumes!")
else:
    # Do the magic calculations
    severity_effect, mix_effect, avg_sev_y1, avg_sev_y2 = decompose_severity_change(df_y1, df_y2)
    total_change = avg_sev_y2 - avg_sev_y1

    # Show the results
    st.subheader("🎉 The Big Reveal 🎉")
    st.write(f"**Year 1 Average Severity:** ${avg_sev_y1:.2f}")
    st.write(f"**Year 2 Average Severity:** ${avg_sev_y2:.2f}")
    st.write(f"**Total Change:** ${total_change:.2f}")
    st.write(f"**Severity Effect:** ${severity_effect:.2f} (Cost changes)")
    st.write(f"**Mix Effect:** ${mix_effect:.2f} (Category shifts)")

    # Make a cool chart
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

    # Add some fun explanation
    st.subheader("🤓 How This Magic Happens")
    st.markdown("""
    Welcome to the **Claim Severity Playground**! Here’s what’s going on:

    - **Severity Effect**: How much the change in claim costs (severity) moves the needle, if the mix of claims stays the same.
    - **Mix Effect**: How much the shift in claim types (more Collision, less Bodily Injury, etc.) changes things, if costs stay steady.
    - **Math Trick**: We use a fair method (Shapley value) to split the total change between these two effects.

    **Try This**: 
    - Boost the severity of Collision claims in Year 2—watch the Severity Effect soar!
    - Add more Med Pay claims in Year 2—see the Mix Effect wiggle!
    """)
