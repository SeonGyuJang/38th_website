from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_compress import Compress
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import init_supabase
from supabase_helpers import SupabaseHelper
from storage_helper import storage
from admin_user import AdminUser
from datetime import datetime, date, timedelta
import tempfile
import os
import shutil
import threading
import smtplib
import json
import random
import string
import requests
import calendar as calendar_module
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================
# 셔틀버스 & 식단표 모듈 (kus_bus_website 포팅)
# ============================================
_menu_data = None
_is_crawling = False

def _load_menu_from_file():
    """저장된 메뉴 JSON 파일 로드"""
    global _menu_data
    menu_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'menu_data')
    student_file = os.path.join(menu_dir, 'student_menu.json')
    staff_file = os.path.join(menu_dir, 'staff_menu.json')
    try:
        if os.path.exists(student_file) and os.path.exists(staff_file):
            with open(student_file, 'r', encoding='utf-8') as f:
                student_data = json.load(f)
            with open(staff_file, 'r', encoding='utf-8') as f:
                staff_data = json.load(f)
            _menu_data = {
                'success': True,
                'data': {
                    '기간': student_data.get('기간', {}),
                    '학생식당': student_data,
                    '교직원식당': staff_data
                }
            }
            return True
    except Exception as e:
        print(f'메뉴 파일 로드 오류: {e}')
    return False

def _perform_crawling():
    """백그라운드 크롤링"""
    global _menu_data, _is_crawling
    if _is_crawling:
        return
    try:
        _is_crawling = True
        from crawling import crawl_and_save_menu
        result = crawl_and_save_menu()
        if result:
            _menu_data = {'success': True, 'data': result}
        else:
            if _menu_data is None:
                _menu_data = {'success': False, 'message': '식단표를 불러오는데 실패했습니다.'}
    except Exception as e:
        print(f'크롤링 오류: {e}')
        if _menu_data is None:
            _menu_data = {'success': False, 'message': str(e)}
    finally:
        _is_crawling = False

def _is_menu_stale():
    """저장된 메뉴 데이터가 현재 날짜 기준으로 만료됐는지 확인"""
    global _menu_data
    if not _menu_data or not _menu_data.get('success'):
        return True
    try:
        period = None
        data = _menu_data.get('data', {})
        # 학생식당 기간 정보 확인
        if '학생식당' in data and '기간' in data['학생식당']:
            period = data['학생식당']['기간']
        elif '기간' in data:
            period = data['기간']
        if not period:
            return True
        end_str = period.get('종료일', '')
        # "2026.03.08" 형식 파싱
        end_date = datetime.strptime(end_str.replace('.', '-'), '%Y-%m-%d').date()
        return date.today() > end_date
    except Exception:
        return True

def _maybe_crawl():
    """만료됐을 때만 크롤링 (스케줄러용 래퍼)"""
    if _is_menu_stale() and not _is_crawling:
        _perform_crawling()

def _init_menu_scheduler():
    """메뉴 자동 갱신 스케줄러 설정 (매일 오전 5시)"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(_maybe_crawl, trigger='cron', hour='5', minute='0')
        scheduler.start()
    except Exception as e:
        print(f'스케줄러 설정 오류: {e}')

# 서버 시작 시 메뉴 초기화
_load_menu_from_file()
# 데이터가 만료됐으면 즉시 재크롤링
if _is_menu_stale():
    threading.Thread(target=_perform_crawling, daemon=True).start()
threading.Thread(target=_init_menu_scheduler, daemon=True).start()

# ── 정적 파일 캐시 버스팅용 버전 문자열 ──────────────────────────────────────
def _get_static_version():
    """배포마다 달라지는 버전 문자열 반환 (캐시 버스팅용).
    git commit hash를 우선 사용하고, 없으면 app.py 파일 수정 시각을 사용."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    # fallback: app.py 수정 시각 (초 단위)
    try:
        return str(int(os.path.getmtime(os.path.abspath(__file__))))
    except Exception:
        return '1'

_STATIC_VER = _get_static_version()

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

# Jinja 전역 변수: 모든 템플릿에서 {{ static_ver }} 로 캐시 버스팅 버전 사용
@app.context_processor
def inject_static_version():
    return {'static_ver': _STATIC_VER}

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
# 회의실 이름 매핑
# ============================================

ROOM_DISPLAY_NAMES = {
    1: '316호',
    2: '219호',
    3: '220호',
    4: '221호',
}

def get_room_display_name(room_number):
    """room_number(1~4)를 실제 호실 이름으로 변환"""
    return ROOM_DISPLAY_NAMES.get(int(room_number), f'{room_number}호')

# ============================================
# 버스 예약 - 방향/노선 매핑
# ============================================

BUS_DIRECTIONS = {
    'sejong_to_seoul': {'label': '세종 → 서울', 'time': '07:00', 'short': '가는 버스'},
    'seoul_to_sejong': {'label': '서울 → 세종', 'time': '20:00', 'short': '오는 버스'},
}

BUS_PAYMENT_STATUS_LABELS = {
    'pending': '입금 대기',
    'paid': '입금 완료',
    'cancelled': '취소됨',
    'expired': '만료됨',
}

BUS_BOOKING_STATUS_LABELS = {
    'reserved': '예약됨 (운행 확정 대기)',
    'confirmed': '운행 확정',
    'cancelled': '취소됨',
}


def get_bus_direction_info(direction):
    """direction 코드에 대한 표시 정보 반환"""
    return BUS_DIRECTIONS.get(direction, {'label': direction, 'time': '', 'short': direction})


def generate_bus_order_number():
    """PayAction 주문번호 생성 (22자 이하, 영문/숫자)"""
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    suffix = ''.join(random.choices(string.digits, k=4))
    return f'BUS{ts}{suffix}'


BUS_BOOKING_OPEN_SETTING_KEY = 'bus_booking_open'


def is_bus_booking_open():
    """버스 예약 페이지 공개 여부. 관리자가 명시적으로 열기 전까지는 기본적으로 닫혀 있다."""
    return db_helper.get_setting(BUS_BOOKING_OPEN_SETTING_KEY, 'false') == 'true'

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

        # local_hostname을 명시하지 않으면 smtplib가 socket.getfqdn()으로 로컬 PC의
        # 호스트명을 자동으로 사용해 EHLO를 보내는데, 한글이 포함된 컴퓨터 이름(흔히
        # 한국어 Windows 환경)일 경우 ASCII 인코딩에 실패해 UnicodeEncodeError가 발생한다.
        # 메일 발송과 무관한 값이므로 고정된 ASCII 값을 명시해 우회한다.
        with smtplib.SMTP(mail_server, mail_port, timeout=10, local_hostname='localhost') as server:
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


def send_email_async(to_email, subject, html):
    """이메일을 백그라운드 스레드에서 발송 (응답 블로킹 방지)"""
    thread = threading.Thread(target=send_email, args=(to_email, subject, html), daemon=True)
    thread.start()


# ============================================
# PayAction (무통장입금 자동확인) 연동 함수
# https://payaction.app/developer
# ============================================

def payaction_create_order(order_number, amount, orderer_name, orderer_phone, orderer_email, billing_name, auto_cancel_at=None):
    """PayAction에 주문을 등록해 무통장입금 자동확인을 요청합니다.

    PAYACTION_API_KEY / PAYACTION_MALL_ID가 설정되어 있지 않으면 조용히 False를 반환합니다.
    이 경우에도 예약 자체는 '입금 대기' 상태로 생성되며, 관리자가 관리자 페이지에서
    입금을 수동으로 확인 처리할 수 있습니다.
    """
    api_key = app.config.get('PAYACTION_API_KEY')
    mall_id = app.config.get('PAYACTION_MALL_ID')
    if not api_key or not mall_id:
        print(f'[PayAction 미설정] 주문 등록 생략. order_number={order_number}')
        return False

    base_url = app.config.get('PAYACTION_BASE_URL', 'https://api.payaction.app')
    payload = {
        'order_number': order_number,
        'order_amount': amount,
        'order_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00'),
        'billing_name': billing_name,
        'orderer_name': orderer_name,
    }
    if orderer_phone:
        payload['orderer_phone_number'] = orderer_phone
    if orderer_email:
        payload['orderer_email'] = orderer_email
    if auto_cancel_at:
        payload['auto_cancel_date'] = auto_cancel_at.strftime('%Y-%m-%dT%H:%M:%S+09:00')

    try:
        resp = requests.post(
            f'{base_url}/order',
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'x-mall-id': mall_id,
            },
            timeout=10,
        )
        data = resp.json() if resp.content else {}
        if resp.status_code == 200 and data.get('status') == 'success':
            print(f'[PayAction 주문 등록 성공] order_number={order_number}')
            return True
        print(f'[PayAction 주문 등록 실패] order_number={order_number}, status={resp.status_code}, body={data}')
        return False
    except Exception as e:
        print(f'[PayAction 주문 등록 오류] order_number={order_number}: {type(e).__name__}: {e}')
        return False


