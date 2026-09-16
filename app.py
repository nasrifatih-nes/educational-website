from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os

app = Flask(__name__)

# إعداد مسار حفظ الملفات المرفوعة
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# قاعدة بيانات مؤقتة لتخزين الدروس
lessons_db = []

# --- واجهات التلاميذ العامة ---
@app.route('/')
def index():
    return render_template('index.html', lessons=lessons_db)

@app.route('/lessons')
def student_lessons():
    return render_template('lessons.html', lessons=lessons_db)

@app.route('/exercises')
def student_exercises():
    return render_template('exercises.html')

@app.route('/exams')
def student_exams():
    return render_template('exams.html')

# --- لوحة تحكم الأستاذ (الخاصة بك وحدك عبر رابط /admin) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        title = request.form.get('title')
        file = request.files.get('file')
        sub_type = request.form.get('sub_type')
        
        if file and title:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            lessons_db.append({
                'id': len(lessons_db) + 1,
                'title': title,
                'filename': filename,
                'sub_type': sub_type
            })
            return redirect(url_for('admin_dashboard'))
            
    return render_template('admin.html', lessons=lessons_db)

# مسار لتحميل الملفات المرفوعة
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)