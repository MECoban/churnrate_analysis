import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit UI
st.title("Customer Churn Analysis Dashboard")

# File uploader
data_file = st.file_uploader("Upload your CSV file", type=["csv"])

if data_file is not None:
    # Load the uploaded CSV file
    data = pd.read_csv(data_file)

    # Convert date columns to datetime format
    data['created_date'] = pd.to_datetime(data['Created (UTC)'], errors='coerce')
    data['canceled_date'] = pd.to_datetime(data['Canceled At (UTC)'], errors='coerce')

    # Extract year-month for analysis
    data['created_month'] = data['created_date'].dt.to_period('M')
    data['canceled_month'] = data['canceled_date'].dt.to_period('M')

    # Ensure Customer ID uniqueness
    data = data.drop_duplicates(subset=['Customer ID'])

    # Calculate customers created per month
    created_per_month = data.groupby('created_month')['Customer ID'].count()

    # Calculate customers canceled per month
    canceled_per_month = data.groupby('canceled_month')['Customer ID'].count()

    # Calculate active customers per month correctly
    active_per_month = {}
    all_months = pd.period_range(start=data['created_month'].min(), end=pd.Timestamp.today().to_period('M'), freq='M')

    for month in all_months:
        active_customers = data[
            (data['created_month'] <= month) & 
            ((data['canceled_month'].isna()) | (data['canceled_month'] > month))  # Adjusted to exclude canceled customers
        ]
        active_per_month[month] = len(active_customers)

    active_per_month = pd.Series(active_per_month)

    # Correct churn rate calculation
    churn_rate = (canceled_per_month / created_per_month.replace(0, pd.NA)).fillna(0) * 100

    # Prepare final DataFrame
    output = pd.DataFrame({
        'Created': created_per_month,
        'Canceled': canceled_per_month,
        'Active': active_per_month,
        'Churn Rate (%)': churn_rate
    }).fillna(0)

    # Display results
    st.write("### Monthly Customer Analysis")
    st.dataframe(output)

    # Plot customer trends
    st.write("### Customer Trends")
    fig, ax = plt.subplots()
    ax.plot(output.index.astype(str), output['Active'], marker='o', label='Active Customers')
    ax.plot(output.index.astype(str), output['Created'], marker='s', linestyle='dashed', label='New Customers')
    ax.plot(output.index.astype(str), output['Canceled'], marker='x', linestyle='dotted', label='Canceled Customers')
    ax.set_xticklabels(output.index.astype(str), rotation=45)
    ax.set_ylabel("Number of Customers")
    ax.set_title("Monthly Customer Trends")
    ax.legend()
    st.pyplot(fig)

    # Export emails of canceled customers along with cancellation date
    st.write("### Canceled Customers Email List")
    canceled_customers = data.loc[data['canceled_date'].notna(), ['Customer Email', 'canceled_date']].drop_duplicates().sort_values(by='canceled_date')
    st.dataframe(canceled_customers)

    # Save to CSV
    canceled_customers.to_csv('canceled_customers_emails.csv', index=False)
    data.to_csv('monthly_customer_churn_analysis.csv', index_label='Month')

    st.success("Analysis Completed!")
else:
    st.warning("Please upload a CSV file to begin analysis.")
