import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency

# =========================
# Fungsi Analisis
# =========================
def analyze_delivery_vs_review(df):
    """Hubungan antara lama pengiriman dengan review score + rata-rata waktu pengiriman."""
    df['delivery_duration'] = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.days
    avg_review_by_duration = df.groupby('delivery_duration', as_index=False)['review_score'].mean()

    avg_delivery_time = df['delivery_duration'].mean()
    avg_review_score = df['review_score'].mean()

    return avg_review_by_duration, avg_review_score, avg_delivery_time

def analyze_top_cities_customers(df):
    """Top 5 state berdasarkan pelanggan unik."""
    city_customer_counts = df.groupby('customer_state')['customer_unique_id'].nunique().reset_index()
    return city_customer_counts.sort_values(by='customer_unique_id', ascending=False).head(5)

def analyze_top_cities_revenue(df):
    """Top 5 state berdasarkan revenue."""
    city_revenue = df.groupby('customer_state')['payment_value'].sum().reset_index()
    return city_revenue.sort_values(by='payment_value', ascending=False).head(5)

def analyze_payment_type_counts(df):
    """Jumlah penggunaan metode pembayaran."""
    payment_type_counts = df['payment_type'].value_counts().reset_index()
    payment_type_counts.columns = ['payment_type', 'count']
    return payment_type_counts

def analyze_payment_type_revenue(df):
    """Revenue berdasarkan metode pembayaran."""
    payment_type_revenue = df.groupby('payment_type')['payment_value'].sum().reset_index()
    payment_type_revenue.columns = ['payment_type', 'total_revenue']
    return payment_type_revenue

def safe_qcut(series, q, ascending=True):
    """Helper untuk qcut aman dari error bin duplicate."""
    series = series.rank(method='first') if not ascending else series
    try:
        # Hitung bin dengan duplicates drop
        bins = pd.qcut(series, q, labels=False, duplicates="drop")
        n_bins = bins.nunique()
        labels = list(range(1, n_bins + 1))
        if not ascending:
            labels = labels[::-1]  # untuk recency kebalik
        return pd.qcut(series, q=n_bins, labels=labels, duplicates="drop")
    except ValueError:
        return pd.Series([None] * len(series))

def analyze_rfm_segmentation(df):
    """RFM Segmentation dengan qcut aman."""
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_id": "nunique",
        "payment_value": "sum",
        "order_purchase_timestamp": "max"
    })
    rfm_df.columns = ["customer_unique_id", "frequency", "monetary", "last_order_date"]
    rfm_df["last_order_date"] = pd.to_datetime(rfm_df["last_order_date"]).dt.date
    recent_date = pd.to_datetime(df["order_purchase_timestamp"]).dt.date.max()

    rfm_df["recency"] = rfm_df["last_order_date"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop(columns="last_order_date", inplace=True)
    rfm_df = rfm_df.dropna(subset=["recency", "frequency", "monetary"])

    # Gunakan safe_qcut
    rfm_df['r_score'] = safe_qcut(rfm_df['recency'], 5, ascending=False)
    rfm_df['f_score'] = safe_qcut(rfm_df['frequency'], 5, ascending=True)
    rfm_df['m_score'] = safe_qcut(rfm_df['monetary'], 5, ascending=True)

    rfm_df['rfm_segment'] = (
        rfm_df['r_score'].astype(str) +
        rfm_df['f_score'].astype(str) +
        rfm_df['m_score'].astype(str)
    )

    def assign_rfm_level(row):
        if row['rfm_segment'] == '555':
            return 'Best Customers'
        elif row['r_score'] >= 4 and row['f_score'] >= 4:
            return 'Loyal Customers'
        elif row['r_score'] >= 4 and row['m_score'] >= 4:
            return 'Big Spenders'
        elif row['f_score'] >= 4 and row['m_score'] >= 4:
            return 'Frequent Buyers'
        elif row['r_score'] >= 4:
            return 'Recent Customers'
        elif row['f_score'] >= 4:
            return 'Frequent Customers'
        elif row['m_score'] >= 4:
            return 'High Value Customers'
        else:
            return 'Others'

    rfm_df['rfm_level'] = rfm_df.apply(assign_rfm_level, axis=1)
    return rfm_df

# =========================
# Load Data
# =========================
try:
    df = pd.read_csv("dashboard/main_data.csv")
    datetime_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date', 'review_creation_date', 'review_answer_timestamp'
    ]
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

except FileNotFoundError:
    st.error("Make sure 'main_data.csv' is in the same directory.")
    st.stop()

