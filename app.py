from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # جدول الدروس (subscription_type: free, pdf_sub, word_sub)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            subscription_type TEXT DEFAULT 'free'
        )
    ''')
    
    # جدول التمارين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            subscription_type TEXT DEFAULT 'free'
        )
    ''')
    
    # جدول الفروض والاختبارات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            level TEXT NOT NULL,
            semester TEXT NOT NULL,
            subject_source TEXT,
            subject_sub_type TEXT DEFAULT 'free',      -- اشتراك موضوع الفرض/الاختبار
            correction_source TEXT,
            correction_sub_type TEXT DEFAULT 'free'    -- اشتراك التصحيح النموذجي
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg']

@app.route('/')
def home():
    return render_template('index.html')

# --- إدارة الدروس ---
@app.route('/lessons', methods=['GET', 'POST'])
def lessons():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        sub_type = request.form['subscription_type']  # free, pdf_sub, word_sub
        file = request.files.get('file')
        
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ext = filename.rsplit('.', 1)[1].lower()
            file_type = 'image' if ext in ['png', 'jpg', 'jpeg'] else ext
            
            cursor.execute('INSERT INTO lessons (title, filename, file_type, subscription_type) VALUES (?, ?, ?, ?)',
                           (title, filename, file_type, sub_type))
            conn.commit()
        return redirect(url_for('lessons'))
        
    cursor.execute('SELECT * FROM lessons')
    lessons_list = cursor.fetchall()
    conn.close()
    return render_template('lessons.html', lessons=lessons_list)

@app.route('/delete_lesson/<int:lesson_id>')
def delete_lesson(lesson_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('lessons'))

# --- إدارة التمارين ---
@app.route('/exercises', methods=['GET', 'POST'])
def exercises():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        sub_type = request.form['subscription_type']
        file = request.files.get('file')
        
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ext = filename.rsplit('.', 1)[1].lower()
            file_type = 'image' if ext in ['png', 'jpg', 'jpeg'] else ext
            
            cursor.execute('INSERT INTO exercises (title, filename, file_type, subscription_type) VALUES (?, ?, ?, ?)',
                           (title, filename, file_type, sub_type))
            conn.commit()
        return redirect(url_for('exercises'))
        
    cursor.execute('SELECT * FROM exercises')
    exercises_list = cursor.fetchall()
    conn.close()
    return render_template('exercises.html', exercises=exercises_list)

@app.route('/delete_exercise/<int:ex_id>')
def delete_exercise(ex_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM exercises WHERE id = ?', (ex_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('exercises'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- بنك الفروض والاختبارات ---
@app.route('/exams', methods=['GET'])
def exams_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    selected_level = request.args.get('level', '')
    selected_semester = request.args.get('semester', '')
    selected_type = request.args.get('type', '')
    
    query = "SELECT * FROM exams WHERE 1=1"
    params = []
    
    if selected_level:
        query += " AND level = ?"
        params.append(selected_level)
    if selected_semester:
        query += " AND semester = ?"
        params.append(selected_semester)
    if selected_type:
        query += " AND type = ?"
        params.append(selected_type)
        
    cursor.execute(query, params)
    exams_list = cursor.fetchall()
    conn.close()
    
    levels = [
        "السنة الأولى جذع مشترك علوم وتكنولوجيا",
        "السنة الثانية علوم تجريبية",
        "السنة الثالثة علوم تجريبية",
        "السنة الثانية رياضيات",
        "السنة الثالثة رياضيات"
    ]
    semesters = ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"]
    
    return render_template('exams.html', exams=exams_list, levels=levels, semesters=semesters)

@app.route('/add_exam', methods=['GET', 'POST'])
def add_exam():
    if request.method == 'POST':
        title = request.form['title']
        ex_type = request.form['type']
        level = request.form['level']
        semester = request.form['semester']
        
        subject_sub_type = request.form['subject_sub_type']
        correction_sub_type = request.form['correction_sub_type']
        
        # معالجة الموضوع
        subject_source = ""
        if 'subject_file_upload' in request.files and request.files['subject_file_upload'].filename != '':
            file = request.files['subject_file_upload']
            if allowed_file(file.filename):
                filename = "sub_" + file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                subject_source = url_for('uploaded_file', filename=filename)
        elif request.form.get('subject_file_link'):
            subject_source = request.form.get('subject_file_link')
            
        # معالجة التصحيح
        correction_source = ""
        if 'correction_file_upload' in request.files and request.files['correction_file_upload'].filename != '':
            file = request.files['correction_file_upload']
            if allowed_file(file.filename):
                filename = "corr_" + file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                correction_source = url_for('uploaded_file', filename=filename)
        elif request.form.get('correction_file_link'):
            correction_source = request.form.get('correction_file_link')
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO exams (title, type, level, semester, subject_source, subject_sub_type, correction_source, correction_sub_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, ex_type, level, semester, subject_source, subject_sub_type, correction_source, correction_sub_type))
        conn.commit()
        conn.close()
        return redirect(url_for('exams_page'))
        
    levels = [
        "السنة الأولى جذع مشترك علوم وتكنولوجيا",
        "السنة الثانية علوم تجريبية",
        "السنة الثالثة علوم تجريبية",
        "السنة الثانية رياضيات",
        "السنة الثالثة رياضيات"
    ]
    semesters = ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"]
    return render_template('add_exam.html', levels=levels, semesters=semesters)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)