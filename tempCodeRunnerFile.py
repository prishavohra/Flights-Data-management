from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# MySQL database configuration
db_config = {
    'user': 'root',
    'password': 'Prikshit@0401',
    'host': 'localhost',
    'database': 'projectsql'
}

# Function to generate a unique PNR
def generate_pnr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Route for the homepage (login page)
@app.route('/')
def index():
    return render_template('login.html')

# Route for login functionality
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Connect to the MySQL database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Check if the user exists and password is correct
    query = "SELECT User_id, User_role FROM Users WHERE Username = %s AND Password = %s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    if result:
        session['username'] = username
        session['user_id'] = result[0]
        session['role'] = result[1]

        if result[1] == 'employee':
            return redirect(url_for('employee_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    else:
        return "Login failed! Invalid username or password."

# Route for logout functionality
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))

# Employee Dashboard
@app.route('/employee_dashboard')
def employee_dashboard():
    if 'role' not in session or session['role'] != 'employee':
        return redirect(url_for('index'))  # Redirect to login if not employee

    # Fetch flight schedules (Employee-related functionality)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = "SELECT Flight_id, Flight_number, Departure_airport_code, Arrival_airport_code, Departure_time, Arrival_time FROM Flights"
    cursor.execute(query)
    flights = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('employee_dashboard.html', flights=flights)

# Customer Dashboard
@app.route('/customer_dashboard')
def customer_dashboard():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer

    # Customer dashboard with options
    return render_template('customer_dashboard.html')

# Booking Page (for customers)
@app.route('/book_flight_page', methods=['GET', 'POST'])
def book_flight_page():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer

    flights = []
    if request.method == 'POST':
        departure_city = request.form['departure_city']
        arrival_city = request.form['arrival_city']

        # Fetch available flights based on the departure and arrival cities
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = """SELECT Flight_id, Flight_number, Departure_airport_code, Arrival_airport_code, Departure_time, Arrival_time 
                   FROM Flights WHERE Departure_airport_code = %s AND Arrival_airport_code = %s AND Status = 'scheduled'"""
        cursor.execute(query, (departure_city, arrival_city))
        flights = cursor.fetchall()

        cursor.close()
        connection.close()

    # Pass the random module to the template
    return render_template('book_flight_page.html', flights=flights, random=random)

# Services Page (for selecting services)
@app.route('/services_page/<int:flight_id>', methods=['GET', 'POST'])
def services_page(flight_id):
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer

    if request.method == 'POST':
        selected_services = request.form.getlist('services')  # Get selected services as a list

        # Process the selected services (could be storing them in a booking or transaction record)
        print(f"Selected services for Flight {flight_id}: {selected_services}")
        return redirect(url_for('payment_page', flight_id=flight_id))

    # Fetch services available for the flight (for example, baggage, meals, etc.)
    services = ['Baggage', 'Meal', 'Extra legroom', 'Wi-Fi']  # Example services, modify as needed

    return render_template('services.html', flight_id=flight_id, services=services)

# Payment Page
@app.route('/payment_page/<int:flight_id>', methods=['GET', 'POST'])
def payment_page(flight_id):
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer

    if request.method == 'POST':
        payment_method = request.form['payment_method']
        print(f"Payment confirmed for Flight {flight_id} using {payment_method}")

        # Update the booking status to 'confirmed' or perform other payment-related actions here
        return render_template('payment_confirmation.html', flight_id=flight_id, payment_method=payment_method)

    return render_template('payment.html', flight_id=flight_id)

# Route for the complete_payment endpoint (Step 1)
@app.route('/complete_payment', methods=['POST'])
def complete_payment():
    payment_method = request.form['payment_method']
    flight_id = request.form['flight_id']

    # Perform payment processing logic
    print(f"Payment completed for Flight {flight_id} using {payment_method}")
    
    # You can add logic here to update booking status or perform other tasks
    
    return render_template('payment_confirmation.html', flight_id=flight_id, payment_method=payment_method)

# View Travel History Page
@app.route('/view_travel_history')
def view_travel_history():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer
    
    customer_id = session['user_id']
    
    # Fetch travel history (completed bookings)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """SELECT Flights.Flight_id, Flights.Flight_number, Flights.Departure_airport_code, Flights.Arrival_airport_code, 
                      Flights.Departure_time, Flights.Arrival_time 
               FROM Bookings 
               JOIN Flights ON Bookings.Flight_id = Flights.Flight_id
               WHERE Bookings.Customer_id = %s AND Bookings.Status = 'completed'"""
    cursor.execute(query, (customer_id,))
    travel_history = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('viewtravelhistory.html', travel_history=travel_history)

# View Current Flight Status Page
@app.route('/view_current_flight_status')
def view_current_flight_status():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer
    
    customer_id = session['user_id']
    
    # Fetch current flight status (booked flights)
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """SELECT Flights.Flight_id, Flights.Flight_number, Flights.Departure_airport_code, Flights.Arrival_airport_code, Flights.Status
               FROM Bookings 
               JOIN Flights ON Bookings.Flight_id = Flights.Flight_id
               WHERE Bookings.Customer_id = %s AND Bookings.Status = 'booked'"""
    cursor.execute(query, (customer_id,))
    current_flight_status = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('viewstatus.html', current_flight_status=current_flight_status)

# Leave Feedback Page
@app.route('/leave_feedback', methods=['GET', 'POST'])
def leave_feedback():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))  # Redirect to login if not customer

    if request.method == 'POST':
        feedback = request.form['feedback']
        rating = request.form['rating']
        customer_id = session['user_id']
        flight_id = request.form['flight_id']
        
        # Insert feedback into the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = """INSERT INTO Feedback (Rating, Comments, Feedback_date, Customer_id, Flight_id)
                   VALUES (%s, %s, CURDATE(), %s, %s)"""
        cursor.execute(query, (rating, feedback, customer_id, flight_id))
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for('customer_dashboard'))  # Redirect to dashboard after feedback submission

    # Fetch flights the customer can leave feedback for (completed flights)
    customer_id = session['user_id']
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """SELECT Flights.Flight_id, Flights.Flight_number, Flights.Departure_airport_code, Flights.Arrival_airport_code, 
                      Flights.Departure_time, Flights.Arrival_time 
               FROM Bookings 
               JOIN Flights ON Bookings.Flight_id = Flights.Flight_id 
               LEFT JOIN Feedback ON Flights.Flight_id = Feedback.Flight_id AND Bookings.Customer_id = Feedback.Customer_id
               WHERE Bookings.Customer_id = %s AND Bookings.Status = 'completed' AND Feedback.Feedback_id IS NULL"""
    cursor.execute(query, (customer_id,))
    flights = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('feedback.html', flights=flights)

if __name__ == '__main__':
    app.run(debug=True)
