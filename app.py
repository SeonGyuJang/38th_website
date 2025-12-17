from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Admin, Schedule, Promise, PromiseProgress, MeetingMinutes, Regulation, Program, Organization, Banner
from config import Config
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# ============ Public Routes ============

@app.route('/')
def index():
    """홈페이지"""
    # 배너 가져오기 (이벤트 배너 우선, 없으면 기본 배너)
    banner = Banner.query.filter_by(is_active=True, is_event_banner=True).order_by(Banner.order).first()
    if not banner:
        banner = Banner.query.filter_by(is_active=True, is_event_banner=False).order_by(Banner.order).first()

    # 조직도 데이터 구조화
    organization_data = None
    all_members = Organization.query.order_by(Organization.order).all()
    if all_members:
        organization_data = {
            'presidents': [],  # 총학생회장, 부총학생회장
            'chairs': [],  # 위원장들
            'departments': {}  # 부서별 그룹
        }

        for member in all_members:
            position = member.position.lower()
            if '총학생회장' in position or '회장' in position:
                organization_data['presidents'].append(member)
            elif '위원장' in position:
                organization_data['chairs'].append(member)
            elif member.department:
                if member.department not in organization_data['departments']:
                    organization_data['departments'][member.department] = []
                organization_data['departments'][member.department].append(member)

    # 공약 이행률 계산
    promises_list = Promise.query.all()
    promise_rate = 0
    if promises_list:
        total_progress = sum(p.progress_rate for p in promises_list)
        promise_rate = total_progress / len(promises_list)

    # 상위 공약 3개
    top_promises = Promise.query.order_by(Promise.progress_rate.desc(), Promise.order).limit(3).all()

    # 최근 회의록 3개
    recent_minutes = MeetingMinutes.query.order_by(MeetingMinutes.meeting_date.desc()).limit(3).all()

    # 최근 회칙 3개
    recent_regulations = Regulation.query.order_by(Regulation.order).limit(3).all()

    return render_template('index.html',
                         banner=banner,
                         organization_data=organization_data,
                         promise_rate=promise_rate,
                         top_promises=top_promises,
                         recent_minutes=recent_minutes,
                         recent_regulations=recent_regulations)


@app.route('/schedule')
def schedule():
    """일정 페이지"""
    schedules = Schedule.query.order_by(Schedule.start_date.desc()).all()
    return render_template('schedule.html', schedules=schedules)


@app.route('/organization')
def organization():
    """조직도 페이지"""
    members = Organization.query.order_by(Organization.order).all()
    return render_template('organization.html', members=members)


@app.route('/promises')
def promises():
    """공약 페이지"""
    promises_list = Promise.query.order_by(Promise.order).all()

    # 카테고리별로 그룹화
    categories = {}
    for promise in promises_list:
        if promise.category not in categories:
            categories[promise.category] = []
        categories[promise.category].append(promise)

    # 전체 이행률 계산
    total_progress = sum(p.progress_rate for p in promises_list) / len(promises_list) if promises_list else 0

    return render_template('promises.html', categories=categories, total_progress=round(total_progress))


@app.route('/promises/<int:promise_id>')
def promise_detail(promise_id):
    """공약 상세 페이지"""
    promise = Promise.query.get_or_404(promise_id)
    progress_updates = PromiseProgress.query.filter_by(promise_id=promise_id).order_by(PromiseProgress.date.desc()).all()
    return render_template('promise_detail.html', promise=promise, progress_updates=progress_updates)


@app.route('/minutes')
def minutes():
    """회의록 페이지"""
    meeting_minutes = MeetingMinutes.query.order_by(MeetingMinutes.meeting_date.desc()).all()
    return render_template('minutes.html', minutes=meeting_minutes)


@app.route('/minutes/<int:minute_id>')
def minute_detail(minute_id):
    """회의록 상세 페이지"""
    minute = MeetingMinutes.query.get_or_404(minute_id)
    return render_template('minute_detail.html', minute=minute)


@app.route('/regulations')
def regulations():
    """회칙 페이지"""
    regulations_list = Regulation.query.order_by(Regulation.category, Regulation.order).all()

    # 카테고리별로 그룹화
    categories = {}
    for regulation in regulations_list:
        if regulation.category not in categories:
            categories[regulation.category] = []
        categories[regulation.category].append(regulation)

    return render_template('regulations.html', categories=categories)


@app.route('/programs')
def programs():
    """교내 프로그램 페이지"""
    programs_list = Program.query.filter_by(is_active=True).order_by(Program.created_at.desc()).all()
    return render_template('programs.html', programs=programs_list)


