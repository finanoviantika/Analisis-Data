# 🛒 E-Commerce Public Dashboard

Dashboard ini dibuat dengan **Streamlit** untuk menganalisis data e-commerce, termasuk:
- Hubungan waktu pengiriman dengan review score
- Top state berdasarkan pelanggan dan revenue tertinggi
- Metode pembayaran yang sering digunakan dan paling banyak menghasilkan revenue
- Segmentasi pelanggan menggunakan RFM analysis

## Setup Environment - Anaconda
```
conda create --name ecommerce-dashboard python=3.9
conda activate ecommerce-dashboard
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_ecommerce_dashboard
cd proyek_ecommerce_dashboard
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run steamlit app
```
streamlit run dashboard.py
```