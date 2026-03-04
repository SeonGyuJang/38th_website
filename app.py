from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_compress import Compress
from werkzeug.utils import secure_filename
from config import Config
from database import init_supabase
from supabase_helpers import SupabaseHelper
from storage_helper import storage
from admin_user import AdminUser
from datetime import datetime, date, timedelta
import tempfile
import os
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
# 이메일 발송 함수
# ============================================

def send_email(to_email, subject, html_body):
    """SMTP를 통해 이메일 발송"""
    mail_username = app.config.get('MAIL_USERNAME')
    mail_password = app.config.get('MAIL_PASSWORD')
    mail_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = app.config.get('MAIL_PORT', 587)
    mail_use_tls = app.config.get('MAIL_USE_TLS', True)
    mail_sender = app.config.get('MAIL_DEFAULT_SENDER') or mail_username

    if not mail_username or not mail_password:
        print(f'[이메일 미발송] MAIL_USERNAME/MAIL_PASSWORD 미설정. 수신자: {to_email}, 제목: {subject}')
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_sender
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_sender, to_email, msg.as_string())
        print(f'[이메일 발송 성공] 수신자: {to_email}, 제목: {subject}')
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f'[이메일 발송 실패] 인증 오류 — Gmail 앱 비밀번호를 확인하세요. 오류: {e}')
        return False
    except smtplib.SMTPException as e:
        print(f'[이메일 발송 실패] SMTP 오류: {e}')
        return False
    except Exception as e:
        print(f'[이메일 발송 실패] 수신자: {to_email}, 오류: {type(e).__name__}: {e}')
        return False


def send_booking_submitted_user_email(booking):
    """대관 신청 완료 이메일 (신청자에게)"""
    subject = f'[총학생회] 회의실 {booking["room_number"]}호 대관 신청이 접수되었습니다'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #961A32; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">회의실 대관 신청 접수 확인</p>
      </div>
      <div style="background: white; padding: 40px;">
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">대관 신청이 접수되었습니다</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">신청하신 내용을 검토 후 승인 여부를 안내해 드리겠습니다.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">신청자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">회의실 {booking['room_number']}호</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['booking_date']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">시간</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['start_time']} ~ {booking['end_time']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">사용 목적</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['purpose']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">현재 상태</td><td style="padding: 12px 16px;"><span style="background: #FFF3CD; color: #856404; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 700;">검토 중</span></td></tr>
        </table>
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">승인 여부는 별도의 이메일로 안내됩니다. 문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2025 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_booking_admin_notification_email(booking):
    """새 대관 신청 알림 이메일 (관리자에게)"""
    admin_email = app.config.get('ADMIN_EMAIL')
    if not admin_email:
        return False
    subject = f'[총학생회] 새로운 회의실 대관 신청 - {booking["applicant_name"]} (회의실 {booking["room_number"]}호)'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #1a1a1a; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">관리자 알림</h1>
        <p style="color: rgba(255,255,255,0.7); margin: 8px 0 0 0; font-size: 14px;">새로운 회의실 대관 신청이 접수되었습니다</p>
      </div>
      <div style="background: white; padding: 40px;">
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 24px 0;">신청 내용</h2>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">신청자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">이메일</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_email']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">연락처</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('applicant_phone') or '-'}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">소속</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('organization') or '-'}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">회의실 {booking['room_number']}호</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['booking_date']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">시간</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['start_time']} ~ {booking['end_time']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">인원</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('attendees', 1)}명</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">사용 목적</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['purpose']}</td></tr>
        </table>
        <div style="margin-top: 24px; padding: 16px; background: #fff3cd; border-radius: 8px;">
          <p style="margin: 0; color: #856404; font-size: 14px; font-weight: 600;">관리자 페이지에서 승인/거절 처리를 해주세요.</p>
        </div>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2025 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(admin_email, subject, html)