def payaction_cancel_order(order_number):
    """PayAction에 등록된 주문을 취소합니다."""
    api_key = app.config.get('PAYACTION_API_KEY')
    mall_id = app.config.get('PAYACTION_MALL_ID')
    if not api_key or not mall_id:
        return False

    base_url = app.config.get('PAYACTION_BASE_URL', 'https://api.payaction.app')
    try:
        resp = requests.post(
            f'{base_url}/orders/{order_number}/cancel',
            headers={
                'x-api-key': api_key,
                'x-mall-id': mall_id,
            },
            timeout=10,
        )
        data = resp.json() if resp.content else {}
        if resp.status_code == 200 and data.get('status') == 'success':
            print(f'[PayAction 주문 취소 성공] order_number={order_number}')
            return True
        print(f'[PayAction 주문 취소 실패] order_number={order_number}, status={resp.status_code}, body={data}')
        return False
    except Exception as e:
        print(f'[PayAction 주문 취소 오류] order_number={order_number}: {type(e).__name__}: {e}')
        return False


def send_booking_submitted_user_email(booking):
    """대관 신청 완료 이메일 (신청자에게)"""
    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 회의실 {room_name} 대관 신청이 승인되었습니다'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #1A7F37; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
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
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>회의실 {room_name}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['booking_date']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">시간</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['start_time']} ~ {booking['end_time']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">사용 목적</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['purpose']}</td></tr>
        </table>
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_booking_admin_notification_email(booking):
    """새 대관 신청 알림 이메일 (관리자에게)"""
    admin_emails = app.config.get('ADMIN_EMAILS', [])
    if not admin_emails:
        return False

    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 새로운 회의실 대관 신청 - {booking["applicant_name"]} (회의실 {room_name})'
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
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">회의실 {room_name}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['booking_date']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">시간</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['start_time']} ~ {booking['end_time']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">인원</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('attendees', 1)}명</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">사용 목적</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['purpose']}</td></tr>
        </table>
        <div style="margin-top: 24px; padding: 16px; background: #e8f5e9; border-radius: 8px;">
          <p style="margin: 0; color: #2e7d32; font-size: 14px; font-weight: 600;">예약이 자동으로 승인 처리되었습니다. 이상이 있는 경우 관리자 페이지에서 취소해 주세요.</p>
        </div>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    
    # 모든 관리자 이메일에 발송
    result = True
    for email in admin_emails:
        if not send_email(email, subject, html):
            result = False
    
    return result


