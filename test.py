import psutil
import time
import logging
import csv
import sqlite3
from flask import Flask, jsonify, request
from threading import Thread

# Flask app setup
app = Flask(__name__)
url_timestamp = {}
url_viewtime = {}
prev_url = ""

# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler('network_usage_and_browsing_activity.log')
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set up SQLite database connection
conn = sqlite3.connect('network_logs.db', check_same_thread=False)
cursor = conn.cursor()

# Create network usage and browsing activity tables
cursor.execute('''CREATE TABLE IF NOT EXISTS network_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    bytes_sent INTEGER,
    bytes_recv INTEGER
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS browsing_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    time_spent INTEGER
)''')
conn.commit()

# Open CSV files for logging
csv_file = open('network_usage.csv', mode='a', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Timestamp', 'Bytes Sent', 'Bytes Received'])

browsing_csv_file = open('browsing_activity.csv', mode='a', newline='')
browsing_csv_writer = csv.writer(browsing_csv_file)
browsing_csv_writer.writerow(['Timestamp', 'URL', 'Time Spent'])

# Function to track network usage and log browsing activity
def track_network_usage():
    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent
    bytes_recv = net_io.bytes_recv

    while True:
        time.sleep(1)
        net_io = psutil.net_io_counters()
        bytes_sent_diff = net_io.bytes_sent - bytes_sent
        bytes_recv_diff = net_io.bytes_recv - bytes_recv
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        # Log to file
        logger.info(f"Bytes Sent: {bytes_sent_diff}, Bytes Received: {bytes_recv_diff}")

        # Log to CSV
        csv_writer.writerow([timestamp, bytes_sent_diff, bytes_recv_diff])
        csv_file.flush()

        # Log to SQLite database
        cursor.execute('INSERT INTO network_usage (timestamp, bytes_sent, bytes_recv) VALUES (?, ?, ?)',
                       (timestamp, bytes_sent_diff, bytes_recv_diff))
        conn.commit()

# Flask routes to handle browsing activity
def url_strip(url):
    if "http://" in url or "https://" in url:
        url = url.replace("https://", '').replace("http://", '').replace('\"', '')
    if "/" in url:
        url = url.split('/', 1)[0]
    return url

@app.route('/send_url', methods=['POST'])
def send_url():
    resp_json = request.get_data()
    params = resp_json.decode()
    url = params.replace("url=", "")
    print("Currently viewing: " + url_strip(url))
    parent_url = url_strip(url)

    global url_timestamp
    global url_viewtime
    global prev_url

    # Initialize view time for the current URL if not already done
    if parent_url not in url_viewtime:
        url_viewtime[parent_url] = 0

    # If the user was previously viewing a tab, log the time spent on that tab
    if prev_url and prev_url in url_timestamp:
        time_spent = int(time.time() - url_timestamp[prev_url])
        url_viewtime[prev_url] += time_spent

        # Log browsing activity to SQLite and CSV
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO browsing_activity (url, time_spent) VALUES (?, ?)', (prev_url, time_spent))
        conn.commit()
        browsing_csv_writer.writerow([timestamp, prev_url, time_spent])
        browsing_csv_file.flush()

        print(f"Time spent on {prev_url}: {time_spent} seconds")

    # Record the timestamp for the new tab
    url_timestamp[parent_url] = int(time.time())
    prev_url = parent_url

    print("Final timestamps: ", url_timestamp)
    print("Final viewtimes: ", url_viewtime)

    return jsonify({'message': 'success!'}), 200

@app.route('/quit_url', methods=['POST'])
def quit_url():
    resp_json = request.get_data()
    params = resp_json.decode()
    url = params.replace("url=", "")
    parent_url = url_strip(url)

    global url_timestamp
    global url_viewtime
    global prev_url

    if parent_url in url_timestamp:
        # Calculate the time spent on the tab being closed
        time_spent = int(time.time() - url_timestamp[parent_url])
        url_viewtime[parent_url] += time_spent

        # Log browsing activity to SQLite and CSV
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO browsing_activity (url, time_spent) VALUES (?, ?)', (parent_url, time_spent))
        conn.commit()
        browsing_csv_writer.writerow([timestamp, parent_url, time_spent])
        browsing_csv_file.flush()

        print(f"Time spent on {parent_url} before closing: {time_spent} seconds")

        # Remove the closed tab from the timestamp dictionary
        del url_timestamp[parent_url]

    # Reset prev_url after tab closure
    prev_url = ''

    return jsonify({'message': 'quit success!'}), 200

# Start network tracking and Flask app in parallel
if __name__ == "__main__":
    # Start the network usage tracking in a separate thread
    network_thread = Thread(target=track_network_usage)
    network_thread.daemon = True
    network_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
