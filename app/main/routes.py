import os
import cv2
import numpy as np
import json # <--- Add this import for the chart data
from io import BytesIO
from datetime import date # <--- Add this import for today's date
from flask import render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_paginate import Pagination, get_page_parameter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import func, cast, Date # <--- Add these imports for database functions
from app import db, dr_model, detector, CLASS_LABELS, IMG_SIZE, DET_SIZE, THRESHOLD
from app.main import bp
from app.models import Patient
from app.forms import PatientCheckForm

# is_retinal_image and preprocess functions remain unchanged...
def is_retinal_image(path: str) -> bool:
    img = cv2.imread(path)
    if img is None:
        return False
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, DET_SIZE) / 255.0
    p_non = float(detector.predict(img[None])[0, 0])
    return (1 - p_non) > THRESHOLD

def preprocess(path: str) -> np.ndarray:
    img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, IMG_SIZE) / 255.0
    return img[None]


# --- THIS IS THE UPDATED HOME/DASHBOARD ROUTE ---
@bp.route('/')
@bp.route('/home')
@login_required
def home():
    # Query for dashboard statistics
    total_patients = db.session.query(func.count(Patient.id)).scalar()
    today_s_analyses = db.session.query(func.count(Patient.id)).filter(cast(Patient.created_at, Date) == date.today()).scalar()
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

    # Query for chart data
    diagnosis_distribution = db.session.query(Patient.dr_result, func.count(Patient.dr_result)).group_by(Patient.dr_result).all()
    
    chart_labels = [result[0].replace('_', ' ') if result[0] else 'N/A' for result in diagnosis_distribution]
    chart_data = [result[1] for result in diagnosis_distribution]

    return render_template(
        'home.html', 
        title='Dashboard',
        total_patients=total_patients,
        today_s_analyses=today_s_analyses,
        recent_patients=recent_patients,
        chart_labels=json.dumps(chart_labels),
        chart_data=json.dumps(chart_data)
    )

# --- All other routes (check, patient_list, etc.) remain unchanged below this point ---
@bp.route('/check', methods=['GET', 'POST'])
@login_required
def check():
    form = PatientCheckForm()
    if form.validate_on_submit():
        file = form.image.data
        fname = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
        file.save(save_path)

        if not is_retinal_image(save_path):
            flash('Please upload a valid fundus image.', 'warning')
            return redirect(url_for('main.check'))

        preds = dr_model.predict(preprocess(save_path))[0]
        idx = np.argmax(preds)
        top_label = CLASS_LABELS[idx]
        top_conf = f"{preds[idx] * 100:.2f}%"
        probs = [{'label': lbl, 'conf': f"{p * 100:.2f}%"} for lbl, p in zip(CLASS_LABELS, preds)]

        p = Patient(
            name=form.name.data,
            date_of_birth=form.date_of_birth.data,
            medical_history=form.medical_history.data,
            symptoms=form.symptoms.data,
            image_filename=fname,
            dr_result=top_label,
            dr_confidence=float(preds[idx]),
            user_id=current_user.id
        )
        db.session.add(p)
        db.session.commit()

        return render_template('check_result.html', top_label=top_label, top_conf=top_conf, filename=fname, probs=probs)
    return render_template('check.html', form=form, title='New Analysis')

@bp.route('/patients')
@login_required
def patient_list():
    search = request.args.get('q', '', type=str)
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10

    query = Patient.query
    if search:
        query = query.filter(Patient.name.ilike(f'%{search}%'))

    total = query.count()
    patients = query.order_by(Patient.created_at.desc()) \
        .offset((page - 1) * per_page).limit(per_page).all()

    pagination = Pagination(
        page=page, per_page=per_page, total=total,
        css_framework='bootstrap5', record_name='patients'
    )

    return render_template(
        'patient_list.html',
        patients=patients,
        pagination=pagination,
        search=search
    )

@bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patient_detail.html', patient=patient)

@bp.route('/patients/<int:patient_id>/report')
@login_required
def download_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"Patient Report: {patient.name}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, f"Date of Birth: {patient.date_of_birth.strftime('%d %B, %Y')}")
    if patient.user:
        pdf.drawString(50, height - 100, f"Recorded by: {patient.user.email}")
        y_offset = 20
    else:
        y_offset = 0

    pdf.drawString(50, height - 100 - y_offset, f"Medical History: {patient.medical_history or '—'}")
    pdf.drawString(50, height - 120 - y_offset, f"Symptoms: {patient.symptoms or '—'}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 160 - y_offset, "Analysis Result")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 180 - y_offset, f"DR Diagnosis: {patient.dr_result or '—'}")
    conf_text = f"{patient.dr_confidence * 100:.2f}%" if patient.dr_confidence is not None else "—"
    pdf.drawString(50, height - 200 - y_offset, f"Confidence: {conf_text}")

    if patient.image_filename:
        img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], patient.image_filename)
        pdf.drawImage(img_path, 50, height - 420 - y_offset, width=200, preserveAspectRatio=True, mask='auto')

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"report_{patient.id}.pdf",
        mimetype='application/pdf'
    )