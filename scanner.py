import cv2
from pyzbar.pyzbar import decode
from db import get_connection


def mark_attendance(participant_id, event_id):

    conn = get_connection()
    cur = conn.cursor()

    # Check if already marked
    cur.execute("""
        SELECT * FROM attendance
        WHERE participant_id = %s
        AND event_id = %s
    """, (participant_id, event_id))

    result = cur.fetchone()

    if result:
        print("Attendance already marked!")
    else:
        cur.execute("""
            INSERT INTO attendance(
                participant_id,
                event_id,
                status
            )
            VALUES(%s, %s, 'Present')
        """, (participant_id, event_id))

        conn.commit()

        print("Attendance Marked Successfully!")

    cur.close()
    conn.close()


camera = cv2.VideoCapture(0)
print("camera opened",camera.isOpened())

print("Press Q to quit scanner")

while True:

    success, frame = camera.read()

    for qr in decode(frame):

        data = qr.data.decode('utf-8')

        print("QR Data:", data)

        participant_id, event_id = data.split(',')

        mark_attendance(
            int(participant_id),
            int(event_id)
        )

        # Avoid repeated scans
        cv2.waitKey(2000)

    cv2.imshow("QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
