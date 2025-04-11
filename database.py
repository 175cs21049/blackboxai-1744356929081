import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_file="attendance.db"):
        self.db_file = db_file
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            employee_id TEXT UNIQUE NOT NULL,
            face_encoding TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create attendance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            check_in TIMESTAMP,
            check_out TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        conn.commit()
        conn.close()

    def register_user(self, full_name, email, employee_id, face_encoding):
        """Register a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
            INSERT INTO users (full_name, email, employee_id, face_encoding)
            VALUES (?, ?, ?, ?)
            ''', (full_name, email, employee_id, json.dumps(face_encoding)))
            
            conn.commit()
            return {"status": "success", "user_id": cursor.lastrowid}
        except sqlite3.IntegrityError as e:
            return {"status": "error", "message": "Email or Employee ID already exists"}
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return dict(user)
        return None

    def get_all_face_encodings(self):
        """Get all users' face encodings for recognition"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, face_encoding FROM users')
        encodings = cursor.fetchall()
        conn.close()

        return {row['id']: json.loads(row['face_encoding']) for row in encodings}

    def mark_attendance(self, user_id, attendance_type):
        """Mark attendance (check-in or check-out)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        current_time = datetime.now()
        today = current_time.date()

        try:
            # Check if attendance record exists for today
            cursor.execute('''
            SELECT * FROM attendance 
            WHERE user_id = ? AND date = ?
            ''', (user_id, today))
            
            record = cursor.fetchone()

            if attendance_type == 'check_in':
                if record and record['check_in']:
                    return {"status": "error", "message": "Already checked in today"}
                
                if not record:
                    cursor.execute('''
                    INSERT INTO attendance (user_id, date, check_in)
                    VALUES (?, ?, ?)
                    ''', (user_id, today, current_time))
                else:
                    cursor.execute('''
                    UPDATE attendance 
                    SET check_in = ?
                    WHERE user_id = ? AND date = ?
                    ''', (current_time, user_id, today))

            elif attendance_type == 'check_out':
                if not record or not record['check_in']:
                    return {"status": "error", "message": "Must check in first"}
                if record['check_out']:
                    return {"status": "error", "message": "Already checked out today"}

                cursor.execute('''
                UPDATE attendance 
                SET check_out = ?
                WHERE user_id = ? AND date = ?
                ''', (current_time, user_id, today))

            conn.commit()
            return {"status": "success"}

        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def get_attendance_history(self, user_id, limit=30):
        """Get attendance history for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM attendance 
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ?
        ''', (user_id, limit))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history

    def get_today_attendance(self, user_id):
        """Get today's attendance status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().date()

        cursor.execute('''
        SELECT * FROM attendance 
        WHERE user_id = ? AND date = ?
        ''', (user_id, today))

        record = cursor.fetchone()
        conn.close()

        return dict(record) if record else None
