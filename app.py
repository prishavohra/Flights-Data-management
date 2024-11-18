from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import random

app = Flask(__name__, template_folder='templates')

# MySQL configurations
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Prikshit@0401',
    'database': 'projectsql'
}

# Secret key for session management (For Flash messages and session handling)
app.secret_key = 'your_secret_key'

# Route for home or login page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Establish a connection to the MySQL database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Query to check if the username and password match an entry in the Users table
        cursor.execute("SELECT * FROM Users WHERE Username = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            # Check if the password matches
            if user[2] == password:  # Assuming password is at index 2
                user_role = user[3]  # Assuming user role is at index 3
                print(f"Logged in as: {user_role}")  # Debugging line to print user role
                
                # Store user session data
                session['user_id'] = user[0]  # Assuming user ID is at index 0
                session['user_role'] = user_role  # Store user role in session
                
                # Redirect based on the role of the user
                if user_role == 'customer':
                    return redirect(url_for('customer_dashboard'))
                elif user_role == 'employee':
                    return redirect(url_for('employee_dashboard'))
                else:
                    flash('Invalid role. Please try again.', 'danger')
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('Username not found. Please try again.', 'danger')
        
        cursor.close()
        conn.close()
    
    return render_template('login.html')

# Route for customer dashboard



@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Check user credentials in database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Users WHERE Username = %s AND Password = %s", (username, password))
    user = cursor.fetchone()

    if user:
        user_role = user[3]  # Assuming user role is in index 3
        session['user_id'] = user[0]  # Store user ID in session
        session['user_role'] = user_role  # Store user role in session
        
        # Redirect based on the role of the user
        if user_role == 'customer':
            return redirect(url_for('customer_dashboard'))
        elif user_role == 'employee':
            return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid role")
            return redirect(url_for('home'))
    else:
        flash("Invalid username or password")
        return redirect(url_for('home'))


@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    return render_template('customer_dashboard.html')

@app.route('/flight_search', methods=['GET', 'POST'])
def flight_search():
    if request.method == 'POST':
        departure_airport = request.form['departure_airport']
        arrival_airport = request.form['arrival_airport']

        # Query flights based on city codes (departure and arrival)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM Flights
            WHERE Departure_airport_code = %s AND Arrival_airport_code = %s 
        """, (departure_airport, arrival_airport))

        flights = cursor.fetchall()

        # Add random prices to the flights data
        flight_details = []
        for flight in flights:
            flight_id, flight_number, dep_airport, arr_airport, dep_time, arr_time, duration, status, available_seats, aircraft_id = flight
            random_price = random.randint(1000, 8000)  # Random price between 1000 to 8000
            flight_details.append({
                'flight_id': flight_id,
                'flight_number': flight_number,
                'departure_airport': dep_airport,
                'arrival_airport': arr_airport,
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'price': random_price
            })

        cursor.close()
        conn.close()

        return render_template('flight_results.html', flights=flight_details)

    return render_template('flight_search.html')





from datetime import datetime



@app.route('/select_services', methods=['POST'])
def select_services():
    if request.method == 'POST':
        print(request.form)  # Debug: print the entire form data to see what is passed

        try:
            flight_id = request.form['flight_id']
            
            # Set a fixed price for the flight here
            flight_price = 3500  # Example fixed price, modify as per your requirement
            
        except KeyError as e:
            print(f"Error: {e}")
            return f"Error: Missing flight_id or other data in form: {e}"

        selected_services = request.form.getlist('services')  # Get list of selected services
        total_price = 5785  # Start with the base flight price
        
        # Define service prices
        service_prices = {
            '1': 500, '9': 300, '5': 600, '2': 400, '4': 800,
            '10': 700, '3': 200, '8': 1000, '6': 900, '7': 150
        }

        # Calculate the total price of selected services
        total_service_price = sum(service_prices.get(service, 0) for service in selected_services)

        # Final total price = flight price + selected services
        total_price = 5785

        # Generate or fetch booking_id as needed
        # Ensure this is implemented

        # Store the total price, flight_id, and selected services in the session
        session['total_price'] = total_price
        session['flight_id'] = flight_id
        session['selected_services'] = selected_services
        session['booking_id'] = 180 # Ensure the booking ID is included

        # Redirect to the payment page
        return redirect(url_for('payment'))



@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'total_price' not in session:
        return redirect(url_for('home'))

    total_price = session['total_price']

    if request.method == 'POST':
        try:
            payment_method = request.form['payment_method']
        except KeyError:
            flash('Payment method is required.', 'danger')
            return redirect(url_for('payment'))  # Redirect to the same page if payment method is missing

        # Process the payment (integration with payment gateway would go here)

        # After successful payment, update the booking status in the database
        booking_id = session.get('booking_id')  # Ensure that booking_id is stored in the session
        if not booking_id:
            flash('Booking ID not found.', 'danger')
            return redirect(url_for('home'))

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Update payment status in the database (assuming successful payment)
        cursor.execute("""
            UPDATE Bookings
            SET Payment_id = %s, Status = 'confirmed'
            WHERE Booking_id = %s
        """, (payment_method, booking_id))  # Update payment method and confirm booking

        conn.commit()
        cursor.close()
        conn.close()

        flash('Booking confirmed! Your payment has been successfully processed.', 'success')
        
        # Redirect to the Thank You page after successful payment
        return redirect(url_for('thank_you'))  # Ensure 'thank_you' route exists

    return render_template('payment.html')

@app.route('/view_current_flights')
def view_current_flights():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    customer_id = session['user_id']

    # Fetch the current booked flights from the Bookings table
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.Booking_id, f.Flight_number, f.Departure_airport_code, f.Arrival_airport_code, b.Status, f.Departure_time, f.Arrival_time
        FROM Bookings b
        JOIN Flights f ON b.Flight_id = f.Flight_id
        WHERE b.Customer_id = %s AND b.Status = 'booked'
    """, (customer_id,))
    
    current_flights = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('current_flights.html', flights=current_flights)
