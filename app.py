from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Admin, Schedule, Promise, PromiseProgress, MeetingMinutes, Regulation, Program, Organization, Banner, Archive, ArchiveImage
from config import Config
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_file(file, subfolder='files'):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        file.save(save_path)
        return url_for('static', filename=f'uploads/{subfolder}/{filename}')
    return None

@app.route('/')
def index():
    # 배너 로직 강화: 모든 활성 배너 노출 (캐러셀)
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.is_event_banner.desc(), Banner.order.asc()).all()
    
    # 전반적인 공약 이행률 계산
    promises_list = Promise.query.all()
    promise_rate = int(sum(p.progress_rate for p in promises_list) / len(promises_list)) if promises_list else 0

    # 메인 페이지용 다가오는 일정 (2개)
    upcoming_schedules = Schedule.query.filter(Schedule.start_date >= datetime.now()).order_by(Schedule.start_date.asc()).limit(2).all()
    
    # 메인 페이지용 최근 회의록 (2개)
    recent_minutes = MeetingMinutes.query.order_by(MeetingMinutes.meeting_date.desc()).limit(2).all()
    
    return render_template('index.html',
                           banners=banners,
                           promise_rate=promise_rate,
                           upcoming_schedules=upcoming_schedules,
                           recent_minutes=recent_minutes)

@app.route('/schedule')
def schedule():
    schedules_query = Schedule.query.order_by(Schedule.start_date.desc()).all()
    # Serialize Schedule objects for JSON compatibility
    schedules = [{
        'id': s.id,
        'title': s.title,
        'description': s.description,
        'start_date': s.start_date.isoformat() if s.start_date else None,
        'end_date': s.end_date.isoformat() if s.end_date else None,
        'location': s.location,
        'category': s.category
    } for s in schedules_query]
    return render_template('schedule.html', schedules=schedules, schedules_raw=schedules_query)

@app.route('/organization')
def organization():
    # 간략 보기용 데이터 (회장단)
    presidents = Organization.query.filter(Organization.position.contains('회장')).order_by(Organization.order).all()
    # 위원장
    heads = Organization.query.filter(Organization.position.contains('위원장')).order_by(Organization.order).all()

    # 상세 보기용 데이터 (부서별 그룹화)
    all_members = Organization.query.order_by(Organization.order).all()
    departments = {}
    for m in all_members:
        dept = m.department or "회장단 및 중앙기구"
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(m)

    return render_template('organization.html',
                           presidents=presidents,
                           heads=heads,
                           departments=departments)

@app.route('/promises')
def promises():
    promises_list = Promise.query.order_by(Promise.order).all()
    categories = {}
    for promise in promises_list:
        if promise.category not in categories:
            categories[promise.category] = []
        categories[promise.category].append(promise)
    total_progress = sum(p.progress_rate for p in promises_list) / len(promises_list) if promises_list else 0
    return render_template('promises.html', categories=categories, total_progress=round(total_progress))

@app.route('/promises/<int:promise_id>')
def promise_detail(promise_id):
    promise = Promise.query.get_or_404(promise_id)
    progress_updates = PromiseProgress.query.filter_by(promise_id=promise_id).order_by(PromiseProgress.date.desc()).all()
    return render_template('promise_detail.html', promise=promise, progress_updates=progress_updates)

@app.route('/minutes')
def minutes():
    meeting_minutes = MeetingMinutes.query.order_by(MeetingMinutes.meeting_date.desc()).all()
    return render_template('minutes.html', minutes=meeting_minutes)

@app.route('/minutes/<int:minute_id>')
def minute_detail(minute_id):
    minute = MeetingMinutes.query.get_or_404(minute_id)
    return render_template('minute_detail.html', minute=minute)

@app.route('/regulations')
def regulations():
    regulations_list = Regulation.query.order_by(Regulation.order, Regulation.id).all()
    categories = {}
    for regulation in regulations_list:
        if regulation.category not in categories:
            categories[regulation.category] = []
        categories[regulation.category].append(regulation)
    return render_template('regulations.html', categories=categories)

@app.route('/regulations/pdf/<filename>')
def regulation_pdf(filename):
    """회칙 PDF 파일 뷰어"""
    regulations_dir = os.path.join(app.root_path, 'static', 'regulations')
    return send_from_directory(regulations_dir, filename)

@app.route('/programs')
def programs():
    programs_list = Program.query.filter_by(is_active=True).order_by(Program.created_at.desc()).all()
    return render_template('programs.html', programs=programs_list)