def send_booking_approved_email(booking):
    """대관 신청 승인 이메일 (신청자에게)"""
    subject = f'[총학생회] 회의실 {booking["room_number"]}호 대관 신청이 승인되었습니다'
    admin_note = booking.get('admin_note')
    note_html = f'<p style="color: #444; font-size: 14px; margin: 16px 0 0 0;"><strong>관리자 메모:</strong> {admin_note}</p>' if admin_note else ''
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #1A7F37; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">회의실 대관 신청 승인 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #d4edda; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #155724; font-weight: 700; font-size: 15px;">✓ 승인 완료</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">대관 신청이 승인되었습니다!</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">아래 일정에 회의실을 이용하실 수 있습니다.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">신청자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>회의실 {booking['room_number']}호</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['booking_date']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">시간</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['start_time']} ~ {booking['end_time']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">사용 목적</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['purpose']}</td></tr>
        </table>
        {note_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2025 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_booking_rejected_email(booking):
    """대관 신청 거절 이메일 (신청자에게)"""
    subject = f'[총학생회] 회의실 {booking["room_number"]}호 대관 신청 결과 안내'
    admin_note = booking.get('admin_note')
    note_html = f'<p style="color: #444; font-size: 14px; margin: 16px 0 0 0;"><strong>거절 사유:</strong> {admin_note}</p>' if admin_note else ''
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #6c757d; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">회의실 대관 신청 결과 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">대관 신청이 거절되었습니다</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">신청하신 내용이 이번에는 승인되지 못했습니다.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">회의실 {booking['room_number']}호</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['booking_date']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">시간</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['start_time']} ~ {booking['end_time']}</td></tr>
        </table>
        {note_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2025 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


# ============================================
# 유지보수 모드
# ============================================

MAINTENANCE_MODE_FILE = os.environ.get(
    'MAINTENANCE_MODE_FILE',
    os.path.join(tempfile.gettempdir(), 'maintenance_mode.txt')
)

def is_maintenance_mode():
    """유지보수 모드 활성화 여부 확인"""
    return os.path.exists(MAINTENANCE_MODE_FILE)

def set_maintenance_mode(enabled):
    """유지보수 모드 활성화/비활성화"""
    if enabled:
        # 파일 생성으로 유지보수 모드 활성화
        with open(MAINTENANCE_MODE_FILE, 'w') as f:
            f.write(f'Enabled at: {datetime.now()}')
        return True
    else:
        # 파일 삭제로 유지보수 모드 비활성화
        if os.path.exists(MAINTENANCE_MODE_FILE):
            os.remove(MAINTENANCE_MODE_FILE)
        return True

@app.before_request
def check_maintenance_mode():
    """
    모든 요청 전에 유지보수 모드 확인
    관리자 경로(/admin/)와 정적 파일은 제외
    """
    # 관리자 경로나 정적 파일은 유지보수 모드에서도 접근 가능
    if request.path.startswith('/admin') or request.path.startswith('/static'):
        return None

    # 유지보수 페이지 자체는 항상 접근 가능
    if request.path == '/maintenance':
        return None

    # 유지보수 모드가 활성화되어 있으면 유지보수 페이지로 리다이렉트
    if is_maintenance_mode():
        return render_template('maintenance.html'), 503

@app.route('/maintenance')
def maintenance():
    return render_template('maintenance.html'), 503

# ============================================
# 공개 페이지
# ============================================

@app.route('/')
def index():
    # 배너 로직 강화: 모든 활성 배너 노출 (캐러셀)
    banners = db_helper.get_all_banners(is_active=True)

    # 전반적인 공약 이행률 계산
    promises_list = db_helper.get_all_promises()
    promise_rate = round(sum(p.get('progress_rate', 0) for p in promises_list) / len(promises_list)) if promises_list else 0

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
    # 부서명 매핑: 축약형 → 풀네임
    DEPT_MAPPING = {
        '중집위_미디어소통국': '중앙집행위원회 미디어소통국',
        '중집위_사무국': '중앙집행위원회 사무국',
        '중집위_재정국': '중앙집행위원회 재정국',
        '기정위_문화기획국': '기획정책위원회 문화기획국',
        '기정위_대외협력국': '기획정책위원회 대외협력국',
        '기정위_정책국': '기획정책위원회 정책국',
        '인복위_홍보국': '인권/복지부 홍보국',
        '인복위_기획국': '인권/복지부 기획국',
        '인복위_사무재정국': '인권/복지부 사무재정국',
        '교복위_홍보국': '교육/복지부 홍보국',
        '교복위_기획국': '교육/복지부 기획국',
        '교복위_사무재정국': '교육/복지부 사무재정국'
    }

    # 간략 보기용 데이터 (회장단)
    presidents = db_helper.get_organizations_by_position('회장')
    # 위원장
    heads = db_helper.get_organizations_by_position('위원장')

    # 상세 보기용 데이터 (부서별 그룹화)
    all_members = db_helper.get_all_organizations()
    departments = {}
    for m in all_members:
        # 데이터 정규화: position과 department의 공백 제거
        if m.get('position'):
            m['position'] = m['position'].strip()
        if m.get('department'):
            m['department'] = m['department'].strip()
            # 축약형이면 풀네임으로 변환
            m['department'] = DEPT_MAPPING.get(m['department'], m['department'])

        dept = m.get('department') or "회장단 및 중앙기구"
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(m)

    # presidents와 heads도 정규화
    for p in presidents:
        if p.get('position'):
            p['position'] = p['position'].strip()
        if p.get('department'):
            p['department'] = p['department'].strip()
            p['department'] = DEPT_MAPPING.get(p['department'], p['department'])

    for h in heads:
        if h.get('position'):
            h['position'] = h['position'].strip()
        if h.get('department'):
            h['department'] = h['department'].strip()
            h['department'] = DEPT_MAPPING.get(h['department'], h['department'])

    return render_template('organization.html',
                           presidents=presidents,
                           heads=heads,
                           departments=departments)

@app.route('/promises')
def promises():
    # N+1 쿼리 방지: 모든 데이터를 한 번에 가져오기
    promises_list = db_helper.get_all_promises()
    all_progress = db_helper.get_all_promise_progress()  # 한 번에 모든 진행 상황 조회

    categories = {}
    for promise in promises_list:
        category = promise.get('category')
        if category not in categories:
            categories[category] = []
        # 그룹화된 데이터에서 해당 공약의 진행 상황 가져오기 (DB 쿼리 없음)
        promise['progress_updates'] = all_progress.get(promise['id'], [])
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

@app.route('/api/promise/<int:promise_id>/details')
def api_promise_details(promise_id):
    """공약 상세 정보 API (Ajax 요청용)"""
    promise = db_helper.get_promise_by_id(promise_id)
    if not promise:
        return jsonify({'error': 'Promise not found'}), 404

    progress_updates = db_helper.get_promise_progress(promise_id)

    # 날짜 포맷팅
    formatted_updates = []
    for update in progress_updates:
        formatted_updates.append({
            'id': update['id'],
            'title': update['title'],
            'content': update['content'],
            'date': update['date'].strftime('%Y년 %m월 %d일')
        })

    return jsonify({
        'id': promise['id'],
        'detailed_description': promise.get('detailed_description', ''),
        'progress_updates': formatted_updates
    })

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
# 회의실 대관
# ============================================

@app.route('/meeting-room')
def meeting_room():
    today = date.today()
    max_date = today + timedelta(days=14)  # 최대 2주 앞까지 예약 가능

    # 선택한 날짜 (기본: 오늘)
    selected_date_str = request.args.get('date', today.strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today

    # 2주 초과 날짜 접근 시 max_date로 클램핑
    if selected_date > max_date:
        selected_date = max_date
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    # 선택한 날짜가 속한 주의 월~일 계산
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    prev_week = selected_date - timedelta(days=7)
    next_week = selected_date + timedelta(days=7)

    # 선택한 날짜의 대관 현황 조회
    bookings = db_helper.get_bookings_by_date(selected_date_str)

    # 회의실별 예약 정보 구성
    rooms = {1: [], 2: [], 3: [], 4: []}
    for b in bookings:
        rn = b.get('room_number')
        if rn in rooms:
            rooms[rn].append(b)

    return render_template('meeting_room.html',
                           rooms=rooms,
                           selected_date=selected_date,
                           today=today,
                           max_date=max_date,
                           week_dates=week_dates,
                           prev_week=prev_week,
                           next_week=next_week)


@app.route('/meeting-room/book', methods=['POST'])
def meeting_room_book():
    room_number = request.form.get('room_number', type=int)
    applicant_name = request.form.get('applicant_name', '').strip()
    applicant_email = request.form.get('applicant_email', '').strip()
    applicant_phone = request.form.get('applicant_phone', '').strip()
    organization = request.form.get('organization', '').strip()
    purpose = request.form.get('purpose', '').strip()
    booking_date = request.form.get('booking_date', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    attendees = request.form.get('attendees', 1, type=int)

    # 기본 유효성 검사
    if not all([room_number, applicant_name, applicant_email, purpose, booking_date, start_time, end_time]):
        flash('필수 항목을 모두 입력해주세요.', 'error')
        return redirect(url_for('meeting_room', date=booking_date))

    if room_number not in [1, 2, 3, 4]:
        flash('올바른 회의실을 선택해주세요.', 'error')
        return redirect(url_for('meeting_room', date=booking_date))

    if start_time >= end_time:
        flash('종료 시간은 시작 시간보다 늦어야 합니다.', 'error')
        return redirect(url_for('meeting_room', date=booking_date))

    # 날짜 유효성 (과거 날짜 불가, 2주 초과 불가)
    try:
        bd = datetime.strptime(booking_date, '%Y-%m-%d').date()
        today_d = date.today()
        max_date = today_d + timedelta(days=14)
        if bd < today_d:
            flash('오늘 이후 날짜만 신청 가능합니다.', 'error')
            return redirect(url_for('meeting_room', date=booking_date))
        if bd > max_date:
            flash('대관은 오늘부터 최대 2주 앞까지만 신청 가능합니다.', 'error')
            return redirect(url_for('meeting_room', date=booking_date))
    except ValueError:
        flash('올바른 날짜를 입력해주세요.', 'error')
        return redirect(url_for('meeting_room'))

    # 시간 중복 확인 (같은 날짜 같은 회의실)
    existing_bookings = db_helper.get_bookings_by_date(booking_date)
    for eb in existing_bookings:
        if eb.get('room_number') == room_number and eb.get('status') in ['pending', 'approved']:
            es = eb.get('start_time', '')
            ee = eb.get('end_time', '')
            if not (end_time <= es or start_time >= ee):
                flash(f'선택하신 시간대({start_time}~{end_time})에 이미 신청된 대관이 있습니다. 다른 시간을 선택해주세요.', 'error')
                return redirect(url_for('meeting_room', date=booking_date))

    data = {
        'room_number': room_number,
        'applicant_name': applicant_name,
        'applicant_email': applicant_email,
        'applicant_phone': applicant_phone or None,
        'organization': organization or None,
        'purpose': purpose,
        'booking_date': booking_date,
        'start_time': start_time,
        'end_time': end_time,
        'attendees': attendees,
        'status': 'pending'
    }
    booking = db_helper.create_meeting_room_booking(data)

    if booking:
        # 이메일 발송
        user_email_sent = send_booking_submitted_user_email(booking)
        send_booking_admin_notification_email(booking)
        if user_email_sent:
            flash('대관 신청이 완료되었습니다. 확인 이메일을 발송했습니다. 승인 후 이메일로 안내해 드립니다.', 'success')
        else:
            flash('대관 신청이 완료되었습니다. 승인 후 이메일로 안내해 드립니다. (확인 이메일 발송에 실패했습니다)', 'success')
    else:
        flash('대관 신청 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')

    return redirect(url_for('meeting_room', date=booking_date))


@app.route('/api/meeting-room/availability')
def api_meeting_room_availability():
    """특정 날짜의 회의실 가용성 API"""
    booking_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    bookings = db_helper.get_bookings_by_date(booking_date)
    result = {1: [], 2: [], 3: [], 4: []}
    for b in bookings:
        rn = b.get('room_number')
        if rn in result:
            result[rn].append({
                'start_time': b.get('start_time'),
                'end_time': b.get('end_time'),
                'status': b.get('status')
            })
    return jsonify(result)


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
        'programs': db_helper.count_active_programs(),
        'pending_bookings': db_helper.count_pending_bookings()
    }
    maintenance_mode = is_maintenance_mode()
    return render_template('admin/dashboard.html', stats=stats, maintenance_mode=maintenance_mode)

@app.route('/admin/maintenance/toggle', methods=['POST'])
@login_required
def admin_maintenance_toggle():
    """유지보수 모드 토글 (Super Admin 전용)"""
    # Super Admin 권한 체크 (is_super_admin이 True인 경우만 허용)
    if not current_user.is_super_admin:
        flash('Super Admin만 유지보수 모드를 변경할 수 있습니다.', 'error')
        return redirect(url_for('admin_dashboard'))

    current_mode = is_maintenance_mode()
    new_mode = not current_mode

    if set_maintenance_mode(new_mode):
        if new_mode:
            flash('유지보수 모드가 활성화되었습니다. 관리자를 제외한 모든 사용자는 유지보수 페이지를 보게 됩니다.', 'success')
        else:
            flash('유지보수 모드가 비활성화되었습니다. 모든 사용자가 정상적으로 사이트에 접근할 수 있습니다.', 'success')
    else:
        flash('유지보수 모드 변경에 실패했습니다.', 'error')

    return redirect(url_for('admin_dashboard'))

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
    all_progress = db_helper.get_all_promise_progress()
    # 각 공약의 진행 상황 추가
    for promise in promises_list:
        promise['progress_updates'] = all_progress.get(promise['id'], [])
    return render_template('admin/promises.html', promises=promises_list)

@app.route('/admin/promises/add', methods=['GET', 'POST'])
@login_required
def admin_promise_add():
    if request.method == 'POST':
        # 텍스트 필드는 앞뒤 공백 제거 (줄바꿈은 유지)
        description = request.form['description'].strip()
        detailed_description = request.form.get('detailed_description', '').strip() if request.form.get('detailed_description') else None

        data = {
            'category': request.form['category'].strip(),
            'title': request.form['title'].strip(),
            'description': description,
            'detailed_description': detailed_description,
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
        # 텍스트 필드는 앞뒤 공백 제거 (줄바꿈은 유지)
        description = request.form['description'].strip()
        detailed_description = request.form.get('detailed_description', '').strip() if request.form.get('detailed_description') else None

        data = {
            'category': request.form['category'].strip(),
            'title': request.form['title'].strip(),
            'description': description,
            'detailed_description': detailed_description,
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
        # 텍스트 필드는 앞뒤 공백 제거 (줄바꿈은 유지)
        data = {
            'promise_id': promise_id,
            'title': request.form['title'].strip(),
            'content': request.form['content'].strip(),
            'date': request.form['date']
        }
        db_helper.create_promise_progress(data)
        flash('진행상황이 추가되었습니다.', 'success')
        return redirect(url_for('admin_promises'))
    return render_template('admin/promise_progress_form.html', promise=promise)

@app.route('/admin/promises/progress/<int:progress_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_promise_progress_edit(progress_id):
    progress = db_helper.get_promise_progress_by_id(progress_id)
    if not progress:
        flash('진행상황을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_promises'))

    promise = db_helper.get_promise_by_id(progress['promise_id'])
    if not promise:
        flash('공약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_promises'))

    if request.method == 'POST':
        data = {
            'title': request.form['title'].strip(),
            'content': request.form['content'].strip(),
            'date': request.form['date']
        }
        db_helper.update_promise_progress(progress_id, data)
        flash('진행상황이 수정되었습니다.', 'success')
        return redirect(url_for('admin_promises'))

    return render_template('admin/promise_progress_form.html', promise=promise, progress=progress, is_edit=True)

@app.route('/admin/promises/progress/<int:progress_id>/delete', methods=['POST'])
@login_required
def admin_promise_progress_delete(progress_id):
    if db_helper.delete_promise_progress(progress_id):
        flash('진행상황이 삭제되었습니다.', 'success')
    else:
        flash('진행상황 삭제에 실패했습니다.', 'error')
    return redirect(url_for('admin_promises'))

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
    # 부서명 매핑: 축약형 → 풀네임
    DEPT_MAPPING = {
        '중집위_미디어소통국': '중앙집행위원회 미디어소통국',
        '중집위_사무국': '중앙집행위원회 사무국',
        '중집위_재정국': '중앙집행위원회 재정국',
        '기정위_문화기획국': '기획정책위원회 문화기획국',
        '기정위_대외협력국': '기획정책위원회 대외협력국',
        '기정위_정책국': '기획정책위원회 정책국',
        '인복위_홍보국': '인권/복지부 홍보국',
        '인복위_기획국': '인권/복지부 기획국',
        '인복위_사무재정국': '인권/복지부 사무재정국',
        '교복위_홍보국': '교육/복지부 홍보국',
        '교복위_기획국': '교육/복지부 기획국',
        '교복위_사무재정국': '교육/복지부 사무재정국'
    }

    member = db_helper.get_organization_by_id(member_id)
    if not member:
        flash('조직도 멤버를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_organization'))

    # 기존 데이터의 department를 풀네임으로 변환 (폼에서 올바르게 선택되도록)
    if member.get('department'):
        member['department'] = DEPT_MAPPING.get(member['department'], member['department'])

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
        # 새 파일이 업로드되면 우선적으로 사용
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename:  # 파일이 실제로 선택되었는지 확인
                saved_path = save_file(file, 'archives')
                if saved_path:
                    thumbnail_url = saved_path
        # URL 텍스트가 입력되면 사용 (빈 문자열이 아닐 때만)
        thumbnail_url_input = request.form.get('thumbnail_url_text', '').strip()
        if thumbnail_url_input:
            thumbnail_url = thumbnail_url_input

        data = {
            'title': request.form['title'],
            'description': request.form.get('description', '').strip(),
            'event_date': request.form['event_date'],
            'category': request.form.get('category', '').strip(),
            'location': request.form.get('location', '').strip(),
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
# 히스토리 로그
# ============================================

@app.route('/admin/history')
@login_required
def admin_history():
    history_logs = db_helper.get_all_history_logs()
    return render_template('admin/history.html', history_logs=history_logs)

@app.route('/admin/history/add', methods=['POST'])
@login_required
def admin_history_add():
    worker_name = request.form.get('worker_name', '').strip()
    work_content = request.form.get('work_content', '').strip()

    if not worker_name or not work_content:
        flash('작업자와 작업 내용을 모두 입력해주세요.', 'error')
        return redirect(url_for('admin_history'))

    data = {
        'worker_name': worker_name,
        'work_content': work_content,
        'created_at': datetime.now().isoformat()
    }
    db_helper.create_history_log(data)
    flash('히스토리 로그가 등록되었습니다.', 'success')
    return redirect(url_for('admin_history'))

@app.route('/admin/history/check/<int:log_id>', methods=['POST'])
@login_required
def admin_history_check(log_id):
    if not current_user.is_super_admin:
        flash('Super Admin만 확인 표시를 할 수 있습니다.', 'error')
        return redirect(url_for('admin_history'))

    history_log = db_helper.get_history_log_by_id(log_id)
    if not history_log:
        flash('히스토리 로그를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_history'))

    is_checked = not bool(history_log.get('is_checked'))
    data = {
        'is_checked': is_checked,
        'checked_by': current_user.name if is_checked else None,
        'checked_at': datetime.now().isoformat() if is_checked else None
    }
    db_helper.update_history_log(log_id, data)
    flash('확인 표시가 변경되었습니다.', 'success')
    return redirect(url_for('admin_history'))

@app.route('/admin/history/delete/<int:log_id>', methods=['POST'])
@login_required
def admin_history_delete(log_id):
    if not current_user.is_super_admin:
        flash('Super Admin만 히스토리를 삭제할 수 있습니다.', 'error')
        return redirect(url_for('admin_history'))

    history_log = db_helper.get_history_log_by_id(log_id)
    if not history_log:
        flash('히스토리 로그를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_history'))

    db_helper.delete_history_log(log_id)
    flash('히스토리 로그가 삭제되었습니다.', 'success')
    return redirect(url_for('admin_history'))

# ============================================
# 회의실 대관 관리
# ============================================

@app.route('/admin/meeting-rooms')
@login_required
def admin_meeting_rooms():
    status_filter = request.args.get('status', '')
    if status_filter in ['pending', 'approved', 'rejected']:
        bookings = db_helper.get_all_meeting_room_bookings(status=status_filter)
    else:
        bookings = db_helper.get_all_meeting_room_bookings()
    return render_template('admin/meeting_rooms.html', bookings=bookings, status_filter=status_filter)


@app.route('/admin/meeting-rooms/approve/<int:booking_id>', methods=['POST'])
@login_required
def admin_meeting_room_approve(booking_id):
    booking = db_helper.get_meeting_room_booking_by_id(booking_id)
    if not booking:
        flash('대관 신청을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_meeting_rooms'))

    admin_note = request.form.get('admin_note', '').strip()
    data = {
        'status': 'approved',
        'admin_note': admin_note or None,
        'updated_at': datetime.now().isoformat()
    }
    updated = db_helper.update_meeting_room_booking(booking_id, data)
    if updated:
        email_data = {**booking, 'status': 'approved', 'admin_note': admin_note}
        email_sent = send_booking_approved_email(email_data)
        if email_sent:
            flash(f'회의실 {booking["room_number"]}호 대관 신청이 승인되었습니다. 신청자에게 이메일이 발송되었습니다.', 'success')
        else:
            flash(f'회의실 {booking["room_number"]}호 대관 신청이 승인되었습니다. (이메일 발송 실패 — 서버 로그를 확인하세요)', 'warning')
    else:
        flash('승인 처리 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_meeting_rooms'))