@app.route('/view_travel_history')
def view_travel_history():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    customer_id = session['user_id']

    # Fetch the travel history (flights where status is not 'booked')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.Booking_id, f.Flight_number, f.Departure_airport_code, f.Arrival_airport_code, b.Status, f.Departure_time, f.Arrival_time
        FROM Bookings b
        JOIN Flights f ON b.Flight_id = f.Flight_id
        WHERE b.Customer_id = %s AND b.Status != 'booked'
    """, (customer_id,))

    travel_history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('travel_history.html', flights=travel_history)
@app.route('/about_customer')
def about_customer():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    customer_id = session['user_id']

    # Fetch all information about the customer
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Customer_id  ,First_name ,Last_name ,Age ,City ,State ,Country ,Postal_code ,Customer_type,Loyalty_points
        FROM Customers
        WHERE Customer_id = %s
    """, (customer_id,))

    customer_info = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('about_customer.html', customer=customer_info)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')  # This will render a thank you page
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        flight_id = request.form['flight_id']
        rating = request.form['rating']
        comments = request.form['comments']

        # Insert feedback into the Feedback table
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Feedback (Customer_id, Flight_id, Rating, Comments, Feedback_date)
            VALUES (%s, %s, %s, %s, NOW())
        """, (session['user_id'], flight_id, rating, comments))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('customer_dashboard'))

    else:
        # Fetch user's past flights for feedback
        customer_id = session['user_id']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT f.Flight_id, f.Flight_number, f.Departure_airport_code, f.Arrival_airport_code
            FROM Bookings b
            JOIN Flights f ON b.Flight_id = f.Flight_id
            WHERE b.Customer_id = %s AND b.Status != 'booked'
        """, (customer_id,))

        flights = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('feedback.html', flights=flights)



# Route for logout (end session)
@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    return redirect(url_for('home'))  # Redirect to login page



@app.route('/view_all_schedules')
def view_all_schedules():
    if 'user_id' not in session or session['user_role'] != 'employee':
        return redirect(url_for('home'))

    # Fetch all schedules
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.Flight_number, e.First_name, e.Last_name, s.shift_start_time, s.shift_end_time
        FROM Schedules s
        JOIN Employees e ON s.Employee_id = e.Employee_id
        JOIN Flights f ON s.Flight_id = f.Flight_id
        ORDER BY f.Flight_number, s.shift_start_time
    """)

    schedules = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_all_schedules.html', schedules=schedules)

@app.route('/view_personal_schedule')
def view_personal_schedule():
    if 'user_id' not in session or session['user_role'] != 'employee':
        return redirect(url_for('home'))

    employee_id = session['user_id']

    # Fetch personal schedule for logged-in employee
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.schedule_id, f.flight_number, s.shift_start_time, s.shift_end_time
        FROM Schedules s
        JOIN Flights f ON s.flight_id = f.flight_id
        WHERE s.employee_id = %s
    """, (employee_id,))

    personal_schedule = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_personal_schedule.html', schedules=personal_schedule)

@app.route('/about_employee')
def about_employee():
    if 'user_id' not in session or session['user_role'] != 'employee':
        return redirect(url_for('home'))

    employee_id = session['user_id']

    # Fetch employee information
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT employee_id, First_name, role, department, benefits
        FROM Employees
        WHERE employee_id = %s
    """, (employee_id,))

    employee_info = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('about_employee.html', employee=employee_info)

@app.route('/logout_employee')
def logout_employee():
    session.clear()  # Clear session data
    return redirect(url_for('home'))  # Redirect to login page



@app.route('/employee_dashboard')
@app.route('/employee_dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['user_role'] != 'employee':
        return redirect(url_for('home'))  # Redirect to home if not an employee
    return render_template('employee_dashboard.html')
if __name__ == "__main__":
    app.run(debug=True)