@app.route('/archive')
def archive():
    archives_list = Archive.query.filter_by(is_active=True).order_by(Archive.event_date.desc()).all()
    return render_template('archive.html', archives=archives_list)

@app.route('/archive/<int:archive_id>')
def archive_detail(archive_id):
    archive_item = Archive.query.get_or_404(archive_id)
    return render_template('archive_detail.html', archive=archive_item)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'schedules': Schedule.query.count(),
        'promises': Promise.query.count(),
        'minutes': MeetingMinutes.query.count(),
        'programs': Program.query.filter_by(is_active=True).count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/schedules')
@login_required
def admin_schedules():
    schedules = Schedule.query.order_by(Schedule.start_date.desc()).all()
    return render_template('admin/schedules.html', schedules=schedules)

@app.route('/admin/schedules/add', methods=['GET', 'POST'])
@login_required
def admin_schedule_add():
    if request.method == 'POST':
        schedule = Schedule(
            title=request.form['title'],
            description=request.form.get('description'),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M'),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form.get('end_date') else None,
            location=request.form.get('location'),
            category=request.form.get('category')
        )
        db.session.add(schedule)
        db.session.commit()
        flash('일정이 추가되었습니다.', 'success')
        return redirect(url_for('admin_schedules'))
    return render_template('admin/schedule_form.html')

@app.route('/admin/schedules/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def admin_schedule_edit(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if request.method == 'POST':
        schedule.title = request.form['title']
        schedule.description = request.form.get('description')
        schedule.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M')
        schedule.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form.get('end_date') else None
        schedule.location = request.form.get('location')
        schedule.category = request.form.get('category')
        db.session.commit()
        flash('일정이 수정되었습니다.', 'success')
        return redirect(url_for('admin_schedules'))
    return render_template('admin/schedule_form.html', schedule=schedule)

@app.route('/admin/schedules/delete/<int:schedule_id>', methods=['POST'])
@login_required
def admin_schedule_delete(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('일정이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_schedules'))

@app.route('/admin/promises')
@login_required
def admin_promises():
    promises_list = Promise.query.order_by(Promise.order).all()
    return render_template('admin/promises.html', promises=promises_list)

@app.route('/admin/promises/add', methods=['GET', 'POST'])
@login_required
def admin_promise_add():
    if request.method == 'POST':
        promise = Promise(
            category=request.form['category'],
            title=request.form['title'],
            description=request.form['description'],
            detailed_description=request.form.get('detailed_description'),
            progress_rate=int(request.form.get('progress_rate', 0)),
            status=request.form.get('status', '진행중'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(promise)
        db.session.commit()
        flash('공약이 추가되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_form.html')

@app.route('/admin/promises/edit/<int:promise_id>', methods=['GET', 'POST'])
@login_required
def admin_promise_edit(promise_id):
    promise = Promise.query.get_or_404(promise_id)
    if request.method == 'POST':
        promise.category = request.form['category']
        promise.title = request.form['title']
        promise.description = request.form['description']
        promise.detailed_description = request.form.get('detailed_description')
        promise.progress_rate = int(request.form.get('progress_rate', 0))
        promise.status = request.form.get('status', '진행중')
        promise.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('공약이 수정되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_form.html', promise=promise)

@app.route('/admin/promises/delete/<int:promise_id>', methods=['POST'])
@login_required
def admin_promise_delete(promise_id):
    promise = Promise.query.get_or_404(promise_id)
    db.session.delete(promise)
    db.session.commit()
    flash('공약이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_promises'))

@app.route('/admin/promises/<int:promise_id>/progress/add', methods=['GET', 'POST'])
@login_required
def admin_promise_progress_add(promise_id):
    promise = Promise.query.get_or_404(promise_id)
    if request.method == 'POST':
        progress = PromiseProgress(
            promise_id=promise_id,
            title=request.form['title'],
            content=request.form['content'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d')
        )
        db.session.add(progress)
        db.session.commit()
        flash('진행상황이 추가되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_progress_form.html', promise=promise)

@app.route('/admin/minutes')
@login_required
def admin_minutes():
    meeting_minutes = MeetingMinutes.query.order_by(MeetingMinutes.meeting_date.desc()).all()
    return render_template('admin/minutes.html', minutes=meeting_minutes)

@app.route('/admin/minutes/add', methods=['GET', 'POST'])
@login_required
def admin_minute_add():
    if request.method == 'POST':
        file_url = None
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'minutes')
            if saved_path: file_url = saved_path
        if not file_url and request.form.get('file_url_text'):
             file_url = request.form.get('file_url_text')

        minute = MeetingMinutes(
            title=request.form['title'],
            meeting_type=request.form.get('meeting_type'),
            meeting_date=datetime.strptime(request.form['meeting_date'], '%Y-%m-%d'),
            attendees=request.form.get('attendees'),
            agenda=request.form.get('agenda'),
            content=request.form['content'],
            decisions=request.form.get('decisions'),
            file_url=file_url
        )
        db.session.add(minute)
        db.session.commit()
        flash('회의록이 추가되었습니다.', 'success')
        return redirect(url_for('admin_minutes'))
    return render_template('admin/minute_form.html')

@app.route('/admin/minutes/edit/<int:minute_id>', methods=['GET', 'POST'])
@login_required
def admin_minute_edit(minute_id):
    minute = MeetingMinutes.query.get_or_404(minute_id)
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'minutes')
            if saved_path: minute.file_url = saved_path
        if request.form.get('file_url_text'):
             minute.file_url = request.form.get('file_url_text')

        minute.title = request.form['title']
        minute.meeting_type = request.form.get('meeting_type')
        minute.meeting_date = datetime.strptime(request.form['meeting_date'], '%Y-%m-%d')
        minute.attendees = request.form.get('attendees')
        minute.agenda = request.form.get('agenda')
        minute.content = request.form['content']
        minute.decisions = request.form.get('decisions')
        db.session.commit()
        flash('회의록이 수정되었습니다.', 'success')
        return redirect(url_for('admin_minutes'))
    return render_template('admin/minute_form.html', minute=minute)

@app.route('/admin/minutes/delete/<int:minute_id>', methods=['POST'])
@login_required
def admin_minute_delete(minute_id):
    minute = MeetingMinutes.query.get_or_404(minute_id)
    db.session.delete(minute)
    db.session.commit()
    flash('회의록이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_minutes'))

