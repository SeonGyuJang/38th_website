from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3, os, re, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

the_signal_bp = Blueprint('the_signal', __name__, url_prefix='/the_signal')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'the_signal.db')

THE_SIGNAL_ADMIN_PASSWORD = os.environ.get('THE_SIGNAL_ADMIN_PASSWORD', '13272441')

DEFAULT_TOPICS = [
    (11, 13, '11:00 ~ 13:00', '"첫사랑이었던 그 사람에게"',
     '첫사랑에게 하고 싶었던 말을 남겨보세요...', '💌'),
    (13, 15, '13:00 ~ 15:00', '"X(전남친/전여친)에게 연락이 온다면?"',
     'X에게 하고 싶은 말을 남겨보세요...', '📱'),
    (15, 17, '15:00 ~ 17:00', '"딱 한 번의 호출 기회, 지금 생각나는 사람"',
     '지금 생각나는 그 사람에게 한마디...', '📟'),
]

DEFAULT_CODES = [
    ('1004',    '천사',         'Angel ♡',              '사랑/감정'),
    ('486',     '사랑해',       'I Love You',            '사랑/감정'),
    ('143',     '사랑해 (EN)',  'I Love You (ENG)',       '사랑/감정'),
    ('1212',    '보고싶어',     'I Miss You',            '사랑/감정'),
    ('1010235', '열렬히 사모해','I Adore You',            '사랑/감정'),
    ('0',       '사랑',         'Love',                  '사랑/감정'),
    ('31',      '사귀자',       "Let's Date",            '사랑/감정'),
    ('♡',       '하트',         'Heart',                 '사랑/감정'),
    ('8282',    '빨리빨리',     'Hurry Up!',             '안부/일상'),
    ('0404',    '잘 있어?',     'Are You OK?',           '안부/일상'),
    ('1001',    '이리와',       'Come Here',             '안부/일상'),
    ('17171',   '같이가자',     "Let's Go Together",     '안부/일상'),
    ('24',      '이사했어',     'I Moved',               '안부/일상'),
    ('114',     '전화해줘',     'Call Me',               '안부/일상'),
    ('010',     '연락해',       'Contact Me',            '안부/일상'),
    ('177',     '있잖아',       'Hey Listen',            '안부/일상'),
    ('7942',    '친구사이',     'Just Friends',          '우정/재미'),
    ('7',       '친구',         'Friend',                '우정/재미'),
    ('333',     '감사해',       'Thank You',             '우정/재미'),
    ('100',     '최고야',       "You're the Best",       '우정/재미'),
    ('10100',   '열심히 살자',  'Live Diligently',       '우정/재미'),
    ('555',     '하하하',       'Hahaha',                '우정/재미'),
    ('9999',    '급해!',        'URGENT!',               '우정/재미'),
    ('119',     '도와줘!',      'Help Me!',              '우정/재미'),
    ('112',     '긴급연락!',    'Emergency!',            '우정/재미'),
    ('404',     '없어...',      'Not Found',             '우정/재미'),
    ('1004000', '천사 만명',    'A Million Angels',      '우정/재미'),
]

PROFANITY = [
    '씨발', '씨팔', '씨빨', '씨바', '시발', '시팔', '시빨', '시바',
    'ㅆㅣㅂㅏㄹ', 'ㅅㅣㅂㅏㄹ', 'ㅅㅣㅂ', 'ㅆㅣㅂ',
    '개새끼', '개새', '새끼', '개년', '개놈', '개같',
    '병신', '병쉰', '미친놈', '미친년', '미친새',
    '창녀', '창년', '보지', '자지', '씹', '씹새', '씹년', '씹놈',
    '지랄', '존나', '존내', '졸라', '존같',
    '닥쳐', '꺼져', '뒤져', '뒤지',
    '느금마', '니애미', '니엄마', '니에미', '네애미', '네엄마',
    '쌍년', '쌍놈', '썅년', '썅놈',
    '섹스', '야동',
    'fuck', 'fck', 'fuk',
    'shit', 'sht',
    'bitch', 'btch',
    'asshole', 'cunt', 'dick', 'cock', 'pussy',
    'bastard', 'nigger', 'nigga',
    'motherfucker',
    'whore', 'slut',
]


def _strip(text):
    return re.sub(r'[^가-힣㄰-㆏ᄀ-ᇿa-zA-Z]', '', text)