# =========================
# Sidebar Filter
# =========================
st.sidebar.header("Filter Data")
min_date = df['order_purchase_timestamp'].min().date()
max_date = df['order_purchase_timestamp'].max().date()
date_range = st.sidebar.date_input("Pilih Rentang Tanggal", [min_date, max_date])

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df['order_purchase_timestamp'].dt.date >= start_date) &
                     (df['order_purchase_timestamp'].dt.date <= end_date)]
else:
    filtered_df = df.copy()

st.title("🛒 E-Commerce Public Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Orders", filtered_df['order_id'].nunique())
col2.metric("Total Customers", filtered_df['customer_unique_id'].nunique())
with col3:
    total_revenue = format_currency(filtered_df['payment_value'].sum(), "BRL", locale="pt_BR")
    st.metric("Total Revenue", value=total_revenue)

# =========================
# 1. Rata-rata Review Score + Hubungan Waktu Pengiriman
# =========================
st.subheader("1. Hubungan Waktu Pengiriman dengan Review Score")
avg_review_by_duration_df, avg_review_score, avg_delivery_time = analyze_delivery_vs_review(filtered_df)

col1, col2 = st.columns(2)
col1.metric("Rata-rata Review Score", round(avg_review_score, 2))
col2.metric("Rata-rata Waktu Pengiriman (hari)", round(avg_delivery_time, 2))

fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(data=avg_review_by_duration_df, x='delivery_duration', y='review_score', ax=ax)
ax.set_xlabel('Waktu Pengiriman (hari)', fontsize=12)
ax.set_ylabel('Rata-rata Review Score', fontsize=12)
ax.set_title('Hubungan Waktu Pengiriman dengan Rata-rata Review Score', fontsize=13)
st.pyplot(fig)

# =========================
# 2. Top state berdasarkan pelanggan dan revenue tertinggi
# =========================
st.subheader("2. Top State berdasarkan Pelanggan & Revenue Tertinggi")
col1, col2 = st.columns(2)

with col1:
    top_cities_customers = analyze_top_cities_customers(filtered_df)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(data=top_cities_customers, x='customer_unique_id', y='customer_state', palette='viridis', ax=ax)
    ax.set_title('Top 5 State - Pelanggan Unik', fontsize=15)
    ax.set_xlabel('Jumlah Pelanggan Unik', fontsize=15)
    ax.set_ylabel('State', fontsize=15)
    st.pyplot(fig)

with col2:
    top_cities_revenue = analyze_top_cities_revenue(filtered_df)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(data=top_cities_revenue, x='payment_value', y='customer_state', palette='viridis', ax=ax)
    ax.set_title('Top 5 State - Revenue', fontsize=15)
    ax.set_xlabel('Total Revenue', fontsize=15)
    ax.set_ylabel('State', fontsize=15)
    st.pyplot(fig)

# =========================
# 3. Payment Type Counts & Revenue
# =========================
st.subheader("3. Metode Pembayaran")
col1, col2 = st.columns(2)

with col1:
    payment_type_counts = analyze_payment_type_counts(filtered_df)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(data=payment_type_counts, x='payment_type', y='count', ax=ax)
    ax.set_title('Jumlah Penggunaan Metode Pembayaran', fontsize=15)
    ax.set_xlabel('Metode Pembayaran', fontsize=15)
    ax.set_ylabel('Jumlah Penggunaan', fontsize=15)
    plt.xticks(rotation=45)
    st.pyplot(fig)

with col2:
    payment_type_revenue = analyze_payment_type_revenue(filtered_df)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(data=payment_type_revenue, x='payment_type', y='total_revenue', ax=ax)
    ax.set_title('Total Revenue per Metode Pembayaran', fontsize=15)
    ax.set_xlabel('Metode Pembayaran', fontsize=15)
    ax.set_ylabel('Total Revenue', fontsize=15)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# =========================
# 4. RFM Segmentation
# =========================
st.subheader("4. Segmentasi Pelanggan (RFM)")
rfm_all = analyze_rfm_segmentation(filtered_df)
rfm_level_counts = rfm_all['rfm_level'].value_counts().reset_index()
rfm_level_counts.columns = ['rfm_level', 'count']

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=rfm_level_counts, x='rfm_level', y='count', palette='viridis', ax=ax)
ax.set_title('Distribusi Pelanggan per Segmen RFM')
ax.set_xlabel('Segmen RFM')
ax.set_ylabel('Jumlah Pelanggan')
plt.xticks(rotation=45)
st.pyplot(fig)
