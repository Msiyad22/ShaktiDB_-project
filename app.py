from flask import Flask, render_template, request, redirect
from db import get_connection
import os
import qrcode
import pandas as pd
from flask import send_file

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():

    if request.method == 'POST':

        event_name = request.form['event_name']
        event_date = request.form['event_date']
        venue = request.form['venue']

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO events(event_name, event_date, venue)
            VALUES(%s, %s, %s)
            """,
            (event_name, event_date, venue)
        )

        conn.commit()

        cur.close()
        conn.close()

        return redirect('/')

    return render_template('create_event.html')


@app.route('/register', methods=['GET', 'POST'])
def register():

    conn = get_connection()
    cur = conn.cursor()

    # Fetch all events
    cur.execute("""
        SELECT event_id, event_name, event_date
        FROM events
    """)
    events = cur.fetchall()

    if request.method == 'POST':

        name = request.form["name"]
        email = request.form["email"]
        department = request.form["department"]
        event_id = request.form["event_id"]

        # Insert participant
        cur.execute("""
            INSERT INTO participants(name, email, department)
            VALUES(%s, %s, %s)
            RETURNING participant_id
        """, (name, email, department))

        participant_id = cur.fetchone()[0]

        # Generate QR data
        qr_data = f"{participant_id},{event_id}"

        # Generate QR image
        img = qrcode.make(qr_data)

        filename = f"{participant_id}_{event_id}.png"
        filepath = os.path.join("static/qr", filename)

        img.save(filepath)

        # Save registration
        cur.execute("""
            INSERT INTO registration(
                participant_id,
                event_id,
                qr_path
            )
            VALUES(%s, %s, %s)
        """, (
            participant_id,
            event_id,
            filepath
        ))

        conn.commit()

        cur.close()
        conn.close()

        return render_template(
            "success.html",
            qr_path="/" + filepath
        )

    cur.close()
    conn.close()

    return render_template(
        "register.html",
        events=events
    )

from collections import defaultdict

@app.route("/report")
def report():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.event_name,
            p.name,
            p.email,
            p.department,
            a.checking_time,
            a.status
        FROM attendance a
        JOIN participants p
            ON a.participant_id = p.participant_id
        JOIN events e
            ON a.event_id = e.event_id
        ORDER BY e.event_name;
    """)

    records = cur.fetchall()

    grouped = defaultdict(list)

    for row in records:
        grouped[row[0]].append(row)

    report = []

    for event, rows in grouped.items():

        total = len(rows)
        present = sum(1 for r in rows if r[5] == "Present")

        percentage = round((present / total) * 100, 2) if total else 0

        report.append({
            "event": event,
            "total": total,
            "present": present,
            "percentage": percentage,
            "rows": rows
        })

    cur.close()
    conn.close()

    return render_template("report.html", report=report)


@app.route('/export')
def export():

    conn = get_connection()

    query = """

    SELECT
        p.name,
        p.email,
        e.event_name,
        a.checking_time,
        a.status

    FROM attendance a

    JOIN participants p
    ON a.participant_id = p.participant_id

    JOIN events e
    ON a.event_id = e.event_id

    """

    df = pd.read_sql(query, conn)

    filename = "attendance_report.csv"

    df.to_csv(filename, index=False)

    conn.close()

    return send_file(
        filename,
        as_attachment=True
    )
    
    
if __name__ == '__main__':
    app.run(debug=True)