@app.route('/admin/regulations')
@login_required
def admin_regulations():
    regulations_list = Regulation.query.order_by(Regulation.category, Regulation.order).all()
    return render_template('admin/regulations.html', regulations=regulations_list)

@app.route('/admin/regulations/add', methods=['GET', 'POST'])
@login_required
def admin_regulation_add():
    if request.method == 'POST':
        file_url = None
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'regulations')
            if saved_path: file_url = saved_path
        if not file_url and request.form.get('file_url_text'):
             file_url = request.form.get('file_url_text')

        regulation = Regulation(
            category=request.form['category'],
            title=request.form['title'],
            content=request.form['content'],
            file_url=file_url,
            order=int(request.form.get('order', 0))
        )
        db.session.add(regulation)
        db.session.commit()
        flash('회칙이 추가되었습니다.', 'success')
        return redirect(url_for('admin_regulations'))
    return render_template('admin/regulation_form.html')

@app.route('/admin/regulations/edit/<int:regulation_id>', methods=['GET', 'POST'])
@login_required
def admin_regulation_edit(regulation_id):
    regulation = Regulation.query.get_or_404(regulation_id)
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'regulations')
            if saved_path: regulation.file_url = saved_path
        if request.form.get('file_url_text'):
             regulation.file_url = request.form.get('file_url_text')
        regulation.category = request.form['category']
        regulation.title = request.form['title']
        regulation.content = request.form['content']
        regulation.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('회칙이 수정되었습니다.', 'success')
        return redirect(url_for('admin_regulations'))
    return render_template('admin/regulation_form.html', regulation=regulation)

@app.route('/admin/regulations/delete/<int:regulation_id>', methods=['POST'])
@login_required
def admin_regulation_delete(regulation_id):
    regulation = Regulation.query.get_or_404(regulation_id)
    db.session.delete(regulation)
    db.session.commit()
    flash('회칙이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_regulations'))

@app.route('/admin/programs')
@login_required
def admin_programs():
    programs_list = Program.query.order_by(Program.created_at.desc()).all()
    return render_template('admin/programs.html', programs=programs_list)

