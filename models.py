from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    """관리자 모델"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Schedule(db.Model):
    """일정 모델"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    category = db.Column(db.String(50))  # 회의, 행사, 프로젝트 등
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Promise(db.Model):
    """공약 모델"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # 카테고리 (학술, 복지 등)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    detailed_description = db.Column(db.Text)  # 상세 설명
    progress_rate = db.Column(db.Integer, default=0)  # 이행률 (0-100)
    status = db.Column(db.String(50), default='진행중')  # 진행중, 완료, 보류
    order = db.Column(db.Integer, default=0)  # 정렬 순서
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 공약 진행 상황 (1:N 관계)
    progress_updates = db.relationship('PromiseProgress', backref='promise', lazy=True, cascade='all, delete-orphan')


class PromiseProgress(db.Model):
    """공약 진행 상황 모델"""
    id = db.Column(db.Integer, primary_key=True)
    promise_id = db.Column(db.Integer, db.ForeignKey('promise.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MeetingMinutes(db.Model):
    """회의록 모델"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_type = db.Column(db.String(100))  # 정기회의, 임시회의 등
    meeting_date = db.Column(db.DateTime, nullable=False)
    attendees = db.Column(db.Text)  # 참석자
    agenda = db.Column(db.Text)  # 안건
    content = db.Column(db.Text, nullable=False)  # 회의 내용
    decisions = db.Column(db.Text)  # 결정사항
    file_url = db.Column(db.String(500))  # 첨부파일 URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Regulation(db.Model):
    """회칙 모델"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # 단위 (총학생회, 동아리연합회 등)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  # 회칙 설명
    pdf_filename = db.Column(db.String(500))  # PDF 파일명 (static/regulations/ 내)
    file_url = db.Column(db.String(500))  # 첨부파일 URL (하위 호환성)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Program(db.Model):
    """교내 프로그램 모델"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # 학술, 문화, 취업 등
    description = db.Column(db.Text, nullable=False)
    organizer = db.Column(db.String(200))  # 주최기관
    target = db.Column(db.String(200))  # 대상
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    application_start = db.Column(db.DateTime)  # 신청 시작일
    application_end = db.Column(db.DateTime)  # 신청 마감일
    location = db.Column(db.String(200))
    link = db.Column(db.String(500))  # 관련 링크
    image_url = db.Column(db.String(500))  # 이미지 URL
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Organization(db.Model):
    """조직도 모델"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)  # 회장, 부회장, 국장 등
    department = db.Column(db.String(100))  # 소속 부서
    major = db.Column(db.String(100))  # 전공
    student_id = db.Column(db.String(20))  # 학번
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    photo_url = db.Column(db.String(500))  # 프로필 사진 URL
    order = db.Column(db.Integer, default=0)  # 정렬 순서
    parent_id = db.Column(db.Integer, db.ForeignKey('organization.id'))  # 상위 조직
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 하위 조직 관계
    children = db.relationship('Organization', backref=db.backref('parent', remote_side=[id]))


class Banner(db.Model):
    """메인 페이지 배너 모델"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)  # 배너 이미지 URL
    link = db.Column(db.String(500))  # 배너 클릭 시 이동할 링크
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    is_event_banner = db.Column(db.Boolean, default=False)  # True: 이벤트 배너, False: 기본 배너
    order = db.Column(db.Integer, default=0)  # 정렬 순서
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Archive(db.Model):
    """아카이브 모델 - 학생회 활동 사진 모음"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # 행사명/활동명
    description = db.Column(db.Text)  # 행사 설명
    event_date = db.Column(db.DateTime, nullable=False)  # 행사 날짜
    category = db.Column(db.String(100))  # 카테고리 (축제, 행사, 프로그램 등)
    location = db.Column(db.String(200))  # 장소
    thumbnail_url = db.Column(db.String(500))  # 대표 이미지 (썸네일)
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    order = db.Column(db.Integer, default=0)  # 정렬 순서
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 아카이브 이미지들 (1:N 관계)
    images = db.relationship('ArchiveImage', backref='archive', lazy=True, cascade='all, delete-orphan', order_by='ArchiveImage.order')


class ArchiveImage(db.Model):
    """아카이브 이미지 모델"""
    id = db.Column(db.Integer, primary_key=True)
    archive_id = db.Column(db.Integer, db.ForeignKey('archive.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)  # 이미지 URL
    caption = db.Column(db.String(500))  # 이미지 설명
    order = db.Column(db.Integer, default=0)  # 정렬 순서
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
