"""
관리자 계정 생성 및 비밀번호 해시 생성 도구

사용법:
1. 새 비밀번호 해시 생성:
   python create_admin.py generate <비밀번호>

2. Supabase에 관리자 계정 추가:
   - Supabase 대시보드 → Table Editor → admins 테이블
   - 아래 SQL 쿼리 실행:

   INSERT INTO admins (username, password_hash, name, is_super_admin, created_at)
   VALUES ('username', '<생성된_해시>', '이름', false, NOW());
"""

import sys
from werkzeug.security import generate_password_hash, check_password_hash


def generate_hash(password: str):
    """비밀번호 해시 생성"""
    password_hash = generate_password_hash(password)
    print("\n" + "="*80)
    print("비밀번호 해시 생성 완료!")
    print("="*80)
    print(f"\n원본 비밀번호: {password}")
    print(f"\n생성된 해시:\n{password_hash}")
    print("\n" + "="*80)
    print("Supabase에 추가하는 SQL 쿼리 예시:")
    print("="*80)
    print(f"""
INSERT INTO admins (username, password_hash, name, is_super_admin, created_at)
VALUES (
    'your_username',  -- 원하는 사용자명으로 변경
    '{password_hash}',
    '관리자',  -- 원하는 이름으로 변경
    false,
    NOW()
);
""")
    return password_hash


def verify_hash(password: str, password_hash: str):
    """비밀번호 검증"""
    is_valid = check_password_hash(password_hash, password)
    print("\n" + "="*80)
    if is_valid:
        print("✓ 비밀번호 검증 성공! 해시가 올바릅니다.")
    else:
        print("✗ 비밀번호 검증 실패! 해시가 일치하지 않습니다.")
    print("="*80 + "\n")
    return is_valid


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n사용 예시:")
        print("  python create_admin.py generate mypassword123")
        print("  python create_admin.py verify mypassword123 'scrypt:...'")
        return

    command = sys.argv[1]

    if command == "generate":
        if len(sys.argv) < 3:
            print("오류: 비밀번호를 입력하세요.")
            print("사용법: python create_admin.py generate <비밀번호>")
            return
        password = sys.argv[2]
        generate_hash(password)

    elif command == "verify":
        if len(sys.argv) < 4:
            print("오류: 비밀번호와 해시를 모두 입력하세요.")
            print("사용법: python create_admin.py verify <비밀번호> '<해시>'")
            return
        password = sys.argv[2]
        password_hash = sys.argv[3]
        verify_hash(password, password_hash)

    else:
        print(f"오류: 알 수 없는 명령어 '{command}'")
        print("사용 가능한 명령어: generate, verify")


if __name__ == '__main__':
    main()