def send_booking_approved_email(booking):
    """대관 신청 승인 이메일 (신청자에게)"""
    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 회의실 {room_name} 대관 신청이 승인되었습니다'
    admin_note = booking.get('admin_note')
    note_html = f'<p style="color: #444; font-size: 14px; margin: 16px 0 0 0;"><strong>관리자 메모:</strong> {admin_note}</p>' if admin_note else ''
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #1A7F37; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
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
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>회의실 {room_name}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['booking_date']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">시간</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['start_time']} ~ {booking['end_time']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">사용 목적</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['purpose']}</td></tr>
        </table>
        {note_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_booking_rejected_email(booking):
    """대관 신청 거절 이메일 (신청자에게)"""
    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 회의실 {room_name} 대관 신청 결과 안내'
    admin_note = booking.get('admin_note')
    note_html = f'<p style="color: #444; font-size: 14px; margin: 16px 0 0 0;"><strong>거절 사유:</strong> {admin_note}</p>' if admin_note else ''
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #6c757d; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">회의실 대관 신청 결과 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">대관 신청이 거절되었습니다</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">신청하신 내용이 이번에는 승인되지 못했습니다.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">회의실 {room_name}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['booking_date']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">시간</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['start_time']} ~ {booking['end_time']}</td></tr>
        </table>
        {note_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_booking_cancelled_by_admin_email(booking, cancel_reason=None):
    """관리자 취소 알림 이메일 (신청자에게)"""
    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 회의실 {room_name} 대관이 취소되었습니다'
    reason_html = ''
    if cancel_reason:
        reason_html = f"""
        <div style="margin-top: 24px; padding: 16px 20px; background: #fff3cd; border-left: 4px solid #92400e; border-radius: 6px;">
          <p style="margin: 0 0 4px 0; font-weight: 700; color: #92400e; font-size: 14px;">취소 사유</p>
          <p style="margin: 0; color: #555; font-size: 14px; line-height: 1.6;">{cancel_reason}</p>
        </div>"""
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #961A32; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">회의실 대관 취소 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #fee2e2; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #991b1b; font-weight: 700; font-size: 15px;">✕ 대관 취소</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">대관이 관리자에 의해 취소되었습니다</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">아래 예약이 취소 처리되었습니다. 문의사항이 있으시면 연락주세요.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">신청자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>회의실 {room_name}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['booking_date']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">시간</td><td style="padding: 12px 16px; color: #1a1a1a;"><strong>{booking['start_time']} ~ {booking['end_time']}</strong></td></tr>
        </table>
        {reason_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr 또는 010-6598-6414로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_booking_user_cancelled_email(booking):
    """사용자 본인 취소 알림 이메일 (신청자에게)"""
    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 회의실 {room_name} 대관 취소 확인'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #444; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">회의실 대관 취소 확인</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #f3f4f6; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #374151; font-weight: 700; font-size: 15px;">✓ 취소 완료</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">대관 취소가 완료되었습니다</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">신청하신 예약이 정상적으로 취소되었습니다.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">신청자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>회의실 {room_name}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{booking['booking_date']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">시간</td><td style="padding: 12px 16px; color: #1a1a1a;"><strong>{booking['start_time']} ~ {booking['end_time']}</strong></td></tr>
        </table>
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">재신청은 회의실 대관 페이지에서 하실 수 있습니다. 문의: dsng3419@korea.ac.kr</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['applicant_email'], subject, html)


def send_cancellation_admin_notification_email(booking):
    """사용자 자기 취소 알림 이메일 (관리자에게)"""
    admin_emails = app.config.get('ADMIN_EMAILS', [])
    if not admin_emails:
        return False

    room_name = get_room_display_name(booking['room_number'])
    subject = f'[총학생회] 회의실 대관 취소 알림 - {booking["applicant_name"]} (회의실 {room_name})'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #374151; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">관리자 알림</h1>
        <p style="color: rgba(255,255,255,0.7); margin: 8px 0 0 0; font-size: 14px;">사용자가 예약을 취소했습니다</p>
      </div>
      <div style="background: white; padding: 40px;">
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 24px 0;">취소된 예약 내용</h2>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">신청자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">이메일</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['applicant_email']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">연락처</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('applicant_phone') or '-'}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">회의실</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">회의실 {room_name}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking['booking_date']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">시간</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking['start_time']} ~ {booking['end_time']}</td></tr>
        </table>
        <div style="margin-top: 24px; padding: 16px; background: #fee2e2; border-radius: 8px;">
          <p style="margin: 0; color: #991b1b; font-size: 14px; font-weight: 600;">해당 시간대가 다시 예약 가능 상태로 변경되었습니다.</p>
        </div>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """

    result = True
    for email in admin_emails:
        if not send_email(email, subject, html):
            result = False
    return result


# ============================================
# 문의사항(챗봇) 이메일 함수
# ============================================

def send_inquiry_admin_notification(inquiry):
    """새 문의 접수 알림 이메일 (관리자에게)"""
    admin_emails = app.config.get('ADMIN_EMAILS', [])
    admin_email = app.config.get('ADMIN_EMAIL', '')
    all_emails = list(set(admin_emails + ([admin_email] if admin_email else [])))
    if not all_emails:
        return False

    subject = f'[총학생회] 새로운 문의사항 접수 - {inquiry["name"]}'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #961A32; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">새로운 문의사항이 접수되었습니다</p>
      </div>
      <div style="background: white; padding: 40px;">
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 24px 0;">문의 내용</h2>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 100px; border-bottom: 1px solid #eee;">이름</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{inquiry['name']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">이메일</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{inquiry['email']}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">문의 내용</td><td style="padding: 12px 16px; color: #1a1a1a; white-space: pre-wrap;">{inquiry['message']}</td></tr>
        </table>
        <div style="margin-top: 24px; padding: 16px; background: #fff3cd; border-radius: 8px;">
          <p style="margin: 0; color: #856404; font-size: 14px; font-weight: 600;">관리자 페이지에서 답변을 작성하면 신청자에게 이메일로 자동 발송됩니다.</p>
        </div>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    result = True
    for email in all_emails:
        if not send_email(email, subject, html):
            result = False
    return result


def send_inquiry_reply_email(inquiry, reply_text):
    """문의 답변 이메일 (문의자에게)"""
    subject = f'[총학생회] 문의하신 내용에 대한 답변입니다'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #961A32; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">문의사항 답변 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #d4edda; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #155724; font-weight: 700; font-size: 15px;">✓ 답변 완료</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">안녕하세요, {inquiry['name']}님!</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">문의하신 내용에 대한 답변을 보내드립니다.</p>
        <div style="background: #f9f9f9; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #ddd;">
          <p style="color: #888; font-size: 12px; font-weight: 700; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.05em;">원래 문의 내용</p>
          <p style="color: #555; font-size: 14px; margin: 0; white-space: pre-wrap;">{inquiry['message']}</p>
        </div>
        <div style="background: #f0f7ff; border-radius: 8px; padding: 20px; border-left: 4px solid #961A32;">
          <p style="color: #961A32; font-size: 12px; font-weight: 700; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.05em;">총학생회 답변</p>
          <p style="color: #1a1a1a; font-size: 15px; margin: 0; white-space: pre-wrap;">{reply_text}</p>
        </div>
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">추가 문의사항이 있으시면 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(inquiry['email'], subject, html)


# ============================================
# 버스 예약 이메일 함수
# ============================================

def _bus_trip_rows(booking):
    """버스 예약 이메일 공통 정보 테이블 행 HTML 생성"""
    trip = booking.get('trip') or {}
    direction_info = get_bus_direction_info(trip.get('direction'))
    trip_date = trip.get('trip_date', '')
    location = trip.get('location')
    location_row = f"""
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">탑승 장소</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{location}</td></tr>""" if location else ''
    return f"""
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; width: 120px; border-bottom: 1px solid #eee;">노선</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{direction_info['label']}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">날짜</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;"><strong>{trip_date}</strong></td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">출발 시각</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{direction_info['time']}</td></tr>{location_row}
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">탑승자</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('passenger_name', '')}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-bottom: 1px solid #eee;">좌석 수</td><td style="padding: 12px 16px; color: #1a1a1a; border-bottom: 1px solid #eee;">{booking.get('seat_count', 1)}석</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">결제 금액</td><td style="padding: 12px 16px; color: #1a1a1a;"><strong>{booking.get('amount', 0):,}원</strong></td></tr>
    """


def send_bus_booking_admin_notification_email(booking):
    """새 버스 예약 알림 이메일 (관리자에게)"""
    admin_emails = app.config.get('ADMIN_EMAILS', [])
    if not admin_emails:
        return False
    subject = f'[총학생회] 새로운 버스 예약 - {booking.get("passenger_name", "")}'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #1a1a1a; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">관리자 알림</h1>
        <p style="color: rgba(255,255,255,0.7); margin: 8px 0 0 0; font-size: 14px;">새로운 버스 예약이 접수되었습니다</p>
      </div>
      <div style="background: white; padding: 40px;">
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          {_bus_trip_rows(booking)}
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444; border-top: 1px solid #eee;">연락처</td><td style="padding: 12px 16px; color: #1a1a1a; border-top: 1px solid #eee;">{booking.get('passenger_phone', '')}</td></tr>
          <tr><td style="padding: 12px 16px; font-weight: 700; color: #444;">입금자명</td><td style="padding: 12px 16px; color: #1a1a1a;">{booking.get('depositor_name', '')}</td></tr>
        </table>
        <div style="margin-top: 24px; padding: 16px; background: #fef3c7; border-radius: 8px;">
          <p style="margin: 0; color: #92400e; font-size: 14px; font-weight: 600;">입금 확인 전입니다. 관리자 페이지에서 예약 및 입금 현황을 확인하세요.</p>
        </div>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    result = True
    for email in admin_emails:
        if not send_email(email, subject, html):
            result = False
    return result


def send_bus_payment_confirmed_email(booking):
    """입금 확인 완료 이메일 (신청자에게)"""
    subject = '[총학생회] 버스 예약 입금이 확인되었습니다'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #1A7F37; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">입금 확인 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #d4edda; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #155724; font-weight: 700; font-size: 15px;">✓ 입금 확인 완료</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">입금이 확인되었습니다!</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">버스 운행 인원이 모두 확정되면 운행 확정 안내 메일을 다시 보내드립니다.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          {_bus_trip_rows(booking)}
        </table>
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['passenger_email'], subject, html)


BUS_ROUTE_ENDPOINTS = {
    'sejong_to_seoul': ('세종', '서울'),
    'seoul_to_sejong': ('서울', '세종'),
}


def send_bus_trip_confirmed_email(booking):
    """버스 운행 확정 이메일 (신청자에게) — 실제 승차권처럼 일시·장소가 잘 보이도록 구성"""
    trip = booking.get('trip') or {}
    direction = trip.get('direction')
    direction_info = get_bus_direction_info(direction)
    origin, destination = BUS_ROUTE_ENDPOINTS.get(direction, (direction_info['label'], ''))
    trip_date = trip.get('trip_date', '')
    location = trip.get('location') or '추후 안내 (문의 바랍니다)'
    passenger_name = booking.get('passenger_name', '')
    student_id = booking.get('student_id')
    order_number = booking.get('order_number', '')

    subject = f'[총학생회] 🚌 버스 승차권 — {trip_date} {origin} → {destination}'
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #eef1f5; padding: 28px 16px;">
      <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 16px; font-weight: 800; color: #1a1a1a;">고려대학교 세종캠퍼스 제38대 총학생회 비범</div>
        <div style="font-size: 13px; color: #888; margin-top: 4px;">버스 운행이 확정되었습니다 — 아래는 탑승자님의 승차권입니다</div>
      </div>

      <!-- 승차권 -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 6px 24px rgba(0,0,0,0.1);">
        <tr>
          <td style="background: linear-gradient(135deg, #961A32 0%, #6e1424 100%); padding: 22px 28px 26px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="color: rgba(255,255,255,0.85); font-size: 11px; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase;">BOARDING PASS · 탑승권</td>
                <td style="text-align: right; color: rgba(255,255,255,0.85); font-size: 18px;">🚌</td>
              </tr>
            </table>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top: 16px;">
              <tr>
                <td style="color: white; font-size: 26px; font-weight: 800;">{origin}</td>
                <td style="width: 56px; text-align: center; color: rgba(255,255,255,0.65); font-size: 20px;">→</td>
                <td style="color: white; font-size: 26px; font-weight: 800; text-align: right;">{destination}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding: 0 28px;">
            <div style="border-top: 2px dashed #e0e0e0;"></div>
          </td>
        </tr>
        <tr>
          <td style="padding: 22px 28px 4px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="50%" style="padding: 8px 0; vertical-align: top;">
                  <div style="font-size: 11px; color: #999; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">날짜</div>
                  <div style="font-size: 18px; color: #1a1a1a; font-weight: 800; margin-top: 3px;">{trip_date}</div>
                </td>
                <td width="50%" style="padding: 8px 0; vertical-align: top;">
                  <div style="font-size: 11px; color: #999; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">출발 시각</div>
                  <div style="font-size: 18px; color: #1a1a1a; font-weight: 800; margin-top: 3px;">{direction_info['time']}</div>
                </td>
              </tr>
              <tr>
                <td colspan="2" style="padding: 8px 0;">
                  <div style="font-size: 11px; color: #999; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">탑승 장소</div>
                  <div style="font-size: 16px; color: #1a1a1a; font-weight: 700; margin-top: 3px;">{location}</div>
                </td>
              </tr>
              <tr>
                <td width="50%" style="padding: 8px 0;">
                  <div style="font-size: 11px; color: #999; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">탑승자</div>
                  <div style="font-size: 16px; color: #1a1a1a; font-weight: 700; margin-top: 3px;">{passenger_name}{f' ({student_id})' if student_id else ''}</div>
                </td>
                <td width="50%" style="padding: 8px 0;">
                  <div style="font-size: 11px; color: #999; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">좌석</div>
                  <div style="font-size: 16px; color: #1a1a1a; font-weight: 700; margin-top: 3px;">{booking.get('seat_count', 1)}석</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding: 4px 28px 0;">
            <div style="border-top: 2px dashed #e0e0e0;"></div>
          </td>
        </tr>
        <tr>
          <td style="padding: 18px 28px 24px; text-align: center;">
            <div style="font-size: 10px; color: #999; font-weight: 800; text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 6px;">TICKET NO.</div>
            <div style="font-size: 16px; color: #1a1a1a; font-weight: 800; letter-spacing: 0.12em; font-family: 'Courier New', monospace;">{order_number}</div>
          </td>
        </tr>
      </table>

      <div style="margin-top: 18px; background: white; border-radius: 14px; padding: 18px 22px;">
        <p style="margin: 0; font-size: 13px; color: #555; line-height: 1.9;">
          ✓ 출발 시각 <strong>10분 전까지</strong> 탑승 장소에 도착해주세요.<br>
          ✓ 이 메일이 곧 승차권입니다. 캡처하거나 보관해두세요.<br>
          ✓ 문의 : dsng3419@korea.ac.kr / 010-6598-6414
        </p>
      </div>

      <div style="text-align: center; padding: 16px 0 0;">
        <p style="color: #aaa; font-size: 11px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['passenger_email'], subject, html)


def send_bus_trip_cancelled_email(booking, reason=None):
    """버스 운행 취소 이메일 (신청자에게, 관리자가 회차 전체를 취소한 경우)"""
    subject = '[총학생회] 예약하신 버스 운행이 취소되었습니다'
    reason_html = ''
    if reason:
        reason_html = f"""
        <div style="margin-top: 24px; padding: 16px 20px; background: #fff3cd; border-left: 4px solid #92400e; border-radius: 6px;">
          <p style="margin: 0 0 4px 0; font-weight: 700; color: #92400e; font-size: 14px;">취소 사유</p>
          <p style="margin: 0; color: #555; font-size: 14px; line-height: 1.6;">{reason}</p>
        </div>"""
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #961A32; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">버스 운행 취소 안내</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #fee2e2; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #991b1b; font-weight: 700; font-size: 15px;">✕ 운행 취소</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">버스 운행이 취소되었습니다</h2>
        <p style="color: #555; font-size: 15px; margin: 0 0 32px 0;">입금하신 금액은 환불 절차가 진행됩니다. 문의사항이 있으시면 연락주세요.</p>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          {_bus_trip_rows(booking)}
        </table>
        {reason_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">문의사항은 dsng3419@korea.ac.kr 또는 010-6598-6414로 연락주세요.</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['passenger_email'], subject, html)


def send_bus_booking_cancelled_email(booking, reason=None):
    """개별 버스 예약 취소 확인 이메일 (신청자에게)"""
    subject = '[총학생회] 버스 예약 취소 확인'
    reason_html = ''
    if reason:
        reason_html = f"""
        <div style="margin-top: 24px; padding: 16px 20px; background: #fff3cd; border-left: 4px solid #92400e; border-radius: 6px;">
          <p style="margin: 0 0 4px 0; font-weight: 700; color: #92400e; font-size: 14px;">취소 사유</p>
          <p style="margin: 0; color: #555; font-size: 14px; line-height: 1.6;">{reason}</p>
        </div>"""
    html = f"""
    <div style="font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; border-radius: 12px; overflow: hidden;">
      <div style="background: #444; padding: 32px 40px;">
        <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">고려대학교 세종캠퍼스 제38대 총학생회 비범</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">버스 예약 취소 확인</p>
      </div>
      <div style="background: white; padding: 40px;">
        <div style="display: inline-block; padding: 8px 20px; background: #f3f4f6; border-radius: 20px; margin-bottom: 20px;">
          <span style="color: #374151; font-weight: 700; font-size: 15px;">✓ 취소 완료</span>
        </div>
        <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 8px 0;">버스 예약이 취소되었습니다</h2>
        <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; overflow: hidden;">
          {_bus_trip_rows(booking)}
        </table>
        {reason_html}
        <p style="color: #888; font-size: 13px; margin: 24px 0 0 0;">이미 입금하신 경우 환불 절차는 별도로 안내드립니다. 문의: dsng3419@korea.ac.kr</p>
      </div>
      <div style="background: #f5f5f7; padding: 20px 40px; text-align: center;">
        <p style="color: #999; font-size: 12px; margin: 0;">© 2026 고려대학교 세종캠퍼스 제38대 총학생회 비범</p>
      </div>
    </div>
    """
    return send_email(booking['passenger_email'], subject, html)


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
    # 관리자, 정적 파일, API, 셔틀버스 CSV는 유지보수 모드에서도 접근 가능
    if (request.path.startswith('/admin') or request.path.startswith('/static')
            or request.path.startswith('/api/') or request.path.startswith('/schedules/')):
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
        '인복위_홍보국': '인권복지위원회 홍보국',
        '인복위_기획국': '인권복지위원회 기획국',
        '인복위_사무재정국': '인권복지위원회 사무재정국',
        '교복위_홍보국': '교육복지위원회 홍보국',
        '교복위_기획국': '교육복지위원회 기획국',
        '교복위_사무재정국': '교육복지위원회 사무재정국',
        # 이전 형태 호환성 (기존 데이터)
        '인권/복지부 홍보국': '인권복지위원회 홍보국',
        '인권/복지부 기획국': '인권복지위원회 기획국',
        '인권/복지부 사무재정국': '인권복지위원회 사무재정국',
        '교육/복지부 홍보국': '교육복지위원회 홍보국',
        '교육/복지부 기획국': '교육복지위원회 기획국',
        '교육/복지부 사무재정국': '교육복지위원회 사무재정국'
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

    is_restricted_sunday = selected_date.weekday() == 6
    is_restricted_tuesday = selected_date.weekday() == 1

    return render_template('meeting_room.html',
                           rooms=rooms,
                           selected_date=selected_date,
                           today=today,
                           max_date=max_date,
                           week_dates=week_dates,
                           prev_week=prev_week,
                           next_week=next_week,
                           is_restricted_sunday=is_restricted_sunday,
                           is_restricted_tuesday=is_restricted_tuesday)


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
    booking_password = request.form.get('booking_password', '').strip()

    # 기본 유효성 검사
    if not all([room_number, applicant_name, applicant_email, purpose, booking_date, start_time, end_time, booking_password]):
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
    
    # 회의실 1번: 3주 격주 월요일 19:00~24:00 불가 (2026-03-09부터)
    if room_number == 1:
        restricted_monday_start = datetime.strptime('2026-03-09', '%Y-%m-%d').date()
        if bd.weekday() == 0:  # 월요일
            weeks_since_start = (bd - restricted_monday_start).days // 7
            if weeks_since_start >= 0 and weeks_since_start % 3 == 0:
                st_hour = int(start_time.split(':')[0])
                # 19:00 이후 시작이거나, 종료가 19:00 초과인 경우
                if st_hour >= 19 or int(end_time.split(':')[0]) > 19 or (int(end_time.split(':')[0]) == 19 and int(end_time.split(':')[1]) > 0):
                    flash('회의실 1호는 해당 날짜 19:00 ~ 24:00에는 대관할 수 없습니다.', 'error')
                    return redirect(url_for('meeting_room', date=booking_date))

    # 회의실 1번: 매주 일요일 19:00~24:00 불가
    if room_number == 1:
        if bd.weekday() == 6:  # 일요일
            st_hour = int(start_time.split(':')[0])
            et_hour = int(end_time.split(':')[0])
            et_min = int(end_time.split(':')[1])
            if st_hour >= 19 or et_hour > 19 or (et_hour == 19 and et_min > 0):
                flash('316호는 매주 일요일 19:00 ~ 24:00에는 대관할 수 없습니다.', 'error')
                return redirect(url_for('meeting_room', date=booking_date))

    # 회의실 1번: 매주 화요일 21:00~24:00 불가
    if room_number == 1:
        if bd.weekday() == 1:  # 화요일
            st_hour = int(start_time.split(':')[0])
            et_hour = int(end_time.split(':')[0])
            et_min = int(end_time.split(':')[1])
            if st_hour >= 21 or et_hour > 21 or (et_hour == 21 and et_min > 0):
                flash('316호는 매주 화요일 21:00 ~ 24:00에는 대관할 수 없습니다.', 'error')
                return redirect(url_for('meeting_room', date=booking_date))

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
        'status': 'approved',
        'booking_password_hash': generate_password_hash(booking_password)
    }
    booking = db_helper.create_meeting_room_booking(data)

    if booking:
        # 이메일 발송 (백그라운드 스레드로 응답 속도 향상)
        booking_snapshot = dict(booking)
        threading.Thread(target=send_booking_submitted_user_email, args=(booking_snapshot,), daemon=True).start()
        threading.Thread(target=send_booking_admin_notification_email, args=(booking_snapshot,), daemon=True).start()
        flash('대관 신청이 완료되었습니다. 확인 이메일이 곧 발송됩니다.', 'success')
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
# 버스 예약 (세종 ↔ 서울)
# ============================================

def get_bus_trip_remaining_seats(trip):
    """회차의 남은 좌석 수 계산"""
    reserved = db_helper.get_reserved_seat_count(trip['id'])
    return max(0, (trip.get('capacity') or 0) - reserved)


def build_bus_calendar(year, month, today, available_dates_set, selected_date_str):
    """버스 예약 달력 그리드 생성 (월요일 시작). 주 단위 리스트를 반환한다."""
    cal = calendar_module.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_cells = []
        for d in week:
            d_str = d.strftime('%Y-%m-%d')
            week_cells.append({
                'day': d.day,
                'date_str': d_str,
                'in_month': d.month == month,
                'is_past': d < today,
                'is_today': d == today,
                'has_trips': d_str in available_dates_set,
                'is_selected': d_str == selected_date_str,
            })
        weeks.append(week_cells)
    return weeks


@app.route('/bus')
def bus():
    if not is_bus_booking_open() and not current_user.is_authenticated:
        return render_template('bus_not_open.html')

    today = date.today()
    today_str = today.strftime('%Y-%m-%d')

    all_trips = db_helper.get_upcoming_bus_trips(today_str)

    # 회차가 존재하는 날짜 목록 (오름차순, 중복 제거)
    available_dates = sorted({t['trip_date'] for t in all_trips})
    available_dates_set = set(available_dates)

    # 예약 가능한 날짜가 아니면 선택 안 함(=달력만 표시)
    selected_date_str = request.args.get('date', '')
    if selected_date_str not in available_dates_set:
        selected_date_str = None

    # 조회할 달 (YYYY-MM). 값이 없거나 잘못되면 오늘이 속한 달로 대체.
    month_param = request.args.get('month', '')
    try:
        cal_year, cal_month = (int(p) for p in month_param.split('-'))
        calendar_anchor = date(cal_year, cal_month, 1)
    except (ValueError, TypeError):
        # month 파라미터가 없는 첫 방문이라면, 예약 가능한 날짜 중 가장 이른 날짜가
        # 속한 달을 기본으로 보여준다 (당장 이번 달에 열린 회차가 없어도 바로 보이도록).
        if not month_param and available_dates:
            calendar_anchor = datetime.strptime(available_dates[0], '%Y-%m-%d').date().replace(day=1)
        else:
            calendar_anchor = date(today.year, today.month, 1)
        cal_year, cal_month = calendar_anchor.year, calendar_anchor.month

    calendar_weeks = build_bus_calendar(cal_year, cal_month, today, available_dates_set, selected_date_str)
    prev_month_date = (calendar_anchor - timedelta(days=1)).replace(day=1)
    next_month_date = (calendar_anchor.replace(day=28) + timedelta(days=4)).replace(day=1)
    can_go_prev_month = calendar_anchor > date(today.year, today.month, 1)

    trips_today = []
    if selected_date_str:
        trips_today = [t for t in all_trips if t['trip_date'] == selected_date_str]
        for t in trips_today:
            t['remaining_seats'] = get_bus_trip_remaining_seats(t)
            t['direction_info'] = get_bus_direction_info(t['direction'])
        # 방향 순서 고정 (세종→서울, 서울→세종)
        trips_today.sort(key=lambda t: 0 if t['direction'] == 'sejong_to_seoul' else 1)

    return render_template('bus.html',
                           today=today,
                           available_dates=available_dates,
                           selected_date_str=selected_date_str,
                           trips_today=trips_today,
                           bus_directions=BUS_DIRECTIONS,
                           calendar_weeks=calendar_weeks,
                           calendar_year=cal_year,
                           calendar_month=cal_month,
                           current_month_str=calendar_anchor.strftime('%Y-%m'),
                           prev_month_str=prev_month_date.strftime('%Y-%m'),
                           next_month_str=next_month_date.strftime('%Y-%m'),
                           can_go_prev_month=can_go_prev_month)


@app.route('/bus/book', methods=['POST'])
def bus_book():
    if not is_bus_booking_open() and not current_user.is_authenticated:
        flash('버스 예약 페이지는 아직 오픈되지 않았습니다.', 'error')
        return redirect(url_for('bus'))

    trip_id = request.form.get('trip_id', type=int)
    passenger_name = request.form.get('passenger_name', '').strip()
    passenger_phone = request.form.get('passenger_phone', '').strip()
    passenger_email = request.form.get('passenger_email', '').strip()
    student_id = request.form.get('student_id', '').strip()
    depositor_name = request.form.get('depositor_name', '').strip()
    refund_bank_name = request.form.get('refund_bank_name', '').strip()
    refund_account_number = request.form.get('refund_account_number', '').strip()
    refund_account_holder = request.form.get('refund_account_holder', '').strip()
    seat_count = 1  # 1인당 1좌석으로 고정 (여러 좌석이 필요하면 각자 따로 예약)
    booking_password = request.form.get('booking_password', '').strip()

    if not all([trip_id, passenger_name, passenger_phone, passenger_email, student_id, depositor_name, booking_password]):
        flash('필수 항목을 모두 입력해주세요. (학번 포함)', 'error')
        return redirect(url_for('bus'))

    trip = db_helper.get_bus_trip_by_id(trip_id)
    if not trip or trip['status'] == 'cancelled':
        flash('선택하신 버스 회차를 찾을 수 없습니다.', 'error')
        return redirect(url_for('bus'))

    if trip['trip_date'] < date.today().strftime('%Y-%m-%d'):
        flash('지난 날짜의 버스는 예약할 수 없습니다.', 'error')
        return redirect(url_for('bus', date=trip['trip_date'], month=trip['trip_date'][:7]))

    remaining = get_bus_trip_remaining_seats(trip)
    if seat_count > remaining:
        flash(f'남은 좌석이 {remaining}석 뿐입니다. 좌석 수를 줄여주세요.', 'error')
        return redirect(url_for('bus', date=trip['trip_date'], month=trip['trip_date'][:7]))

    amount = (trip.get('price') or 0) * seat_count
    order_number = generate_bus_order_number()

    data = {
        'trip_id': trip_id,
        'passenger_name': passenger_name,
        'passenger_phone': passenger_phone,
        'passenger_email': passenger_email,
        'student_id': student_id or None,
        'depositor_name': depositor_name,
        'refund_bank_name': refund_bank_name or None,
        'refund_account_number': refund_account_number or None,
        'refund_account_holder': refund_account_holder or None,
        'seat_count': seat_count,
        'amount': amount,
        'order_number': order_number,
        'payment_status': 'pending',
        'booking_status': 'reserved',
        'booking_password_hash': generate_password_hash(booking_password),
    }
    booking = db_helper.create_bus_booking(data)

    if not booking:
        flash('예약 처리 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
        return redirect(url_for('bus', date=trip['trip_date'], month=trip['trip_date'][:7]))

    # PayAction 주문 등록 (설정되어 있지 않으면 조용히 생략됨)
    auto_cancel_at = datetime.now() + timedelta(hours=24)
    payaction_create_order(
        order_number=order_number,
        amount=amount,
        orderer_name=passenger_name,
        orderer_phone=passenger_phone,
        orderer_email=passenger_email,
        billing_name=depositor_name,
        auto_cancel_at=auto_cancel_at,
    )

    email_booking = {**booking, 'trip': trip}
    threading.Thread(target=send_bus_booking_admin_notification_email, args=(email_booking,), daemon=True).start()

    flash('예약이 접수되었습니다. 안내드린 계좌로 입금해주세요.', 'success')
    return redirect(url_for('bus_payment', order_number=order_number))


@app.route('/bus/payment/<order_number>')
def bus_payment(order_number):
    booking = db_helper.get_bus_booking_by_order_number(order_number)
    if not booking:
        flash('예약 정보를 찾을 수 없습니다.', 'error')
        return redirect(url_for('bus'))

    return render_template('bus_payment.html',
                           booking=booking,
                           direction_info=get_bus_direction_info(booking['trip']['direction']) if booking.get('trip') else None,
                           bank_name=app.config.get('BUS_BANK_NAME'),
                           bank_account=app.config.get('BUS_BANK_ACCOUNT_NUMBER'),
                           bank_holder=app.config.get('BUS_BANK_ACCOUNT_HOLDER'))


@app.route('/bus/cancel', methods=['GET', 'POST'])
def bus_cancel():
    """사용자 버스 예약 취소 페이지"""
    bookings = None
    searched_email = None

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'lookup':
            email = request.form.get('email', '').strip().lower()
            if not email:
                flash('이메일을 입력해주세요.', 'error')
            else:
                searched_email = email
                bookings = db_helper.get_bus_bookings_by_email(email)
                if not bookings:
                    flash('해당 이메일로 등록된 예약이 없습니다.', 'info')

        elif action == 'cancel':
            booking_id = request.form.get('booking_id', type=int)
            password = request.form.get('booking_password', '').strip()
            email = request.form.get('email', '').strip().lower()

            booking = db_helper.get_bus_booking_by_id(booking_id) if booking_id else None
            if not booking:
                flash('예약을 찾을 수 없습니다. 문의해주세요.', 'error')
            elif booking.get('passenger_email', '').lower() != email:
                flash('이메일이 일치하지 않습니다. 문의해주세요.', 'error')
            elif not booking.get('booking_password_hash') or not check_password_hash(booking['booking_password_hash'], password):
                flash('비밀번호가 올바르지 않습니다. 다시 시도하거나 문의해주세요.', 'error')
            else:
                update_data = {'booking_status': 'cancelled'}
                if booking['payment_status'] == 'pending':
                    update_data['payment_status'] = 'cancelled'
                updated = db_helper.update_bus_booking(booking_id, update_data)
                if updated:
                    if booking['payment_status'] == 'paid':
                        threading.Thread(target=payaction_cancel_order, args=(booking['order_number'],), daemon=True).start()
                    b_snap = {**booking, **update_data}
                    threading.Thread(target=send_bus_booking_cancelled_email, args=(b_snap,), daemon=True).start()
                    flash('버스 예약이 취소되었습니다. 취소 확인 이메일이 곧 발송됩니다.', 'success')
                    return redirect(url_for('bus_cancel'))
                else:
                    flash('취소 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error')

    return render_template('bus_cancel.html', bookings=bookings, searched_email=searched_email,
                           bus_directions=BUS_DIRECTIONS)


def mark_bus_booking_paid(booking, source='webhook'):
    """버스 예약을 입금완료로 변경하고 안내 메일을 정확히 한 번만 발송한다.

    조건부(원자적) UPDATE를 사용해, 웹훅이 중복 수신되거나 관리자 수동확인과
    웹훅이 거의 동시에 들어와도 실제로 상태를 'pending -> paid'로 바꾼
    호출 하나만 이메일을 보내도록 보장한다. 반환값은 처리 성공 여부.
    """
    if booking['booking_status'] == 'cancelled':
        print(f'[버스 입금확인] 처리 생략 (취소된 예약) — booking_id={booking["id"]}, source={source}')
        return False

    updated = db_helper.mark_bus_booking_paid_if_pending(booking['id'])
    if not updated:
        print(f'[버스 입금확인] 처리 생략 (이미 처리됨) — booking_id={booking["id"]}, source={source}')
        return False

    email_booking = {**booking, 'payment_status': 'paid'}
    threading.Thread(target=send_bus_payment_confirmed_email, args=(email_booking,), daemon=True).start()
    print(f'[버스 입금확인] 처리 완료 — booking_id={booking["id"]}, order_number={booking.get("order_number")}, source={source}')

    # 입금 확인 시점에 이미 해당 회차의 운행이 확정되어 있었다면(=늦게 입금된 경우),
    # 별도로 관리자가 운행확정 버튼을 다시 누르지 않아도 곧바로 운행확정(승차권) 메일도 발송한다.
    trip = booking.get('trip')
    if trip and trip.get('status') == 'confirmed' and booking['booking_status'] == 'reserved':
        if db_helper.mark_bus_booking_confirmed_if_reserved(booking['id']):
            ticket_email_booking = {**booking, 'payment_status': 'paid', 'booking_status': 'confirmed'}
            threading.Thread(target=send_bus_trip_confirmed_email, args=(ticket_email_booking,), daemon=True).start()
            print(f'[버스 입금확인] 이미 운행확정된 회차라 승차권 메일도 함께 발송 — booking_id={booking["id"]}')

    return True


@app.route('/api/payaction/webhook', methods=['POST'])
def api_payaction_webhook():
    """PayAction 웹훅 수신.

    PayAction은 연동 방식에 따라 서로 다른 두 가지 payload를 같은 웹훅 URL로 보낼 수 있다.
    1) 입금 자동확인(주문 매칭) 웹훅: {"order_number", "order_status": "매칭완료", ...}
    2) 입출금 데이터수신 웹훅: {"transaction_type": "deposited", "transaction_name", "amount", ...} (주문번호 없음)
    실제로 어느 쪽이 오는지 대시보드 설정에 따라 달라질 수 있으므로 둘 다 처리한다.
    """
    raw_body = request.get_data(as_text=True)
    received_webhook_key = request.headers.get('x-webhook-key') or ''
    received_mall_id = request.headers.get('x-mall-id') or ''
    print(f'[PayAction Webhook] 수신 — headers: x-mall-id={received_mall_id!r}, '
          f'x-webhook-key(received)={received_webhook_key!r}, '
          f'x-trace-id={request.headers.get("x-trace-id")!r} / body: {raw_body}')

    webhook_key = (app.config.get('PAYACTION_WEBHOOK_KEY') or '').strip()
    mall_id = (app.config.get('PAYACTION_MALL_ID') or '').strip()

    if webhook_key:
        if received_webhook_key.strip() != webhook_key:
            print(f'[PayAction Webhook] 거부됨 — x-webhook-key가 PAYACTION_WEBHOOK_KEY 설정값과 일치하지 않습니다. '
                  f'(수신값={received_webhook_key!r}) 대시보드 > API 의 웹훅키와 .env의 PAYACTION_WEBHOOK_KEY를 다시 대조해보세요.')
            return jsonify({'status': 'error', 'message': 'invalid webhook key'}), 401
        if mall_id and received_mall_id.strip() != mall_id:
            print(f'[PayAction Webhook] 거부됨 — x-mall-id가 PAYACTION_MALL_ID 설정값과 일치하지 않습니다. '
                  f'(수신값={received_mall_id!r})')
            return jsonify({'status': 'error', 'message': 'invalid mall id'}), 401

    data = request.get_json(silent=True) or {}

    # ── 방식 1: 입금 자동확인(주문 매칭) 웹훅 ──────────────────────────
    order_number = data.get('order_number')
    if order_number:
        order_status = data.get('order_status')
        booking = db_helper.get_bus_booking_by_order_number(order_number)
        if not booking:
            print(f'[PayAction Webhook] 알 수 없는 order_number: {order_number}')
            return jsonify({'status': 'success'}), 200

        if order_status == '매칭완료':
            mark_bus_booking_paid(booking, source='payaction_order')
        else:
            print(f'[PayAction Webhook] 처리 생략 — order_number={order_number}, order_status={order_status!r}')
        return jsonify({'status': 'success'}), 200

    # ── 방식 2: 입출금 데이터수신 웹훅 (주문번호 없이 입금자명+금액으로 매칭) ──
    transaction_type = data.get('transaction_type')
    if transaction_type == 'deposited':
        transaction_name = (data.get('transaction_name') or '').strip()
        amount = data.get('amount')
        candidates = db_helper.get_pending_bus_bookings_by_deposit(transaction_name, amount)
        if len(candidates) == 1:
            mark_bus_booking_paid(candidates[0], source='payaction_deposit')
        elif len(candidates) == 0:
            print(f'[PayAction Webhook] 입출금 이벤트 — 일치하는 대기중 예약 없음: '
                  f'입금자명={transaction_name!r}, 금액={amount}')
        else:
            print(f'[PayAction Webhook] 입출금 이벤트 — 입금자명={transaction_name!r}, 금액={amount} 조건에 '
                  f'예약이 {len(candidates)}건 있어 자동 매칭을 보류합니다. 관리자가 수동으로 확인해주세요. '
                  f'booking_ids={[c["id"] for c in candidates]}')
        return jsonify({'status': 'success'}), 200

    print(f'[PayAction Webhook] 처리할 수 없는 payload 형식입니다: {data}')
    return jsonify({'status': 'success'}), 200


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
        'pending_bookings': db_helper.count_pending_bookings(),
        'pending_inquiries': db_helper.count_pending_inquiries(),
        'pending_bus_payments': db_helper.count_pending_bus_payments()
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
        '인복위_홍보국': '인권복지위원회 홍보국',
        '인복위_기획국': '인권복지위원회 기획국',
        '인복위_사무재정국': '인권복지위원회 사무재정국',
        '교복위_홍보국': '교육복지위원회 홍보국',
        '교복위_기획국': '교육복지위원회 기획국',
        '교복위_사무재정국': '교육복지위원회 사무재정국',
        # 이전 형태 호환성 (기존 데이터)
        '인권/복지부 홍보국': '인권복지위원회 홍보국',
        '인권/복지부 기획국': '인권복지위원회 기획국',
        '인권/복지부 사무재정국': '인권복지위원회 사무재정국',
        '교육/복지부 홍보국': '교육복지위원회 홍보국',
        '교육/복지부 기획국': '교육복지위원회 기획국',
        '교육/복지부 사무재정국': '교육복지위원회 사무재정국'
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
    if status_filter in ['pending', 'approved', 'rejected', 'cancelled']:
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
        room_name = get_room_display_name(booking['room_number'])
        if email_sent:
            flash(f'회의실 {room_name} 대관 신청이 승인되었습니다. 신청자에게 이메일이 발송되었습니다.', 'success')
        else:
            flash(f'회의실 {room_name} 대관 신청이 승인되었습니다. (이메일 발송 실패 — 서버 로그를 확인하세요)', 'warning')
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
        room_name = get_room_display_name(booking['room_number'])
        if email_sent:
            flash(f'회의실 {room_name} 대관 신청이 거절되었습니다. 신청자에게 이메일이 발송되었습니다.', 'success')
        else:
            flash(f'회의실 {room_name} 대관 신청이 거절되었습니다. (이메일 발송 실패 — 서버 로그를 확인하세요)', 'warning')
    else:
        flash('거절 처리 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_meeting_rooms'))


@app.route('/admin/meeting-rooms/delete/<int:booking_id>', methods=['POST'])
@login_required
def admin_meeting_room_delete(booking_id):
    print(f'[DELETE ROUTE] 진입 booking_id={booking_id} user={current_user}')
    try:
        booking = db_helper.get_meeting_room_booking_by_id(booking_id)
        print(f'[DELETE ROUTE] booking 조회 결과: {booking}')
        if not booking:
            print(f'[DELETE ROUTE] booking_id={booking_id} 찾을 수 없음')
            flash('대관 신청을 찾을 수 없습니다.', 'error')
            return redirect(url_for('admin_meeting_rooms'))
        cancel_reason = request.form.get('cancel_reason', '').strip()
        ok = db_helper.delete_meeting_room_booking(booking_id)
        print(f'[DELETE ROUTE] delete 결과: ok={ok}')
        if ok:
            threading.Thread(target=send_booking_cancelled_by_admin_email, args=(dict(booking), cancel_reason or None), daemon=True).start()
            flash(f'회의실 {get_room_display_name(booking["room_number"])} 대관 신청이 취소되었습니다. 신청자에게 취소 안내 이메일이 발송됩니다.', 'success')
        else:
            flash('삭제 처리 중 오류가 발생했습니다. 서버 로그를 확인하세요.', 'error')
    except Exception as e:
        print(f'[DELETE ROUTE] 예외 발생 booking_id={booking_id}: {e}')
        flash('삭제 처리 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_meeting_rooms'))