# ============ Admin Authentication Routes ============

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """관리자 로그인"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('admin_dashboard'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    """관리자 로그아웃"""
    logout_user()
    return redirect(url_for('index'))


# ============ Admin Dashboard Routes ============

@app.route('/admin')
@login_required
def admin_dashboard():
    """관리자 대시보드"""
    stats = {
        'schedules': Schedule.query.count(),
        'promises': Promise.query.count(),
        'minutes': MeetingMinutes.query.count(),
        'programs': Program.query.filter_by(is_active=True).count()
    }
    return render_template('admin/dashboard.html', stats=stats)


# ============ Admin Schedule Management ============

@app.route('/admin/schedules')
@login_required
def admin_schedules():
    """관리자 일정 관리"""
    schedules = Schedule.query.order_by(Schedule.start_date.desc()).all()
    return render_template('admin/schedules.html', schedules=schedules)


@app.route('/admin/schedules/add', methods=['GET', 'POST'])
@login_required
def admin_schedule_add():
    """일정 추가"""
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
    """일정 수정"""
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
    """일정 삭제"""
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('일정이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_schedules'))


# ============ Admin Promise Management ============

@app.route('/admin/promises')
@login_required
def admin_promises():
    """관리자 공약 관리"""
    promises_list = Promise.query.order_by(Promise.order).all()
    return render_template('admin/promises.html', promises=promises_list)


@app.route('/admin/promises/add', methods=['GET', 'POST'])
@login_required
def admin_promise_add():
    """공약 추가"""
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
    """공약 수정"""
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
    """공약 삭제"""
    promise = Promise.query.get_or_404(promise_id)
    db.session.delete(promise)
    db.session.commit()
    flash('공약이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_promises'))


@app.route('/admin/promises/<int:promise_id>/progress/add', methods=['GET', 'POST'])
@login_required
def admin_promise_progress_add(promise_id):
    """공약 진행상황 추가"""
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


# ============ Admin Minutes Management ============

@app.route('/admin/minutes')
@login_required
def admin_minutes():
    """관리자 회의록 관리"""
    meeting_minutes = MeetingMinutes.query.order_by(MeetingMinutes.meeting_date.desc()).all()
    return render_template('admin/minutes.html', minutes=meeting_minutes)


@app.route('/admin/minutes/add', methods=['GET', 'POST'])
@login_required
def admin_minute_add():
    """회의록 추가"""
    if request.method == 'POST':
        minute = MeetingMinutes(
            title=request.form['title'],
            meeting_type=request.form.get('meeting_type'),
            meeting_date=datetime.strptime(request.form['meeting_date'], '%Y-%m-%d'),
            attendees=request.form.get('attendees'),
            agenda=request.form.get('agenda'),
            content=request.form['content'],
            decisions=request.form.get('decisions'),
            file_url=request.form.get('file_url')
        )
        db.session.add(minute)
        db.session.commit()
        flash('회의록이 추가되었습니다.', 'success')
        return redirect(url_for('admin_minutes'))

    return render_template('admin/minute_form.html')


@app.route('/admin/minutes/edit/<int:minute_id>', methods=['GET', 'POST'])
@login_required
def admin_minute_edit(minute_id):
    """회의록 수정"""
    minute = MeetingMinutes.query.get_or_404(minute_id)

    if request.method == 'POST':
        minute.title = request.form['title']
        minute.meeting_type = request.form.get('meeting_type')
        minute.meeting_date = datetime.strptime(request.form['meeting_date'], '%Y-%m-%d')
        minute.attendees = request.form.get('attendees')
        minute.agenda = request.form.get('agenda')
        minute.content = request.form['content']
        minute.decisions = request.form.get('decisions')
        minute.file_url = request.form.get('file_url')

        db.session.commit()
        flash('회의록이 수정되었습니다.', 'success')
        return redirect(url_for('admin_minutes'))

    return render_template('admin/minute_form.html', minute=minute)


@app.route('/admin/minutes/delete/<int:minute_id>', methods=['POST'])
@login_required
def admin_minute_delete(minute_id):
    """회의록 삭제"""
    minute = MeetingMinutes.query.get_or_404(minute_id)
    db.session.delete(minute)
    db.session.commit()
    flash('회의록이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_minutes'))


# ============ Admin Programs Management ============

@app.route('/admin/programs')
@login_required
def admin_programs():
    """관리자 프로그램 관리"""
    programs_list = Program.query.order_by(Program.created_at.desc()).all()
    return render_template('admin/programs.html', programs=programs_list)


@app.route('/admin/programs/add', methods=['GET', 'POST'])
@login_required
def admin_program_add():
    """프로그램 추가"""
    if request.method == 'POST':
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
            image_url=request.form.get('image_url'),
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
    """프로그램 수정"""
    program = Program.query.get_or_404(program_id)

    if request.method == 'POST':
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
        program.image_url = request.form.get('image_url')
        program.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash('프로그램이 수정되었습니다.', 'success')
        return redirect(url_for('admin_programs'))

    return render_template('admin/program_form.html', program=program)


@app.route('/admin/programs/delete/<int:program_id>', methods=['POST'])
@login_required
def admin_program_delete(program_id):
    """프로그램 삭제"""
    program = Program.query.get_or_404(program_id)
    db.session.delete(program)
    db.session.commit()
    flash('프로그램이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_programs'))


# ============ Admin Banner Management ============

@app.route('/admin/banners')
@login_required
def admin_banners():
    """관리자 배너 관리"""
    banners = Banner.query.order_by(Banner.order).all()
    return render_template('admin/banners.html', banners=banners)


@app.route('/admin/banners/add', methods=['GET', 'POST'])
@login_required
def admin_banner_add():
    """배너 추가"""
    if request.method == 'POST':
        banner = Banner(
            title=request.form['title'],
            image_url=request.form['image_url'],
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
    """배너 수정"""
    banner = Banner.query.get_or_404(banner_id)

    if request.method == 'POST':
        banner.title = request.form['title']
        banner.image_url = request.form['image_url']
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
    """배너 삭제"""
    banner = Banner.query.get_or_404(banner_id)
    db.session.delete(banner)
    db.session.commit()
    flash('배너가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_banners'))


# ============ Admin Organization Management ============

@app.route('/admin/organization')
@login_required
def admin_organization():
    """관리자 조직도 관리"""
    members = Organization.query.order_by(Organization.order).all()
    return render_template('admin/organization.html', members=members)


@app.route('/admin/organization/add', methods=['GET', 'POST'])
@login_required
def admin_organization_add():
    """조직도 멤버 추가"""
    if request.method == 'POST':
        member = Organization(
            name=request.form['name'],
            position=request.form['position'],
            department=request.form.get('department'),
            major=request.form.get('major'),
            student_id=request.form.get('student_id'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            photo_url=request.form.get('photo_url'),
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
    """조직도 멤버 수정"""
    member = Organization.query.get_or_404(member_id)

    if request.method == 'POST':
        member.name = request.form['name']
        member.position = request.form['position']
        member.department = request.form.get('department')
        member.major = request.form.get('major')
        member.student_id = request.form.get('student_id')
        member.phone = request.form.get('phone')
        member.email = request.form.get('email')
        member.photo_url = request.form.get('photo_url')
        member.order = int(request.form.get('order', 0))

        db.session.commit()
        flash('조직도 멤버가 수정되었습니다.', 'success')
        return redirect(url_for('admin_organization'))

    return render_template('admin/organization_form.html', member=member)


@app.route('/admin/organization/delete/<int:member_id>', methods=['POST'])
@login_required
def admin_organization_delete(member_id):
    """조직도 멤버 삭제"""
    member = Organization.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('조직도 멤버가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_organization'))


# ============ Admin Regulations Management ============

@app.route('/admin/regulations')
@login_required
def admin_regulations():
    """관리자 회칙 관리"""
    regulations_list = Regulation.query.order_by(Regulation.category, Regulation.order).all()
    return render_template('admin/regulations.html', regulations=regulations_list)


@app.route('/admin/regulations/add', methods=['GET', 'POST'])
@login_required
def admin_regulation_add():
    """회칙 추가"""
    if request.method == 'POST':
        regulation = Regulation(
            category=request.form['category'],
            title=request.form['title'],
            content=request.form['content'],
            file_url=request.form.get('file_url'),
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
    """회칙 수정"""
    regulation = Regulation.query.get_or_404(regulation_id)

    if request.method == 'POST':
        regulation.category = request.form['category']
        regulation.title = request.form['title']
        regulation.content = request.form['content']
        regulation.file_url = request.form.get('file_url')
        regulation.order = int(request.form.get('order', 0))

        db.session.commit()
        flash('회칙이 수정되었습니다.', 'success')
        return redirect(url_for('admin_regulations'))

    return render_template('admin/regulation_form.html', regulation=regulation)


@app.route('/admin/regulations/delete/<int:regulation_id>', methods=['POST'])
@login_required
def admin_regulation_delete(regulation_id):
    """회칙 삭제"""
    regulation = Regulation.query.get_or_404(regulation_id)
    db.session.delete(regulation)
    db.session.commit()
    flash('회칙이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_regulations'))


# ============ Initialize Database ============

@app.cli.command()
def init_db():
    """데이터베이스 초기화"""
    with app.app_context():
        db.create_all()

        # 기본 관리자 계정 생성 (username: admin, password: admin)
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', name='관리자')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print('기본 관리자 계정이 생성되었습니다. (ID: admin, PW: admin)')


if __name__ == '__main__':
    # 포트 번호를 환경 변수로 설정 가능
    port = int(os.environ.get('PORT', 1234))

    # watchdog 호환성 문제 해결: stat reloader 사용
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True, reloader_type='stat')