@app.route('/admin/programs/add', methods=['GET', 'POST'])
@login_required
def admin_program_add():
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'programs')
            if saved_path: image_url = saved_path
        if not image_url and request.form.get('image_url_text'):
            image_url = request.form.get('image_url_text')

        program = Program(
            title=request.form['title'],
            category=request.form.get('category'),
            description=request.form['description'],
            organizer=request.form.get('organizer'),
            target=request.form.get('target'),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d') if request.form.get('start_date') else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form.get('end_date') else None,
            application_start=datetime.strptime(request.form['application_start'], '%Y-%m-%d') if request.form.get('application_start') else None,
            application_end=datetime.strptime(request.form['application_end'], '%Y-%m-%d') if request.form.get('application_end') else None,
            location=request.form.get('location'),
            link=request.form.get('link'),
            image_url=image_url,
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(program)
        db.session.commit()
        flash('프로그램이 추가되었습니다.', 'success')
        return redirect(url_for('admin_programs'))
    return render_template('admin/program_form.html')

@app.route('/admin/programs/edit/<int:program_id>', methods=['GET', 'POST'])
@login_required
def admin_program_edit(program_id):
    program = Program.query.get_or_404(program_id)
    if request.method == 'POST':
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'programs')
            if saved_path: program.image_url = saved_path
        if request.form.get('image_url_text'):
            program.image_url = request.form.get('image_url_text')
        program.title = request.form['title']
        program.category = request.form.get('category')
        program.description = request.form['description']
        program.organizer = request.form.get('organizer')
        program.target = request.form.get('target')
        program.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d') if request.form.get('start_date') else None
        program.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form.get('end_date') else None
        program.application_start = datetime.strptime(request.form['application_start'], '%Y-%m-%d') if request.form.get('application_start') else None
        program.application_end = datetime.strptime(request.form['application_end'], '%Y-%m-%d') if request.form.get('application_end') else None
        program.location = request.form.get('location')
        program.link = request.form.get('link')
        program.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('프로그램이 수정되었습니다.', 'success')
        return redirect(url_for('admin_programs'))
    return render_template('admin/program_form.html', program=program)

@app.route('/admin/programs/delete/<int:program_id>', methods=['POST'])
@login_required
def admin_program_delete(program_id):
    program = Program.query.get_or_404(program_id)
    db.session.delete(program)
    db.session.commit()
    flash('프로그램이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_programs'))

@app.route('/admin/banners')
@login_required
def admin_banners():
    banners = Banner.query.order_by(Banner.order).all()
    return render_template('admin/banners.html', banners=banners)

@app.route('/admin/banners/add', methods=['GET', 'POST'])
@login_required
def admin_banner_add():
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'banners')
            if saved_path: image_url = saved_path
        if not image_url and request.form.get('image_url_text'):
            image_url = request.form.get('image_url_text')
        banner = Banner(
            title=request.form['title'],
            image_url=image_url,
            link=request.form.get('link'),
            is_active=request.form.get('is_active') == 'on',
            is_event_banner=request.form.get('is_event_banner') == 'on',
            order=int(request.form.get('order', 0))
        )
        db.session.add(banner)
        db.session.commit()
        flash('배너가 추가되었습니다.', 'success')
        return redirect(url_for('admin_banners'))
    return render_template('admin/banner_form.html')

@app.route('/admin/banners/edit/<int:banner_id>', methods=['GET', 'POST'])
@login_required
def admin_banner_edit(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    if request.method == 'POST':
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'banners')
            if saved_path: banner.image_url = saved_path
        if request.form.get('image_url_text'):
            banner.image_url = request.form.get('image_url_text')
        banner.title = request.form['title']
        banner.link = request.form.get('link')
        banner.is_active = request.form.get('is_active') == 'on'
        banner.is_event_banner = request.form.get('is_event_banner') == 'on'
        banner.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('배너가 수정되었습니다.', 'success')
        return redirect(url_for('admin_banners'))
    return render_template('admin/banner_form.html', banner=banner)

@app.route('/admin/banners/delete/<int:banner_id>', methods=['POST'])
@login_required
def admin_banner_delete(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    flash('배너가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_banners'))

@app.route('/admin/organization')
@login_required
def admin_organization():
    members = Organization.query.order_by(Organization.order).all()
    return render_template('admin/organization.html', members=members)