@app.route('/admin/meeting-rooms/reject/<int:booking_id>', methods=['POST'])
@login_required
def admin_meeting_room_reject(booking_id):
    booking = db_helper.get_meeting_room_booking_by_id(booking_id)
    if not booking:
        flash('대관 신청을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_meeting_rooms'))

    admin_note = request.form.get('admin_note', '').strip()
    data = {
        'status': 'rejected',
        'admin_note': admin_note or None,
        'updated_at': datetime.now().isoformat()
    }
    updated = db_helper.update_meeting_room_booking(booking_id, data)
    if updated:
        email_data = {**booking, 'status': 'rejected', 'admin_note': admin_note}
        email_sent = send_booking_rejected_email(email_data)
        if email_sent:
            flash(f'회의실 {booking["room_number"]}호 대관 신청이 거절되었습니다. 신청자에게 이메일이 발송되었습니다.', 'success')
        else:
            flash(f'회의실 {booking["room_number"]}호 대관 신청이 거절되었습니다. (이메일 발송 실패 — 서버 로그를 확인하세요)', 'warning')
    else:
        flash('거절 처리 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_meeting_rooms'))


@app.route('/admin/meeting-rooms/delete/<int:booking_id>', methods=['POST'])
@login_required
def admin_meeting_room_delete(booking_id):
    try:
        ok = db_helper.delete_meeting_room_booking(booking_id)
        if ok:
            flash('대관 신청이 삭제되었습니다.', 'success')
        else:
            flash('삭제 처리 중 오류가 발생했습니다. 서버 로그를 확인하세요.', 'error')
    except Exception as e:
        print(f'[삭제 오류] booking_id={booking_id}: {e}')
        flash('삭제 처리 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_meeting_rooms'))


