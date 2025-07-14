# Updated app.py with forecasting, lead time, alert, reorder, email, quantity for given days, and login system
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import pandas as pd
import numpy as np
import joblib
from keras.models import load_model
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # required for session
@app.before_request
def enforce_login():
    # This will protect all routes unless explicitly excluded
    allowed_routes = ['login', 'static']
    if 'logged_in' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

EXCEL_PATH = "sales_inventory_data.xlsx"
product_sheets = [f"Product_{i}" for i in range(1, 6)]
inventory_sheet = "Inventory"
product_info_sheet = "Product_Info"

models = {}
scalers = {}

# Login credentials (hardcoded)
USERNAME = "admin"
PASSWORD = "password123"

# Decorator to protect views
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('overview'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

for product in product_sheets:
    try:
        models[product] = load_model(f"models/model_{product}.keras")
        scalers[product] = joblib.load(f"scalers/scaler_{product}.pkl")
        print(f"✅ Loaded {product} model and scaler")
    except Exception as e:
        print(f"❌ Error loading model/scaler for {product}: {e}")

def get_last_60_scaled(product):
    df = pd.read_excel(EXCEL_PATH, sheet_name=product)
    df['Units_Sold'] = pd.to_numeric(df['Units_Sold'], errors='coerce')
    df = df.dropna(subset=['Units_Sold'])
    if len(df) < 60:
        raise ValueError(f"Insufficient data: Only {len(df)} rows found for {product}")
    df = df.sort_values('Date')
    last_60 = df['Units_Sold'].values[-60:].reshape(1, 60, 1)
    scaler = scalers[product]
    return scaler.transform(last_60.reshape(-1, 1)).reshape(1, 60, 1)

def get_forecast(product):
    model = models[product]
    scaled_input = get_last_60_scaled(product)
    forecast_scaled = model.predict(scaled_input)
    forecast = scalers[product].inverse_transform(forecast_scaled.reshape(-1, 1)).flatten()
    return forecast.tolist()

def compute_days_covered(current_stock, forecast):
    days = 0
    remaining = current_stock
    for units in forecast:
        if remaining >= units:
            remaining -= units
            days += 1
        else:
            break
    return days

def get_lead_time(product):
    info_df = pd.read_excel(EXCEL_PATH, sheet_name=product_info_sheet)
    row = info_df[info_df['Product_ID'] == product]
    if not row.empty:
        return int(row['Lead Time'].values[0])
    return 7

@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", products=product_sheets)

@app.route("/status", methods=["POST"])
@login_required
def get_status():
    data = request.get_json()
    product = data.get("product")
    days_input = data.get("days")

    try:
        forecast = get_forecast(product)
        inv_df = pd.read_excel(EXCEL_PATH, sheet_name=inventory_sheet)
        inv_row = inv_df[inv_df['Product_ID'] == product]
        if inv_row.empty:
            raise ValueError(f"{product} not found in Inventory sheet")
        current_stock = float(inv_row['Current_Stock'].values[0])

        lead_time = get_lead_time(product)
        days_covered = compute_days_covered(current_stock, forecast)

        reorder_in_days = max(days_covered - lead_time, 0)
        alert = days_covered <= lead_time

        alert_text = "Stock is Sufficient. No Reorder Required." if not alert else f"Reorder Required! You have only {days_covered} days of stock left."

        quantity_needed = 0
        if days_input:
            try:
                days_input = int(days_input)
                quantity_needed = int(sum(forecast[:days_input]))
            except:
                quantity_needed = 0

        suggested_reorder_qty = int(sum(forecast[:lead_time + 1]))

        return jsonify({
            "forecast": forecast,
            "current_stock": int(current_stock),
            "days_covered": int(days_covered),
            "reorder_in_days": int(reorder_in_days),
            "alert": alert,
            "lead_time": lead_time,
            "alert_text": alert_text,
            "quantity_needed": quantity_needed,
            "suggested_quantity": suggested_reorder_qty
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/send_email", methods=["POST"])
@login_required
def send_email():
    data = request.get_json()
    product = data.get("product")
    quantity = int(data.get("quantity"))
    delivery_date = data.get("delivery_date")

    try:
        info_df = pd.read_excel(EXCEL_PATH, sheet_name=product_info_sheet)
        row = info_df[info_df['Product_ID'] == product].iloc[0]
        vendor_name = row['Vendor_Name']
        vendor_email = row['Vendor_Email']

        subject = f"Reorder Request for {product}"
        body = f"""
Dear {vendor_name},

We would like to place a reorder for the following product:

- Product: {product}
- Quantity: {quantity} units
- Expected Delivery Date: {delivery_date}

Please confirm the delivery schedule.

Regards,
Inventory Management System
        """
        sender_email = "your_email@example.com"
        sender_password = "your_app_password"

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = vendor_email
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)

        return jsonify({"success": True, "message": "Email sent successfully."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/overview")
@login_required
def overview():
    try:
        data = []
        inv_df = pd.read_excel(EXCEL_PATH, sheet_name=inventory_sheet)
        info_df = pd.read_excel(EXCEL_PATH, sheet_name=product_info_sheet)

        for product in product_sheets:
            forecast = get_forecast(product)
            stock_row = inv_df[inv_df['Product_ID'] == product]
            lead_row = info_df[info_df['Product_ID'] == product]
            if stock_row.empty or lead_row.empty:
                continue
            current_stock = float(stock_row['Current_Stock'].values[0])
            lead_time = int(lead_row['Lead Time'].values[0])
            days_covered = compute_days_covered(current_stock, forecast)
            alert = days_covered <= lead_time
            stockout_date = (datetime.today() + timedelta(days=days_covered)).strftime("%Y-%m-%d")

            data.append({
                "product": product,
                "days_covered": days_covered,
                "lead_time": lead_time,
                "alert": alert,
                "alert_text": "Reorder Now" if alert else "Stock is Sufficient",
                "stockout_date": stockout_date
            })
        return render_template("overview.html", data=data)

    except Exception as e:
        return f"Error generating overview: {e}"

if __name__ == "__main__":
    app.run(debug=True)





