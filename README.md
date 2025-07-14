#  Smart Inventory Forecasting App

A Flask-based intelligent inventory management system that uses **LSTM deep learning models** to forecast future product demand, analyze stock sufficiency, and automatically suggest reorder quantities. Designed with a **visual dashboard**, **email integration**, and **role-based access**, this tool is ideal for businesses aiming to reduce stockouts and optimize inventory operations.



##  Project Overview

Traditional inventory systems often rely on fixed rules or manual inputs. This app combines **AI/ML forecasting** with real-time stock data to enable:

-  Dynamic stock alerts based on lead time
-  30-day product demand forecasting using LSTM
-  One-click reorder via email to vendors
-  Visual dashboards for quick decision-making
-  Secure login with protected views

---

##  Key Features


| **LSTM Demand Forecasting** | Predicts 30 days of sales for each product |
| **Stock Sufficiency Alerts** | Alerts when inventory is below safe level (based on lead time) |
| **Auto Reorder Workflow** | Enter quantity + delivery date → Email sent to vendor |
| **Reorder Suggestions** | System suggests quantity required to meet a given number of days |
| **Visual Dashboard** | Product-wise view: status, forecast chart, days covered, alerts |
| **Login System** | Simple hardcoded user login with protected views |
| **Excel Integration** | Reads inventory, sales, and vendor details from Excel |
| **Expandable** | Designed for future add-ons like analytics, chatbots, or API support |



##  Tech Stack

- Frontend: HTML, CSS (Bootstrap), JavaScript (AJAX)
- Backend: Flask
- Model: LSTM (Keras), Scikit-learn (scaler)
- Data: Excel-based (`sales_inventory_data.xlsx`)
- Email: SMTP with Gmail
- Authentication: Session-based login

---

##  Machine Learning

- LSTM model trained per product using past 60 days of data
- Scaler used: `MinMaxScaler` (saved via joblib)
- Evaluation: RMSE, MSE on validation data
- Can be extended with:
  - Model comparison (ARIMA, XGBoost, etc.)
  - Hyperparameter tuning
  - Retraining pipeline



 How to Run Locally

git clone https://github.com/india134/Sales_Forecasting_Inventory_Mgt.git
cd Sales_Forecasting_Inventory_Mgt

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