@app.route('/admin/meeting-rooms/book', methods=['POST'])
@login_required
def admin_meeting_room_book():
    """관리자 직접 대관 예약"""
    room_number = request.form.get('room_number', type=int)
    booking_date = request.form.get('booking_date', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    purpose = request.form.get('purpose', '').strip()

    if not all([room_number, booking_date, start_time, end_time]):
        flash('회의실, 날짜, 시간은 필수 항목입니다.', 'error')
        return redirect(url_for('admin_meeting_rooms'))

    if room_number not in [1, 2, 3, 4]:
        flash('올바른 회의실을 선택해주세요.', 'error')
        return redirect(url_for('admin_meeting_rooms'))

    if start_time >= end_time:
        flash('종료 시간은 시작 시간보다 늦어야 합니다.', 'error')
        return redirect(url_for('admin_meeting_rooms'))

    # 시간 중복 확인
    existing_bookings = db_helper.get_bookings_by_date(booking_date)
    for eb in existing_bookings:
        if eb.get('room_number') == room_number and eb.get('status') in ['pending', 'approved']:
            es = eb.get('start_time', '')
            ee = eb.get('end_time', '')
            if not (end_time <= es or start_time >= ee):
                flash(f'선택하신 시간대({start_time}~{end_time})에 이미 대관이 있습니다.', 'error')
                return redirect(url_for('admin_meeting_rooms'))

    data = {
        'room_number': room_number,
        'applicant_name': '관리자',
        'applicant_email': 'admin@kuadmin.internal',
        'applicant_phone': None,
        'organization': '__ADMIN__',
        'purpose': purpose or '관리자 예약',
        'booking_date': booking_date,
        'start_time': start_time,
        'end_time': end_time,
        'attendees': 0,
        'status': 'approved',
        'admin_note': f'관리자({current_user.username}) 직접 예약',
    }
    booking = db_helper.create_meeting_room_booking(data)
    if booking:
        room_name = get_room_display_name(room_number)
        flash(f'{room_name} {booking_date} {start_time}~{end_time} 관리자 예약이 등록되었습니다.', 'success')
    else:
        flash('예약 등록 중 오류가 발생했습니다.', 'error')

    return redirect(url_for('admin_meeting_rooms'))


@app.route('/meeting-room/cancel', methods=['GET', 'POST'])
def meeting_room_cancel():
    """사용자 예약 취소 페이지"""
    bookings = None
    searched_email = None

    if request.method == 'POST':
        action = request.form.get('action', '')

        # Step 1: 이메일로 예약 조회
        if action == 'lookup':
            email = request.form.get('email', '').strip().lower()
            if not email:
                flash('이메일을 입력해주세요.', 'error')
            else:
                searched_email = email
                bookings = db_helper.get_bookings_by_email(email)
                if not bookings:
                    flash('해당 이메일로 등록된 예약이 없습니다.', 'info')

        # Step 2: 비밀번호 인증 후 취소
        elif action == 'cancel':
            booking_id = request.form.get('booking_id', type=int)
            password = request.form.get('booking_password', '').strip()
            email = request.form.get('email', '').strip().lower()

            booking = db_helper.get_meeting_room_booking_by_id(booking_id) if booking_id else None
            if not booking:
                flash('예약을 찾을 수 없습니다. 문의해주세요.', 'error')
            elif booking.get('applicant_email', '').lower() != email:
                flash('이메일이 일치하지 않습니다. 문의해주세요.', 'error')
            elif not booking.get('booking_password_hash'):
                flash('이 예약은 비밀번호 오류가 발생했습니다. 관리자에게 문의해주세요.', 'error')
            elif not check_password_hash(booking['booking_password_hash'], password):
                flash('비밀번호가 올바르지 않습니다. 다시 시도하거나 문의해주세요.', 'error')
            else:
                ok = db_helper.delete_meeting_room_booking(booking_id)
                if ok:
                    b_snap = dict(booking)
                    threading.Thread(target=send_booking_user_cancelled_email, args=(b_snap,), daemon=True).start()
                    threading.Thread(target=send_cancellation_admin_notification_email, args=(b_snap,), daemon=True).start()
                    flash(f'회의실 {get_room_display_name(booking["room_number"])} ({booking["booking_date"]} {booking["start_time"]}~{booking["end_time"]}) 예약이 취소되었습니다. 취소 확인 이메일이 곧 발송됩니다.', 'success')
                    return redirect(url_for('meeting_room_cancel'))
                else:
                    flash('취소 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error')

    return render_template('meeting_room_cancel.html', bookings=bookings, searched_email=searched_email)


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
# 문의사항 (챗봇 위젯) API
# ============================================

@app.route('/api/inquiry', methods=['POST'])
def api_submit_inquiry():
    """문의사항 제출 API (공개)"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '잘못된 요청입니다.'}), 400

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not message:
        return jsonify({'success': False, 'message': '이름, 이메일, 문의 내용을 모두 입력해주세요.'}), 400

    if '@' not in email:
        return jsonify({'success': False, 'message': '올바른 이메일 주소를 입력해주세요.'}), 400

    inquiry_data = {
        'name': name,
        'email': email,
        'message': message,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }

    inquiry = db_helper.create_inquiry(inquiry_data)
    if not inquiry:
        return jsonify({'success': False, 'message': '문의 저장 중 오류가 발생했습니다.'}), 500

    threading.Thread(
        target=send_inquiry_admin_notification,
        args=(inquiry,),
        daemon=True
    ).start()

    return jsonify({'success': True, 'message': '문의가 접수되었습니다. 빠른 시일 내에 답변 드리겠습니다.'})


# ============================================
# 문의사항 관리 (관리자)
# ============================================

@app.route('/admin/inquiries')
@login_required
def admin_inquiries():
    """문의사항 목록 페이지"""
    status_filter = request.args.get('status', '')
    inquiries = db_helper.get_all_inquiries(status=status_filter if status_filter else None)
    pending_count = db_helper.count_pending_inquiries()
    return render_template('admin/inquiries.html', inquiries=inquiries, status_filter=status_filter, pending_count=pending_count)


@app.route('/admin/inquiries/<int:inquiry_id>/reply', methods=['POST'])
@login_required
def admin_inquiry_reply(inquiry_id):
    """문의사항 답변 처리 및 이메일 발송"""
    inquiry = db_helper.get_inquiry_by_id(inquiry_id)
    if not inquiry:
        flash('문의사항을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_inquiries'))

    reply_text = request.form.get('reply', '').strip()
    if not reply_text:
        flash('답변 내용을 입력해주세요.', 'error')
        return redirect(url_for('admin_inquiries'))

    update_data = {
        'reply': reply_text,
        'status': 'replied',
        'replied_by': current_user.name,
        'replied_at': datetime.now().isoformat()
    }
    updated = db_helper.update_inquiry(inquiry_id, update_data)
    if not updated:
        flash('답변 저장 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_inquiries'))

    email_sent = send_inquiry_reply_email(inquiry, reply_text)
    if email_sent:
        flash(f'{inquiry["name"]}님께 답변 이메일이 발송되었습니다.', 'success')
    else:
        flash(f'답변이 저장되었지만 이메일 발송에 실패했습니다. (수신자: {inquiry["email"]})', 'warning')

    return redirect(url_for('admin_inquiries'))


@app.route('/admin/inquiries/<int:inquiry_id>/delete', methods=['POST'])
@login_required
def admin_inquiry_delete(inquiry_id):
    """문의사항 삭제"""
    db_helper.delete_inquiry(inquiry_id)
    flash('문의사항이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_inquiries'))


# ============================================
# 버스 예약 관리 (관리자)
# ============================================

@app.route('/admin/bus')
@login_required
def admin_bus():
    trips = db_helper.get_all_bus_trips(order_by='trip_date', ascending=False)
    for t in trips:
        t['remaining_seats'] = get_bus_trip_remaining_seats(t)
        t['direction_info'] = get_bus_direction_info(t['direction'])

    bookings = db_helper.get_all_bus_bookings()

    return render_template('admin/bus.html',
                           trips=trips,
                           bookings=bookings,
                           bus_directions=BUS_DIRECTIONS,
                           payment_status_labels=BUS_PAYMENT_STATUS_LABELS,
                           booking_status_labels=BUS_BOOKING_STATUS_LABELS,
                           today=date.today(),
                           is_bus_booking_open=is_bus_booking_open())


@app.route('/admin/bus/toggle-open', methods=['POST'])
@login_required
def admin_bus_toggle_open():
    """버스 예약 페이지 공개/비공개 전환"""
    new_value = not is_bus_booking_open()
    db_helper.set_setting(BUS_BOOKING_OPEN_SETTING_KEY, 'true' if new_value else 'false')
    if new_value:
        flash('버스 예약 페이지가 공개되었습니다. 이제 누구나 접속할 수 있습니다.', 'success')
    else:
        flash('버스 예약 페이지가 비공개로 전환되었습니다. 관리자로 로그인한 경우에만 접속할 수 있습니다.', 'success')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/trips/create', methods=['POST'])
@login_required
def admin_bus_trip_create():
    trip_date = request.form.get('trip_date', '').strip()
    direction = request.form.get('direction', '').strip()
    price = request.form.get('price', 0, type=int)
    capacity = request.form.get('capacity', 0, type=int)
    location = request.form.get('location', '').strip()
    note = request.form.get('note', '').strip()

    if not trip_date or direction not in BUS_DIRECTIONS:
        flash('날짜와 노선을 올바르게 선택해주세요.', 'error')
        return redirect(url_for('admin_bus'))

    if price < 0 or capacity < 1:
        flash('요금은 0 이상, 정원은 1석 이상이어야 합니다.', 'error')
        return redirect(url_for('admin_bus'))

    existing = db_helper.get_bus_trip_by_date_direction(trip_date, direction)
    if existing:
        flash('해당 날짜·노선의 버스 회차가 이미 존재합니다.', 'error')
        return redirect(url_for('admin_bus'))

    data = {
        'trip_date': trip_date,
        'direction': direction,
        'departure_time': BUS_DIRECTIONS[direction]['time'],
        'price': price,
        'capacity': capacity,
        'status': 'open',
        'location': location or None,
        'note': note or None,
    }
    trip = db_helper.create_bus_trip(data)
    if trip:
        flash(f'{trip_date} {BUS_DIRECTIONS[direction]["label"]} 버스 회차가 등록되었습니다.', 'success')
    else:
        flash('버스 회차 등록 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/trips/<int:trip_id>/update', methods=['POST'])
@login_required
def admin_bus_trip_update(trip_id):
    trip = db_helper.get_bus_trip_by_id(trip_id)
    if not trip:
        flash('버스 회차를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    price = request.form.get('price', type=int)
    capacity = request.form.get('capacity', type=int)
    location = request.form.get('location', '').strip()
    note = request.form.get('note', '').strip()

    data = {}
    if price is not None and price >= 0:
        data['price'] = price
    if capacity is not None and capacity >= 1:
        data['capacity'] = capacity
    data['location'] = location or None
    data['note'] = note or None
    # 출발 시각은 노선(direction)에 종속된 값이므로, 수정 시 현재 기준 시각으로 동기화한다.
    # (과거에 다른 시각으로 생성된 회차를 새 기준 시각으로 맞추고 싶을 때도 "수정" 저장만 하면 됨)
    data['departure_time'] = BUS_DIRECTIONS[trip['direction']]['time']

    updated = db_helper.update_bus_trip(trip_id, data)
    if updated:
        flash('버스 회차 정보가 수정되었습니다.', 'success')
    else:
        flash('수정 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/trips/<int:trip_id>/confirm', methods=['POST'])
@login_required
def admin_bus_trip_confirm(trip_id):
    """버스 운행 확정 처리 — 입금 완료된 예약을 확정하고 신청자에게 안내 메일 발송"""
    trip = db_helper.get_bus_trip_by_id(trip_id)
    if not trip:
        flash('버스 회차를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    db_helper.update_bus_trip(trip_id, {'status': 'confirmed'})

    bookings = db_helper.get_bus_bookings_by_trip(trip_id)
    confirmed_count = 0
    for b in bookings:
        if b['booking_status'] == 'reserved' and b['payment_status'] == 'paid':
            # 조건부 UPDATE — 중복 클릭/중복 제출이 있어도 실제로 상태를 바꾼
            # 요청만 메일을 보내도록 해 안내 메일이 두 번 나가지 않게 한다.
            if not db_helper.mark_bus_booking_confirmed_if_reserved(b['id']):
                continue
            email_booking = {**b, 'booking_status': 'confirmed', 'trip': trip}
            threading.Thread(target=send_bus_trip_confirmed_email, args=(email_booking,), daemon=True).start()
            confirmed_count += 1

    direction_label = get_bus_direction_info(trip['direction'])['label']
    flash(f'{trip["trip_date"]} {direction_label} 버스 운행이 확정되었습니다. 입금 완료된 {confirmed_count}건에 안내 메일이 발송됩니다.', 'success')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/trips/<int:trip_id>/cancel', methods=['POST'])
@login_required
def admin_bus_trip_cancel(trip_id):
    """버스 회차 전체 취소 — 모든 예약을 취소 처리하고 신청자에게 안내 메일 발송"""
    trip = db_helper.get_bus_trip_by_id(trip_id)
    if not trip:
        flash('버스 회차를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    reason = request.form.get('cancel_reason', '').strip()
    db_helper.update_bus_trip(trip_id, {'status': 'cancelled'})

    bookings = db_helper.get_bus_bookings_by_trip(trip_id)
    cancelled_count = 0
    for b in bookings:
        if b['booking_status'] == 'cancelled':
            continue
        update_data = {'booking_status': 'cancelled'}
        db_helper.update_bus_booking(b['id'], update_data)
        if b['payment_status'] == 'paid':
            threading.Thread(target=payaction_cancel_order, args=(b['order_number'],), daemon=True).start()
        email_booking = {**b, **update_data, 'trip': trip}
        threading.Thread(target=send_bus_trip_cancelled_email, args=(email_booking, reason or None), daemon=True).start()
        cancelled_count += 1

    direction_label = get_bus_direction_info(trip['direction'])['label']
    flash(f'{trip["trip_date"]} {direction_label} 버스 운행이 취소되었습니다. {cancelled_count}건의 예약자에게 안내 메일이 발송됩니다.', 'success')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/trips/<int:trip_id>/delete', methods=['POST'])
@login_required
def admin_bus_trip_delete(trip_id):
    """버스 회차 완전 삭제 — 연결된 예약도 함께 삭제되며, 메일은 발송되지 않는다."""
    trip = db_helper.get_bus_trip_by_id(trip_id)
    if not trip:
        flash('버스 회차를 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    direction_label = get_bus_direction_info(trip['direction'])['label']
    ok = db_helper.delete_bus_trip(trip_id)
    if ok:
        flash(f'{trip["trip_date"]} {direction_label} 회차와 관련 예약이 모두 삭제되었습니다. (메일은 발송되지 않았습니다)', 'success')
    else:
        flash('삭제 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/bookings/<int:booking_id>/mark-paid', methods=['POST'])
@login_required
def admin_bus_booking_mark_paid(booking_id):
    """입금 수동 확인 처리 (PayAction 미연동 시 또는 확인 누락 시 사용)"""
    booking = db_helper.get_bus_booking_by_id(booking_id)
    if not booking:
        flash('예약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    if booking['payment_status'] == 'paid':
        flash('이미 입금 확인된 예약입니다.', 'info')
        return redirect(url_for('admin_bus'))

    if mark_bus_booking_paid(booking, source='admin_manual'):
        flash(f'{booking["passenger_name"]}님의 입금이 확인 처리되었습니다. 안내 메일이 발송됩니다.', 'success')
    else:
        flash('이미 다른 경로(웹훅 등)로 처리되었거나 취소된 예약입니다.', 'info')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def admin_bus_booking_cancel(booking_id):
    """개별 버스 예약 취소 (관리자)"""
    booking = db_helper.get_bus_booking_by_id(booking_id)
    if not booking:
        flash('예약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    reason = request.form.get('cancel_reason', '').strip()
    update_data = {'booking_status': 'cancelled'}
    if booking['payment_status'] == 'pending':
        update_data['payment_status'] = 'cancelled'

    updated = db_helper.update_bus_booking(booking_id, update_data)
    if updated:
        if booking['payment_status'] == 'paid':
            threading.Thread(target=payaction_cancel_order, args=(booking['order_number'],), daemon=True).start()
        email_booking = {**booking, **update_data}
        threading.Thread(target=send_bus_booking_cancelled_email, args=(email_booking, reason or None), daemon=True).start()
        flash(f'{booking["passenger_name"]}님의 버스 예약이 취소되었습니다. 안내 메일이 발송됩니다.', 'success')
    else:
        flash('취소 처리 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_bus'))


@app.route('/admin/bus/bookings/<int:booking_id>/delete', methods=['POST'])
@login_required
def admin_bus_booking_delete(booking_id):
    """개별 버스 예약 완전 삭제 (메일 발송 없음)"""
    booking = db_helper.get_bus_booking_by_id(booking_id)
    if not booking:
        flash('예약을 찾을 수 없습니다.', 'error')
        return redirect(url_for('admin_bus'))

    ok = db_helper.delete_bus_booking(booking_id)
    if ok:
        flash(f'{booking["passenger_name"]}님의 예약이 삭제되었습니다. (메일은 발송되지 않았습니다)', 'success')
    else:
        flash('삭제 중 오류가 발생했습니다.', 'error')
    return redirect(url_for('admin_bus'))


# ============================================
# 파일 업로드 & 다운로드 링크 생성 (관리자 전용)
# ============================================

@app.route('/admin/file-links', methods=['GET', 'POST'])
@login_required
def admin_file_links():
    """파일을 업로드하고 바로 다운로드 가능한 링크를 생성하는 관리자 기능"""
    upload_result = None

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('파일을 선택해주세요.', 'error')
        elif not allowed_file(file.filename):
            flash(f'허용되지 않는 파일 형식입니다. 허용 형식: {", ".join(sorted(Config.ALLOWED_EXTENSIONS))}', 'error')
        else:
            file_url = save_file(file, subfolder='files')
            if file_url:
                upload_result = {
                    'filename': secure_filename(file.filename),
                    'url': file_url,
                }
            else:
                flash('파일 업로드 중 오류가 발생했습니다.', 'error')

    return render_template('admin/file_links.html', upload_result=upload_result)


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
# 셔틀버스 & 식단표 API
# ============================================

@app.route('/schedules/<path:filename>')
def serve_schedule(filename):
    """셔틀버스 시간표 CSV 서빙"""
    return send_from_directory('schedules', filename)

@app.route('/api/menu')
def api_menu():
    """식단표 JSON API"""
    global _menu_data
    if _menu_data is None:
        _load_menu_from_file()
    # 만료됐으면 파일을 먼저 재로드 (다른 프로세스/워커가 이미 갱신했을 수 있음)
    if _is_menu_stale():
        _load_menu_from_file()
    if _menu_data is None or not _menu_data.get('success'):
        if not _is_crawling:
            threading.Thread(target=_perform_crawling, daemon=True).start()
        return jsonify({'success': False, 'message': '식단표를 불러오는 중입니다. 잠시 후 다시 시도해주세요.'})
    # 파일 재로드 후에도 여전히 만료됐으면 백그라운드 재크롤링
    if _is_menu_stale() and not _is_crawling:
        threading.Thread(target=_perform_crawling, daemon=True).start()
    return jsonify(_menu_data)

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