@app.route('/admin/organization/add', methods=['GET', 'POST'])
@login_required
def admin_organization_add():
    if request.method == 'POST':
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            saved_path = save_file(file, 'profiles')
            if saved_path: photo_url = saved_path
        if not photo_url and request.form.get('photo_url_text'):
            photo_url = request.form.get('photo_url_text')
        member = Organization(
            name=request.form['name'],
            position=request.form['position'],
            department=request.form.get('department'),
            major=request.form.get('major'),
            student_id=request.form.get('student_id'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            photo_url=photo_url,
            order=int(request.form.get('order', 0))
        )
        db.session.add(member)
        db.session.commit()
        flash('조직도 멤버가 추가되었습니다.', 'success')
        return redirect(url_for('admin_organization'))
    return render_template('admin/organization_form.html')

@app.route('/admin/organization/edit/<int:member_id>', methods=['GET', 'POST'])
@login_required
def admin_organization_edit(member_id):
    member = Organization.query.get_or_404(member_id)
    if request.method == 'POST':
        if 'photo' in request.files:
            file = request.files['photo']
            saved_path = save_file(file, 'profiles')
            if saved_path: member.photo_url = saved_path
        if request.form.get('photo_url_text'):
            member.photo_url = request.form.get('photo_url_text')
        member.name = request.form['name']
        member.position = request.form['position']
        member.department = request.form.get('department')
        member.major = request.form.get('major')
        member.student_id = request.form.get('student_id')
        member.phone = request.form.get('phone')
        member.email = request.form.get('email')
        member.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('조직도 멤버가 수정되었습니다.', 'success')
        return redirect(url_for('admin_organization'))
    return render_template('admin/organization_form.html', member=member)

@app.route('/admin/organization/delete/<int:member_id>', methods=['POST'])
@login_required
def admin_organization_delete(member_id):
    member = Organization.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('조직도 멤버가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_organization'))

@app.route('/admin/archives')
@login_required
def admin_archives():
    archives = Archive.query.order_by(Archive.event_date.desc()).all()
    return render_template('admin/archives.html', archives=archives)

@app.route('/admin/archives/add', methods=['GET', 'POST'])
@login_required
def admin_archive_add():
    if request.method == 'POST':
        thumbnail_url = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            saved_path = save_file(file, 'archives')
            if saved_path: thumbnail_url = saved_path
        if not thumbnail_url and request.form.get('thumbnail_url_text'):
            thumbnail_url = request.form.get('thumbnail_url_text')

        archive = Archive(
            title=request.form['title'],
            description=request.form.get('description'),
            event_date=datetime.strptime(request.form['event_date'], '%Y-%m-%d'),
            category=request.form.get('category'),
            location=request.form.get('location'),
            thumbnail_url=thumbnail_url,
            is_active=request.form.get('is_active') == 'on',
            order=int(request.form.get('order', 0))
        )
        db.session.add(archive)
        db.session.commit()

        # 다중 이미지 업로드 처리
        if 'images' in request.files:
            files = request.files.getlist('images')
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    image_url = save_file(file, 'archives')
                    if image_url:
                        archive_image = ArchiveImage(
                            archive_id=archive.id,
                            image_url=image_url,
                            order=idx
                        )
                        db.session.add(archive_image)
            db.session.commit()

        flash('아카이브가 추가되었습니다.', 'success')
        return redirect(url_for('admin_archives'))
    return render_template('admin/archive_form.html')

@app.route('/admin/archives/edit/<int:archive_id>', methods=['GET', 'POST'])
@login_required
def admin_archive_edit(archive_id):
    archive = Archive.query.get_or_404(archive_id)
    if request.method == 'POST':
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            saved_path = save_file(file, 'archives')
            if saved_path: archive.thumbnail_url = saved_path
        if request.form.get('thumbnail_url_text'):
            archive.thumbnail_url = request.form.get('thumbnail_url_text')

        archive.title = request.form['title']
        archive.description = request.form.get('description')
        archive.event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d')
        archive.category = request.form.get('category')
        archive.location = request.form.get('location')
        archive.is_active = request.form.get('is_active') == 'on'
        archive.order = int(request.form.get('order', 0))

        # 새로운 이미지 추가
        if 'images' in request.files:
            files = request.files.getlist('images')
            current_max_order = max([img.order for img in archive.images], default=-1)
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    image_url = save_file(file, 'archives')
                    if image_url:
                        archive_image = ArchiveImage(
                            archive_id=archive.id,
                            image_url=image_url,
                            order=current_max_order + idx + 1
                        )
                        db.session.add(archive_image)

        db.session.commit()
        flash('아카이브가 수정되었습니다.', 'success')
        return redirect(url_for('admin_archives'))
    return render_template('admin/archive_form.html', archive=archive)

@app.route('/admin/archives/delete/<int:archive_id>', methods=['POST'])
@login_required
def admin_archive_delete(archive_id):
    archive = Archive.query.get_or_404(archive_id)
    db.session.delete(archive)
    db.session.commit()
    flash('아카이브가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_archives'))

@app.route('/admin/archives/<int:archive_id>/images/delete/<int:image_id>', methods=['POST'])
@login_required
def admin_archive_image_delete(archive_id, image_id):
    image = ArchiveImage.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    flash('이미지가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_archive_edit', archive_id=archive_id))

@app.cli.command()
def init_db():
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', name='관리자')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print('기본 관리자 계정 생성 완료 (admin / admin)')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 1992))
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True, reloader_type='stat')