def has_profanity(text):
    cleaned = _strip(text).lower()
    return any(_strip(w).lower() in cleaned for w in PROFANITY)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_the_signal_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ts_entries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            message    TEXT    NOT NULL,
            parent_id  INTEGER DEFAULT NULL,
            likes      INTEGER DEFAULT 0,
            ip         TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ts_entry_likes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id   INTEGER NOT NULL,
            ip         TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entry_id, ip)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ts_topics (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            time_start INTEGER NOT NULL,
            time_end   INTEGER NOT NULL,
            label      TEXT    NOT NULL,
            topic_text TEXT    NOT NULL,
            hint       TEXT    DEFAULT '',
            emoji      TEXT    DEFAULT ''
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ts_pager_codes (
            code     TEXT PRIMARY KEY,
            korean   TEXT NOT NULL,
            english  TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '기타'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ts_beep_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            to_email    TEXT    NOT NULL,
            code        TEXT    NOT NULL,
            sender_name TEXT    NOT NULL,
            comment     TEXT    DEFAULT '',
            success     INTEGER DEFAULT 0,
            error_msg   TEXT    DEFAULT '',
            ip          TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    for col, dflt in [('parent_id', 'NULL'), ('likes', '0')]:
        try:
            conn.execute(f'ALTER TABLE ts_entries ADD COLUMN {col} INTEGER DEFAULT {dflt}')
        except Exception:
            pass

    if conn.execute('SELECT COUNT(*) FROM ts_topics').fetchone()[0] == 0:
        conn.executemany(
            'INSERT INTO ts_topics (time_start, time_end, label, topic_text, hint, emoji) VALUES (?,?,?,?,?,?)',
            DEFAULT_TOPICS
        )

    if conn.execute('SELECT COUNT(*) FROM ts_pager_codes').fetchone()[0] == 0:
        conn.executemany(
            'INSERT INTO ts_pager_codes (code, korean, english, category) VALUES (?,?,?,?)',
            DEFAULT_CODES
        )

    conn.commit()
    conn.close()


def ts_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('the_signal_admin'):
            return redirect(url_for('the_signal.admin_login'))
        return f(*args, **kwargs)
    return decorated


def _send_email(to_email, subject, html_content):
    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    use_ssl = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    sender = os.environ.get('MAIL_DEFAULT_SENDER', username)

    if not username:
        raise Exception('이메일 서비스가 설정되지 않았습니다')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    if use_ssl:
        server = smtplib.SMTP_SSL(mail_server, mail_port)
    else:
        server = smtplib.SMTP(mail_server, mail_port)
        if use_tls:
            server.starttls()

    server.login(username, password)
    server.send_message(msg)
    server.quit()


# ── Public routes ──────────────────────────────────────────────────────────

@the_signal_bp.route('/')
def index():
    return render_template('the_signal/index.html')


@the_signal_bp.route('/api/topics', methods=['GET'])
def get_topics():
    conn = get_db()
    rows = conn.execute(
        'SELECT id, time_start, time_end, label, topic_text, hint, emoji FROM ts_topics ORDER BY time_start'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@the_signal_bp.route('/api/pager-codes', methods=['GET'])
def get_pager_codes():
    conn = get_db()
    rows = conn.execute(
        'SELECT code, korean, english, category FROM ts_pager_codes ORDER BY rowid'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@the_signal_bp.route('/api/comments', methods=['GET'])
def get_comments():
    ip = request.remote_addr
    conn = get_db()
    rows = conn.execute(
        'SELECT id, name, message, parent_id, likes, created_at FROM ts_entries ORDER BY id ASC'
    ).fetchall()
    liked_ids = {r['entry_id'] for r in conn.execute(
        'SELECT entry_id FROM ts_entry_likes WHERE ip = ?', (ip,)
    ).fetchall()}
    conn.close()
    return jsonify([{
        'id':        r['id'],
        'name':      r['name'],
        'message':   r['message'],
        'parent_id': r['parent_id'],
        'likes':     r['likes'],
        'liked':     r['id'] in liked_ids,
        'time':      r['created_at'],
    } for r in rows])


@the_signal_bp.route('/api/comments', methods=['POST'])
def post_comment():
    data = request.get_json()
    if not data:
        return jsonify({'error': '데이터를 확인해주세요'}), 400

    name      = data.get('name', '').strip()
    message   = data.get('message', '').strip()
    parent_id = data.get('parent_id')
    ip        = request.remote_addr

    if not name or not message:
        return jsonify({'error': '이름과 메시지를 입력해주세요'}), 400
    if len(name) > 20:
        return jsonify({'error': '이름은 20자 이내로 입력해주세요'}), 400
    if len(message) > 300:
        return jsonify({'error': '메시지는 300자 이내로 입력해주세요'}), 400
    if has_profanity(name) or has_profanity(message):
        return jsonify({'error': '부적절한 표현이 포함되어 있어요'}), 400

    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM ts_entries WHERE ip = ? AND created_at > datetime('now', '-1 hour')",
        (ip,)
    ).fetchone()[0]
    if count >= 15:
        conn.close()
        return jsonify({'error': '잠시 후 다시 시도해주세요'}), 429

    if parent_id:
        parent = conn.execute(
            'SELECT id FROM ts_entries WHERE id = ? AND parent_id IS NULL', (parent_id,)
        ).fetchone()
        if not parent:
            conn.close()
            return jsonify({'error': '잘못된 요청입니다'}), 400

    conn.execute(
        'INSERT INTO ts_entries (name, message, parent_id, ip) VALUES (?, ?, ?, ?)',
        (name, message, parent_id or None, ip)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/api/comments/<int:comment_id>/like', methods=['POST'])
def toggle_like(comment_id):
    ip = request.remote_addr
    conn = get_db()
    comment = conn.execute('SELECT id FROM ts_entries WHERE id = ?', (comment_id,)).fetchone()
    if not comment:
        conn.close()
        return jsonify({'error': '댓글을 찾을 수 없습니다'}), 404

    existing = conn.execute(
        'SELECT id FROM ts_entry_likes WHERE entry_id = ? AND ip = ?', (comment_id, ip)
    ).fetchone()

    if existing:
        conn.execute('DELETE FROM ts_entry_likes WHERE entry_id = ? AND ip = ?', (comment_id, ip))
        conn.execute('UPDATE ts_entries SET likes = MAX(0, likes - 1) WHERE id = ?', (comment_id,))
        liked = False
    else:
        conn.execute('INSERT OR IGNORE INTO ts_entry_likes (entry_id, ip) VALUES (?, ?)', (comment_id, ip))
        conn.execute('UPDATE ts_entries SET likes = likes + 1 WHERE id = ?', (comment_id,))
        liked = True

    conn.commit()
    new_likes = conn.execute('SELECT likes FROM ts_entries WHERE id = ?', (comment_id,)).fetchone()['likes']
    conn.close()
    return jsonify({'liked': liked, 'likes': new_likes})


@the_signal_bp.route('/api/send-beep', methods=['POST'])
def send_beep():
    data = request.get_json()
    if not data:
        return jsonify({'error': '데이터를 확인해주세요'}), 400

    email       = data.get('email', '').strip()
    code        = data.get('code', '').strip()
    sender_name = (data.get('sender_name', '') or 'THE SIGNAL').strip()
    comment     = data.get('comment', '').strip()[:80]

    if not email or not code:
        return jsonify({'error': '이메일과 삐삐 코드를 입력해주세요'}), 400
    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'error': '올바른 이메일 주소를 입력해주세요'}), 400
    if comment and has_profanity(comment):
        return jsonify({'error': '부적절한 표현이 포함되어 있어요'}), 400
    if not os.environ.get('MAIL_USERNAME'):
        return jsonify({'error': '이메일 서비스가 설정되지 않았습니다'}), 503

    conn = get_db()
    row = conn.execute('SELECT korean, english FROM ts_pager_codes WHERE code = ?', (code,)).fetchone()
    conn.close()
    code_info = (row['korean'], row['english']) if row else ('비밀 코드', 'Secret Code')

    ip = request.remote_addr
    try:
        html_body = render_template(
            'the_signal/email_template.html',
            code=code,
            korean_meaning=code_info[0],
            english_meaning=code_info[1],
            sender_name=sender_name,
            comment=comment,
        )
        _send_email(
            to_email=email,
            subject=f'📟 [{code}] THE SIGNAL에서 삐삐가 왔어요!',
            html_content=html_body,
        )
        conn = get_db()
        conn.execute(
            'INSERT INTO ts_beep_log (to_email, code, sender_name, comment, success, ip) VALUES (?,?,?,?,1,?)',
            (email, code, sender_name, comment, ip)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        err_str = str(e)[:300]
        try:
            conn = get_db()
            conn.execute(
                'INSERT INTO ts_beep_log (to_email, code, sender_name, comment, success, error_msg, ip) VALUES (?,?,?,?,0,?,?)',
                (email, code, sender_name, comment, err_str, ip)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        return jsonify({'error': '메일 발송에 실패했습니다. 설정을 확인해주세요.'}), 500


# ── Admin routes ───────────────────────────────────────────────────────────

@the_signal_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == THE_SIGNAL_ADMIN_PASSWORD:
            session['the_signal_admin'] = True
            return redirect(url_for('the_signal.admin'))
        error = '비밀번호가 틀렸습니다'
    return render_template('the_signal/admin_login.html', error=error)


@the_signal_bp.route('/admin/logout')
def admin_logout():
    session.pop('the_signal_admin', None)
    return redirect(url_for('the_signal.admin_login'))


@the_signal_bp.route('/admin')
@ts_admin_required
def admin():
    return render_template('the_signal/admin.html')


@the_signal_bp.route('/admin/api/comments', methods=['GET'])
@ts_admin_required
def admin_get_comments():
    conn = get_db()
    rows = conn.execute(
        'SELECT id, name, message, parent_id, likes, created_at FROM ts_entries ORDER BY id DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@the_signal_bp.route('/admin/api/comments/<int:cid>', methods=['PUT'])
@ts_admin_required
def admin_update_comment(cid):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no data'}), 400
    conn = get_db()
    conn.execute('UPDATE ts_entries SET name=?, message=? WHERE id=?',
                 (data.get('name', ''), data.get('message', ''), cid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/admin/api/comments/<int:cid>', methods=['DELETE'])
@ts_admin_required
def admin_delete_comment(cid):
    conn = get_db()
    conn.execute('DELETE FROM ts_entries WHERE id=? OR parent_id=?', (cid, cid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/admin/api/topics', methods=['GET'])
@ts_admin_required
def admin_get_topics():
    conn = get_db()
    rows = conn.execute(
        'SELECT id, time_start, time_end, label, topic_text, hint, emoji FROM ts_topics ORDER BY time_start'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@the_signal_bp.route('/admin/api/topics/<int:tid>', methods=['PUT'])
@ts_admin_required
def admin_update_topic(tid):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no data'}), 400
    conn = get_db()
    conn.execute(
        'UPDATE ts_topics SET time_start=?, time_end=?, label=?, topic_text=?, hint=?, emoji=? WHERE id=?',
        (data['time_start'], data['time_end'], data['label'],
         data['topic_text'], data.get('hint', ''), data.get('emoji', ''), tid)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/admin/api/codes', methods=['GET'])
@ts_admin_required
def admin_get_codes():
    conn = get_db()
    rows = conn.execute(
        'SELECT code, korean, english, category FROM ts_pager_codes ORDER BY rowid'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@the_signal_bp.route('/admin/api/codes', methods=['POST'])
@ts_admin_required
def admin_add_code():
    data = request.get_json()
    if not data or not data.get('code') or not data.get('korean'):
        return jsonify({'error': '코드와 한국어 의미를 입력해주세요'}), 400
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO ts_pager_codes (code, korean, english, category) VALUES (?,?,?,?)',
            (data['code'], data['korean'], data.get('english', ''), data.get('category', '기타'))
        )
        conn.commit()
    except Exception:
        conn.close()
        return jsonify({'error': '이미 존재하는 코드입니다'}), 409
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/admin/api/codes/<path:code>', methods=['PUT'])
@ts_admin_required
def admin_update_code(code):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no data'}), 400
    conn = get_db()
    conn.execute(
        'UPDATE ts_pager_codes SET korean=?, english=?, category=? WHERE code=?',
        (data.get('korean', ''), data.get('english', ''), data.get('category', '기타'), code)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/admin/api/codes/<path:code>', methods=['DELETE'])
@ts_admin_required
def admin_delete_code(code):
    conn = get_db()
    conn.execute('DELETE FROM ts_pager_codes WHERE code=?', (code,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@the_signal_bp.route('/admin/api/beep-log', methods=['GET'])
@ts_admin_required
def admin_get_beep_log():
    conn = get_db()
    rows = conn.execute(
        'SELECT id, to_email, code, sender_name, comment, success, error_msg, ip, created_at '
        'FROM ts_beep_log ORDER BY id DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
