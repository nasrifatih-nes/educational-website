import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nasrifatih_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///educational_platform.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

class ContentItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, default=0.0)
    is_subscription_required = db.Column(db.Boolean, default=False)
    file_source_type = db.Column(db.String(20), default='local')
    file_path_or_url = db.Column(db.String(500), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    items = ContentItem.query.all()
    return render_template('index.html', items=items)

@app.route('/lessons')
def lessons():
    items = ContentItem.query.all()
    return render_template('lessons.html', items=items)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        level = request.form.get('level')
        description = request.form.get('description')
        file_type = request.form.get('file_type')
        price = float(request.form.get('price', 0.0))
        is_sub = True if request.form.get('is_subscription_required') == 'on' else False
        
        source_type = request.form.get('file_source_type')
        file_url = ""

        if source_type == 'local':
            file = request.files.get('local_file')
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_url = url_for('static', filename=f'uploads/{filename}')
        else:
            file_url = request.form.get('drive_url', '')

        new_item = ContentItem(
            title=title,
            category=category,
            level=level,
            description=description,
            file_type=file_type,
            price=price,
            is_subscription_required=is_sub,
            file_source_type=source_type,
            file_path_or_url=file_url
        )
        db.session.add(new_item)
        db.session.commit()
        flash('تمت إضافة العنصر بنجاح!', 'success')
        return redirect(url_for('admin'))

    items = ContentItem.query.all()
    return render_template('admin.html', items=items)

@app.route('/admin/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = ContentItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('تم حذف العنصر بنجاح!', 'danger')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