@app.route('/admin/email-test', methods=['GET', 'POST'])
@login_required
def admin_email_test():
    """이메일 설정 진단 및 테스트 발송"""
    config_status = {
        'MAIL_SERVER': app.config.get('MAIL_SERVER'),
        'MAIL_PORT': app.config.get('MAIL_PORT'),
        'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
        'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': '설정됨 ✓' if app.config.get('MAIL_PASSWORD') else '미설정 ✗',
        'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER'),
        'ADMIN_EMAIL': app.config.get('ADMIN_EMAIL'),
    }

    test_result = None
    if request.method == 'POST':
        to_email = request.form.get('to_email', '').strip()
        if to_email:
            ok = send_email(
                to_email,
                '[총학생회] 이메일 발송 테스트',
                '<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#f9f9f9;border-radius:12px;"><h2 style="color:#961A32;">이메일 발송 테스트 성공!</h2><p>회의실 대관 시스템의 이메일이 정상적으로 작동하고 있습니다.</p></div>'
            )
            test_result = ('success', f'{to_email} 으로 테스트 이메일 발송 성공!') if ok else ('error', '발송 실패 — 서버 로그(터미널)를 확인하세요.')

    return render_template('admin/email_test.html', config_status=config_status, test_result=test_result)


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

    port = int(os.environ.get('PORT', 1112))
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True, reloader_type='stat')
