from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_compress import Compress
from werkzeug.utils import secure_filename
from config import Config
from database import init_supabase
from supabase_helpers import SupabaseHelper
from storage_helper import storage
from admin_user import AdminUser
from datetime import datetime
import os
import shutil

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# 압축 활성화 (gzip) - 응답 크기를 60-80% 감소
compress = Compress()
compress.init_app(app)

# WhiteNoise 설정 - 정적 파일 효율적 서빙 및 캐싱
try:
    from whitenoise import WhiteNoise
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=os.path.join(os.path.dirname(__file__), 'static'),
        prefix='static/',
        max_age=31536000 if not app.debug else 0  # 1년 캐싱 (프로덕션)
    )
except ImportError:
    pass  # WhiteNoise 없으면 기본 설정 사용

# Supabase 초기화
init_supabase(app)
db_helper = SupabaseHelper()

# Flask-Login 초기화
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader"""
    admin_data = db_helper.admin_client.table('admins').select('*').eq('id', int(user_id)).execute()
    if admin_data.data:
        return AdminUser(admin_data.data[0])
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_file(file, subfolder='files'):
    """
    파일을 Supabase Storage에 업로드

    Args:
        file: 업로드할 파일 객체
        subfolder: 저장할 하위 폴더 (files, images, banners 등)

    Returns:
        업로드된 파일의 공개 URL 또는 None
    """
    if file and allowed_file(file.filename):
        return storage.upload_file(file, subfolder)
    return None

def delete_file(file_url):
    """
    파일을 Supabase Storage에서 삭제

    Args:
        file_url: 삭제할 파일의 URL

    Returns:
        삭제 성공 여부
    """
    if file_url:
        return storage.delete_file(file_url)
    return False

def init_default_files():
    """
    서버 시작 시 초기화 함수

    Note: Supabase Storage를 사용하므로 파일 복사는 더 이상 필요하지 않습니다.
    로고는 static/defaults/logo.png에서 직접 서빙됩니다.
    기타 파일들은 Supabase Storage에서 관리됩니다.
    """
    # uploads 폴더 구조 생성 (로컬 개발 환경을 위해)
    uploads_dir = app.config['UPLOAD_FOLDER']
    for subfolder in ['banners', 'files', 'images', 'minutes', 'profiles', 'programs', 'regulations', 'archives']:
        os.makedirs(os.path.join(uploads_dir, subfolder), exist_ok=True)

    print('✓ 서버 초기화 완료')
    print('  - 로고: static/defaults/logo.png에서 서빙')
    print('  - 업로드 파일: Supabase Storage에 저장')

# ============================================
# 공개 페이지
# ============================================

@app.route('/')
def index():
    # 배너 로직 강화: 모든 활성 배너 노출 (캐러셀)
    banners = db_helper.get_all_banners(is_active=True)

    # 전반적인 공약 이행률 계산
    promises_list = db_helper.get_all_promises()
    promise_rate = int(sum(p.get('progress_rate', 0) for p in promises_list) / len(promises_list)) if promises_list else 0

    # 메인 페이지용 다가오는 일정 (2개)
    upcoming_schedules = db_helper.get_upcoming_schedules(limit=2)

    # 메인 페이지용 최근 회의록 (2개)
    recent_minutes = db_helper.get_recent_minutes(limit=2)

    return render_template('index.html',
                           banners=banners,
                           promise_rate=promise_rate,
                           upcoming_schedules=upcoming_schedules,
                           recent_minutes=recent_minutes)

@app.route('/schedule')
def schedule():
    schedules_raw = db_helper.get_all_schedules(order_by='start_date', ascending=False)
    # Serialize Schedule objects for JSON compatibility
    schedules = [{
        'id': s.get('id'),
        'title': s.get('title'),
        'description': s.get('description'),
        'start_date': s.get('start_date'),
        'end_date': s.get('end_date'),
        'location': s.get('location'),
        'category': s.get('category')
    } for s in schedules_raw]
    return render_template('schedule.html', schedules=schedules, schedules_raw=schedules_raw)

@app.route('/organization')
def organization():
    # 간략 보기용 데이터 (회장단)
    presidents = db_helper.get_organizations_by_position('회장')
    # 위원장
    heads = db_helper.get_organizations_by_position('위원장')

    # 상세 보기용 데이터 (부서별 그룹화)
    all_members = db_helper.get_all_organizations()
    departments = {}
    for m in all_members:
        dept = m.get('department') or "회장단 및 중앙기구"
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(m)

    return render_template('organization.html',
                           presidents=presidents,
                           heads=heads,
                           departments=departments)

@app.route('/promises')
def promises():
    promises_list = db_helper.get_all_promises()
    categories = {}
    for promise in promises_list:
        category = promise.get('category')
        if category not in categories:
            categories[category] = []
        # 각 공약에 진행 상황 추가
        promise['progress_updates'] = db_helper.get_promise_progress(promise['id'])
        categories[category].append(promise)
    total_progress = sum(p.get('progress_rate', 0) for p in promises_list) / len(promises_list) if promises_list else 0
    return render_template('promises.html', categories=categories, total_progress=round(total_progress))

@app.route('/promises/<int:promise_id>')
def promise_detail(promise_id):
    promise = db_helper.get_promise_by_id(promise_id)
    if not promise:
        flash('공약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('promises'))
    progress_updates = db_helper.get_promise_progress(promise_id)
    return render_template('promise_detail.html', promise=promise, progress_updates=progress_updates)

@app.route('/minutes')
def minutes():
    meeting_minutes = db_helper.get_all_minutes()
    return render_template('minutes.html', minutes=meeting_minutes)

@app.route('/minutes/<int:minute_id>')
def minute_detail(minute_id):
    minute = db_helper.get_minute_by_id(minute_id)
    if not minute:
        flash('회의록을 찾을 수 없습니다.', 'error')
        return redirect(url_for('minutes'))
    return render_template('minute_detail.html', minute=minute)

@app.route('/regulations')
def regulations():
    regulations_list = db_helper.get_all_regulations()
    categories = {}
    for regulation in regulations_list:
        category = regulation.get('category')
        if category not in categories:
            categories[category] = []
        categories[category].append(regulation)
    return render_template('regulations.html', categories=categories)

@app.route('/regulations/pdf/<path:filename>')
def regulation_pdf(filename):
    """회칙 PDF 파일 제공"""
    # static/uploads/regulations 폴더에서 파일 제공
    regulations_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'regulations')
    return send_from_directory(regulations_dir, filename)

@app.route('/programs')
def programs():
    programs_list = db_helper.get_all_programs(is_active=True)
    return render_template('programs.html', programs=programs_list)

@app.route('/archive')
def archive():
    archives_list = db_helper.get_all_archives(is_active=True)
    return render_template('archive.html', archives=archives_list)

@app.route('/archive/<int:archive_id>')
def archive_detail(archive_id):
    archive_item = db_helper.get_archive_by_id(archive_id)
    if not archive_item:
        flash('아카이브를 찾을 수 없습니다.', 'error')
        return redirect(url_for('archive'))
    return render_template('archive_detail.html', archive=archive_item)

# ============================================
# 관리자 인증
# ============================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin_data = db_helper.get_admin_by_username(username)
        if admin_data and db_helper.check_admin_password(admin_data.get('password_hash'), password):
            admin_user = AdminUser(admin_data)
            login_user(admin_user, remember=True)
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

# ============================================
# 관리자 대시보드
# ============================================

@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'schedules': db_helper.count_schedules(),
        'promises': db_helper.count_promises(),
        'minutes': db_helper.count_minutes(),
        'programs': db_helper.count_active_programs()
    }
    return render_template('admin/dashboard.html', stats=stats)

# ============================================
# 일정 관리
# ============================================

@app.route('/admin/schedules')
@login_required
def admin_schedules():
    schedules = db_helper.get_all_schedules(order_by='start_date', ascending=False)
    return render_template('admin/schedules.html', schedules=schedules)

@app.route('/admin/schedules/add', methods=['GET', 'POST'])
@login_required
def admin_schedule_add():
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'description': request.form.get('description'),
            'start_date': request.form['start_date'],
            'end_date': request.form.get('end_date') if request.form.get('end_date') else None,
            'location': request.form.get('location'),
            'category': request.form.get('category')
        }
        db_helper.create_schedule(data)
        flash('일정이 추가되었습니다.', 'success')
        return redirect(url_for('admin_schedules'))
    return render_template('admin/schedule_form.html')

@app.route('/admin/schedules/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def admin_schedule_edit(schedule_id):
    schedule = db_helper.get_schedule_by_id(schedule_id)
    if not schedule:
        flash('일정을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_schedules'))

    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'description': request.form.get('description'),
            'start_date': request.form['start_date'],
            'end_date': request.form.get('end_date') if request.form.get('end_date') else None,
            'location': request.form.get('location'),
            'category': request.form.get('category')
        }
        db_helper.update_schedule(schedule_id, data)
        flash('일정이 수정되었습니다.', 'success')
        return redirect(url_for('admin_schedules'))
    return render_template('admin/schedule_form.html', schedule=schedule)

@app.route('/admin/schedules/delete/<int:schedule_id>', methods=['POST'])
@login_required
def admin_schedule_delete(schedule_id):
    db_helper.delete_schedule(schedule_id)
    flash('일정이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_schedules'))

# ============================================
# 공약 관리
# ============================================

@app.route('/admin/promises')
@login_required
def admin_promises():
    promises_list = db_helper.get_all_promises()
    return render_template('admin/promises.html', promises=promises_list)

@app.route('/admin/promises/add', methods=['GET', 'POST'])
@login_required
def admin_promise_add():
    if request.method == 'POST':
        data = {
            'category': request.form['category'],
            'title': request.form['title'],
            'description': request.form['description'],
            'detailed_description': request.form.get('detailed_description'),
            'progress_rate': int(request.form.get('progress_rate', 0)),
            'status': request.form.get('status', '진행중'),
            'order': int(request.form.get('order', 0))
        }
        db_helper.create_promise(data)
        flash('공약이 추가되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_form.html')

@app.route('/admin/promises/edit/<int:promise_id>', methods=['GET', 'POST'])
@login_required
def admin_promise_edit(promise_id):
    promise = db_helper.get_promise_by_id(promise_id)
    if not promise:
        flash('공약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_promises'))

    if request.method == 'POST':
        data = {
            'category': request.form['category'],
            'title': request.form['title'],
            'description': request.form['description'],
            'detailed_description': request.form.get('detailed_description'),
            'progress_rate': int(request.form.get('progress_rate', 0)),
            'status': request.form.get('status', '진행중'),
            'order': int(request.form.get('order', 0))
        }
        db_helper.update_promise(promise_id, data)
        flash('공약이 수정되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_form.html', promise=promise)

@app.route('/admin/promises/delete/<int:promise_id>', methods=['POST'])
@login_required
def admin_promise_delete(promise_id):
    db_helper.delete_promise(promise_id)
    flash('공약이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_promises'))

@app.route('/admin/promises/<int:promise_id>/progress/add', methods=['GET', 'POST'])
@login_required
def admin_promise_progress_add(promise_id):
    promise = db_helper.get_promise_by_id(promise_id)
    if not promise:
        flash('공약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_promises'))

    if request.method == 'POST':
        data = {
            'promise_id': promise_id,
            'title': request.form['title'],
            'content': request.form['content'],
            'date': request.form['date']
        }
        db_helper.create_promise_progress(data)
        flash('진행상황이 추가되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_progress_form.html', promise=promise)

# ============================================
# 회의록 관리
# ============================================

@app.route('/admin/minutes')
@login_required
def admin_minutes():
    meeting_minutes = db_helper.get_all_minutes()
    return render_template('admin/minutes.html', minutes=meeting_minutes)

@app.route('/admin/minutes/add', methods=['GET', 'POST'])
@login_required
def admin_minute_add():
    if request.method == 'POST':
        file_url = None
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'minutes')
            if saved_path:
                file_url = saved_path
        if not file_url and request.form.get('file_url_text'):
            file_url = request.form.get('file_url_text')

        data = {
            'title': request.form['title'],
            'meeting_type': request.form.get('meeting_type'),
            'meeting_date': request.form['meeting_date'],
            'attendees': request.form.get('attendees'),
            'agenda': request.form.get('agenda'),
            'content': request.form['content'],
            'decisions': request.form.get('decisions'),
            'file_url': file_url
        }
        db_helper.create_minute(data)
        flash('회의록이 추가되었습니다.', 'success')
        return redirect(url_for('admin_minutes'))
    return render_template('admin/minute_form.html')

@app.route('/admin/minutes/edit/<int:minute_id>', methods=['GET', 'POST'])
@login_required
def admin_minute_edit(minute_id):
    minute = db_helper.get_minute_by_id(minute_id)
    if not minute:
        flash('회의록을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_minutes'))

    if request.method == 'POST':
        file_url = minute.get('file_url')
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'minutes')
            if saved_path:
                file_url = saved_path
        if request.form.get('file_url_text'):
            file_url = request.form.get('file_url_text')

        data = {
            'title': request.form['title'],
            'meeting_type': request.form.get('meeting_type'),
            'meeting_date': request.form['meeting_date'],
            'attendees': request.form.get('attendees'),
            'agenda': request.form.get('agenda'),
            'content': request.form['content'],
            'decisions': request.form.get('decisions'),
            'file_url': file_url
        }
        db_helper.update_minute(minute_id, data)
        flash('회의록이 수정되었습니다.', 'success')
        return redirect(url_for('admin_minutes'))
    return render_template('admin/minute_form.html', minute=minute)

@app.route('/admin/minutes/delete/<int:minute_id>', methods=['POST'])
@login_required
def admin_minute_delete(minute_id):
    db_helper.delete_minute(minute_id)
    flash('회의록이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_minutes'))

# ============================================
# 회칙 관리
# ============================================

@app.route('/admin/regulations')
@login_required
def admin_regulations():
    regulations_list = db_helper.get_all_regulations()
    return render_template('admin/regulations.html', regulations=regulations_list)

@app.route('/admin/regulations/add', methods=['GET', 'POST'])
@login_required
def admin_regulation_add():
    if request.method == 'POST':
        file_url = None
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'regulations')
            if saved_path:
                file_url = saved_path
        if not file_url and request.form.get('file_url_text'):
            file_url = request.form.get('file_url_text')

        data = {
            'category': request.form['category'],
            'title': request.form['title'],
            'content': request.form['content'],
            'file_url': file_url,
            'order': int(request.form.get('order', 0))
        }
        db_helper.create_regulation(data)
        flash('회칙이 추가되었습니다.', 'success')
        return redirect(url_for('admin_regulations'))
    return render_template('admin/regulation_form.html')

@app.route('/admin/regulations/edit/<int:regulation_id>', methods=['GET', 'POST'])
@login_required
def admin_regulation_edit(regulation_id):
    regulation = db_helper.get_regulation_by_id(regulation_id)
    if not regulation:
        flash('회칙을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_regulations'))

    if request.method == 'POST':
        file_url = regulation.get('file_url')
        if 'file' in request.files:
            file = request.files['file']
            saved_path = save_file(file, 'regulations')
            if saved_path:
                file_url = saved_path
        if request.form.get('file_url_text'):
            file_url = request.form.get('file_url_text')

        data = {
            'category': request.form['category'],
            'title': request.form['title'],
            'content': request.form['content'],
            'file_url': file_url,
            'order': int(request.form.get('order', 0))
        }
        db_helper.update_regulation(regulation_id, data)
        flash('회칙이 수정되었습니다.', 'success')
        return redirect(url_for('admin_regulations'))
    return render_template('admin/regulation_form.html', regulation=regulation)

@app.route('/admin/regulations/delete/<int:regulation_id>', methods=['POST'])
@login_required
def admin_regulation_delete(regulation_id):
    db_helper.delete_regulation(regulation_id)
    flash('회칙이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_regulations'))

# ============================================
# 프로그램 관리
# ============================================

@app.route('/admin/programs')
@login_required
def admin_programs():
    programs_list = db_helper.get_all_programs(is_active=None)
    return render_template('admin/programs.html', programs=programs_list)

@app.route('/admin/programs/add', methods=['GET', 'POST'])
@login_required
def admin_program_add():
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'programs')
            if saved_path:
                image_url = saved_path
        if not image_url and request.form.get('image_url_text'):
            image_url = request.form.get('image_url_text')

        data = {
            'title': request.form['title'],
            'category': request.form.get('category'),
            'description': request.form['description'],
            'organizer': request.form.get('organizer'),
            'target': request.form.get('target'),
            'start_date': request.form.get('start_date') if request.form.get('start_date') else None,
            'end_date': request.form.get('end_date') if request.form.get('end_date') else None,
            'application_start': request.form.get('application_start') if request.form.get('application_start') else None,
            'application_end': request.form.get('application_end') if request.form.get('application_end') else None,
            'location': request.form.get('location'),
            'link': request.form.get('link'),
            'image_url': image_url,
            'is_active': request.form.get('is_active') == 'on'
        }
        db_helper.create_program(data)
        flash('프로그램이 추가되었습니다.', 'success')
        return redirect(url_for('admin_programs'))
    return render_template('admin/program_form.html')

@app.route('/admin/programs/edit/<int:program_id>', methods=['GET', 'POST'])
@login_required
def admin_program_edit(program_id):
    program = db_helper.get_program_by_id(program_id)
    if not program:
        flash('프로그램을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_programs'))

    if request.method == 'POST':
        image_url = program.get('image_url')
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'programs')
            if saved_path:
                image_url = saved_path
        if request.form.get('image_url_text'):
            image_url = request.form.get('image_url_text')

        data = {
            'title': request.form['title'],
            'category': request.form.get('category'),
            'description': request.form['description'],
            'organizer': request.form.get('organizer'),
            'target': request.form.get('target'),
            'start_date': request.form.get('start_date') if request.form.get('start_date') else None,
            'end_date': request.form.get('end_date') if request.form.get('end_date') else None,
            'application_start': request.form.get('application_start') if request.form.get('application_start') else None,
            'application_end': request.form.get('application_end') if request.form.get('application_end') else None,
            'location': request.form.get('location'),
            'link': request.form.get('link'),
            'image_url': image_url,
            'is_active': request.form.get('is_active') == 'on'
        }
        db_helper.update_program(program_id, data)
        flash('프로그램이 수정되었습니다.', 'success')
        return redirect(url_for('admin_programs'))
    return render_template('admin/program_form.html', program=program)

@app.route('/admin/programs/delete/<int:program_id>', methods=['POST'])
@login_required
def admin_program_delete(program_id):
    db_helper.delete_program(program_id)
    flash('프로그램이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_programs'))

# ============================================
# 배너 관리
# ============================================

@app.route('/admin/banners')
@login_required
def admin_banners():
    banners = db_helper.get_all_banners(is_active=None)
    return render_template('admin/banners.html', banners=banners)

@app.route('/admin/banners/add', methods=['GET', 'POST'])
@login_required
def admin_banner_add():
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'banners')
            if saved_path:
                image_url = saved_path
        if not image_url and request.form.get('image_url_text'):
            image_url = request.form.get('image_url_text')

        data = {
            'title': request.form['title'],
            'image_url': image_url,
            'link': request.form.get('link'),
            'is_active': request.form.get('is_active') == 'on',
            'is_event_banner': request.form.get('is_event_banner') == 'on',
            'order': int(request.form.get('order', 0))
        }
        db_helper.create_banner(data)
        flash('배너가 추가되었습니다.', 'success')
        return redirect(url_for('admin_banners'))
    return render_template('admin/banner_form.html')

@app.route('/admin/banners/edit/<int:banner_id>', methods=['GET', 'POST'])
@login_required
def admin_banner_edit(banner_id):
    banner = db_helper.get_banner_by_id(banner_id)
    if not banner:
        flash('배너를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_banners'))

    if request.method == 'POST':
        image_url = banner.get('image_url')
        if 'image' in request.files:
            file = request.files['image']
            saved_path = save_file(file, 'banners')
            if saved_path:
                image_url = saved_path
        if request.form.get('image_url_text'):
            image_url = request.form.get('image_url_text')

        data = {
            'title': request.form['title'],
            'image_url': image_url,
            'link': request.form.get('link'),
            'is_active': request.form.get('is_active') == 'on',
            'is_event_banner': request.form.get('is_event_banner') == 'on',
            'order': int(request.form.get('order', 0))
        }
        db_helper.update_banner(banner_id, data)
        flash('배너가 수정되었습니다.', 'success')
        return redirect(url_for('admin_banners'))
    return render_template('admin/banner_form.html', banner=banner)

@app.route('/admin/banners/delete/<int:banner_id>', methods=['POST'])
@login_required
def admin_banner_delete(banner_id):
    db_helper.delete_banner(banner_id)
    flash('배너가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_banners'))

# ============================================
# 조직도 관리
# ============================================

@app.route('/admin/organization')
@login_required
def admin_organization():
    members = db_helper.get_all_organizations()
    return render_template('admin/organization.html', members=members)

@app.route('/admin/organization/add', methods=['GET', 'POST'])
@login_required
def admin_organization_add():
    if request.method == 'POST':
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            saved_path = save_file(file, 'profiles')
            if saved_path:
                photo_url = saved_path
        if not photo_url and request.form.get('photo_url_text'):
            photo_url = request.form.get('photo_url_text')

        data = {
            'name': request.form['name'],
            'position': request.form['position'],
            'department': request.form.get('department'),
            'major': request.form.get('major'),
            'student_id': request.form.get('student_id'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'photo_url': photo_url,
            'order': int(request.form.get('order', 0))
        }
        db_helper.create_organization(data)
        flash('조직도 멤버가 추가되었습니다.', 'success')
        return redirect(url_for('admin_organization'))
    return render_template('admin/organization_form.html')

@app.route('/admin/organization/edit/<int:member_id>', methods=['GET', 'POST'])
@login_required
def admin_organization_edit(member_id):
    member = db_helper.get_organization_by_id(member_id)
    if not member:
        flash('조직도 멤버를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_organization'))

    if request.method == 'POST':
        photo_url = member.get('photo_url')
        if 'photo' in request.files:
            file = request.files['photo']
            saved_path = save_file(file, 'profiles')
            if saved_path:
                photo_url = saved_path
        if request.form.get('photo_url_text'):
            photo_url = request.form.get('photo_url_text')

        data = {
            'name': request.form['name'],
            'position': request.form['position'],
            'department': request.form.get('department'),
            'major': request.form.get('major'),
            'student_id': request.form.get('student_id'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'photo_url': photo_url,
            'order': int(request.form.get('order', 0))
        }
        db_helper.update_organization(member_id, data)
        flash('조직도 멤버가 수정되었습니다.', 'success')
        return redirect(url_for('admin_organization'))
    return render_template('admin/organization_form.html', member=member)

@app.route('/admin/organization/delete/<int:member_id>', methods=['POST'])
@login_required
def admin_organization_delete(member_id):
    db_helper.delete_organization(member_id)
    flash('조직도 멤버가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_organization'))

# ============================================
# 아카이브 관리
# ============================================

@app.route('/admin/archives')
@login_required
def admin_archives():
    archives = db_helper.get_all_archives(is_active=None)
    return render_template('admin/archives.html', archives=archives)

@app.route('/admin/archives/add', methods=['GET', 'POST'])
@login_required
def admin_archive_add():
    if request.method == 'POST':
        thumbnail_url = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            saved_path = save_file(file, 'archives')
            if saved_path:
                thumbnail_url = saved_path
        if not thumbnail_url and request.form.get('thumbnail_url_text'):
            thumbnail_url = request.form.get('thumbnail_url_text')

        data = {
            'title': request.form['title'],
            'description': request.form.get('description'),
            'event_date': request.form['event_date'],
            'category': request.form.get('category'),
            'location': request.form.get('location'),
            'thumbnail_url': thumbnail_url,
            'is_active': request.form.get('is_active') == 'on',
            'order': int(request.form.get('order', 0))
        }
        archive = db_helper.create_archive(data)

        # 다중 이미지 업로드 처리
        if archive and 'images' in request.files:
            files = request.files.getlist('images')
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    image_url = save_file(file, 'archives')
                    if image_url:
                        image_data = {
                            'archive_id': archive['id'],
                            'image_url': image_url,
                            'order': idx
                        }
                        db_helper.create_archive_image(image_data)

        flash('아카이브가 추가되었습니다.', 'success')
        return redirect(url_for('admin_archives'))
    return render_template('admin/archive_form.html')

@app.route('/admin/archives/edit/<int:archive_id>', methods=['GET', 'POST'])
@login_required
def admin_archive_edit(archive_id):
    archive = db_helper.get_archive_by_id(archive_id)
    if not archive:
        flash('아카이브를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_archives'))

    if request.method == 'POST':
        thumbnail_url = archive.get('thumbnail_url')
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            saved_path = save_file(file, 'archives')
            if saved_path:
                thumbnail_url = saved_path
        if request.form.get('thumbnail_url_text'):
            thumbnail_url = request.form.get('thumbnail_url_text')

        data = {
            'title': request.form['title'],
            'description': request.form.get('description'),
            'event_date': request.form['event_date'],
            'category': request.form.get('category'),
            'location': request.form.get('location'),
            'thumbnail_url': thumbnail_url,
            'is_active': request.form.get('is_active') == 'on',
            'order': int(request.form.get('order', 0))
        }
        db_helper.update_archive(archive_id, data)

        # 새로운 이미지 추가
        if 'images' in request.files:
            files = request.files.getlist('images')
            current_images = archive.get('images', [])
            current_max_order = max([img.get('order', 0) for img in current_images], default=-1)
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    image_url = save_file(file, 'archives')
                    if image_url:
                        image_data = {
                            'archive_id': archive_id,
                            'image_url': image_url,
                            'order': current_max_order + idx + 1
                        }
                        db_helper.create_archive_image(image_data)

        flash('아카이브가 수정되었습니다.', 'success')
        return redirect(url_for('admin_archives'))
    return render_template('admin/archive_form.html', archive=archive)

@app.route('/admin/archives/delete/<int:archive_id>', methods=['POST'])
@login_required
def admin_archive_delete(archive_id):
    db_helper.delete_archive(archive_id)
    flash('아카이브가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_archives'))

@app.route('/admin/archives/<int:archive_id>/images/delete/<int:image_id>', methods=['POST'])
@login_required
def admin_archive_image_delete(archive_id, image_id):
    db_helper.delete_archive_image(image_id)
    flash('이미지가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_archive_edit', archive_id=archive_id))

# ============================================
# 성능 최적화: 캐싱 헤더 추가
# ============================================

@app.after_request
def add_header(response):
    """응답에 캐싱 및 보안 헤더 추가"""
    # 정적 파일 캐싱 (1년)
    if 'static' in request.path or any(ext in request.path for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2']):
        response.cache_control.max_age = 31536000  # 1년
        response.cache_control.public = True
    # HTML 페이지는 짧은 캐싱
    elif request.path.endswith('.html') or request.path == '/':
        response.cache_control.max_age = 300  # 5분
        response.cache_control.public = True

    # 보안 헤더
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response

# ============================================
# CLI 명령어
# ============================================

@app.cli.command()
def init_db():
    """데이터베이스 초기화"""
    print("Supabase를 사용하고 있습니다. supabase_schema.sql을 Supabase에 적용해주세요.")
    print("\n관리자 계정은 Supabase의 admins 테이블에서 직접 관리하세요.")
    print("예시:")
    print("  INSERT INTO admins (username, password_hash, name, created_at)")
    print("  VALUES ('your_username', 'scrypt:...', '이름', NOW());")
    print("\n비밀번호 해시 생성:")
    print("  from werkzeug.security import generate_password_hash")
    print("  print(generate_password_hash('your_password'))")

if __name__ == '__main__':
    # 기본 파일 초기화
    init_default_files()

    port = int(os.environ.get('PORT', 1992))
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True, reloader_type='stat')
