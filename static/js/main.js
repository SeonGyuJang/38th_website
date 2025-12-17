// ============================================
// 고려대학교 38대 총학생회 웹사이트
// JavaScript 인터랙션
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // 모바일 메뉴 토글
    initMobileMenu();

    // 현재 페이지 네비게이션 하이라이트
    highlightCurrentPage();

    // 스무스 스크롤
    initSmoothScroll();

    // 프로그레스 바 애니메이션
    animateProgressBars();

    // 카드 애니메이션
    initCardAnimations();

    // 폼 유효성 검사
    initFormValidation();

    // Alert 메시지 자동 닫기
    initAlertAutoClose();
});

// ============ 모바일 메뉴 토글 ============
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');

            // 햄버거 아이콘 애니메이션
            const spans = menuToggle.querySelectorAll('span');
            if (mobileMenu.classList.contains('active')) {
                spans[0].style.transform = 'rotate(-45deg) translate(-5px, 6px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(45deg) translate(-5px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });

        // 메뉴 외부 클릭 시 닫기
        document.addEventListener('click', function(event) {
            if (!menuToggle.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.remove('active');
                const spans = menuToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });

        // 모바일 메뉴 링크 클릭 시 메뉴 닫기
        const mobileLinks = mobileMenu.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', function() {
                mobileMenu.classList.remove('active');
                const spans = menuToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            });
        });
    }
}

// ============ 현재 페이지 네비게이션 하이라이트 ============
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a, .mobile-menu a');

    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add('active');
        }
    });
}

// ============ 스무스 스크롤 ============
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ============ 프로그레스 바 애니메이션 ============
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar-fill');

    if (progressBars.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const progressBar = entry.target;
                const targetWidth = progressBar.getAttribute('data-progress') || progressBar.style.width;
                progressBar.style.width = targetWidth;
            }
        });
    }, { threshold: 0.5 });

    progressBars.forEach(bar => {
        const finalWidth = bar.style.width;
        bar.setAttribute('data-progress', finalWidth);
        bar.style.width = '0%';
        observer.observe(bar);
    });
}

// ============ 카드 애니메이션 ============
function initCardAnimations() {
    const cards = document.querySelectorAll('.card');

    if (cards.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

// ============ 폼 유효성 검사 ============
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#dc3545';

                    // 에러 메시지 표시
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        errorMsg.style.color = '#dc3545';
                        errorMsg.style.fontSize = '0.875rem';
                        errorMsg.style.marginTop = '0.25rem';
                        errorMsg.textContent = '필수 입력 항목입니다.';
                        field.parentNode.insertBefore(errorMsg, field.nextSibling);
                    }
                } else {
                    field.style.borderColor = '';
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                // 첫 번째 에러 필드로 스크롤
                const firstError = form.querySelector('[required]:invalid, [required][value=""]');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });

        // 실시간 유효성 검사
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            field.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.style.borderColor = '';
                    const errorMsg = this.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });
        });
    });
}

// ============ Alert 메시지 자동 닫기 ============
function initAlertAutoClose() {
    const alerts = document.querySelectorAll('.alert[data-auto-close]');

    alerts.forEach(alert => {
        const duration = parseInt(alert.getAttribute('data-auto-close')) || 5000;

        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';

            setTimeout(() => {
                alert.remove();
            }, 300);
        }, duration);

        // 닫기 버튼 추가
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = 'background: none; border: none; font-size: 1.5rem; cursor: pointer; padding: 0; margin-left: auto; opacity: 0.7;';
        closeBtn.addEventListener('click', () => {
            alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        });
        alert.appendChild(closeBtn);
    });
}

// ============ 삭제 확인 다이얼로그 ============
function confirmDelete(message) {
    return confirm(message || '정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.');
}

// 전역 함수로 노출
window.confirmDelete = confirmDelete;

// ============ 날짜 포맷팅 ============
function formatDate(dateString, format = 'YYYY-MM-DD') {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes);
}

// ============ 이미지 미리보기 ============
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            if (previewElement) {
                previewElement.src = e.target.result;
                previewElement.style.display = 'block';
            }
        };

        reader.readAsDataURL(input.files[0]);
    }
}

// 전역 함수로 노출
window.previewImage = previewImage;

// ============ 텍스트 에디터 개선 (선택사항) ============
function enhanceTextareas() {
    const textareas = document.querySelectorAll('.form-textarea[data-enhance]');

    textareas.forEach(textarea => {
        // 자동 높이 조절
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });

        // 초기 높이 설정
        textarea.style.height = textarea.scrollHeight + 'px';
    });
}

enhanceTextareas();

// ============ 검색 필터링 ============
function initSearchFilter() {
    const searchInputs = document.querySelectorAll('[data-search]');

    searchInputs.forEach(input => {
        const targetSelector = input.getAttribute('data-search');
        const targetElements = document.querySelectorAll(targetSelector);

        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();

            targetElements.forEach(element => {
                const text = element.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    element.style.display = '';
                } else {
                    element.style.display = 'none';
                }
            });
        });
    });
}

initSearchFilter();

// ============ 로딩 인디케이터 ============
function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'loading-overlay';
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    loader.innerHTML = '<div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #961A32; border-radius: 50%; animation: spin 1s linear infinite;"></div>';

    // 스피너 애니메이션 추가
    const style = document.createElement('style');
    style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
    document.head.appendChild(style);

    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.remove();
    }
}

// 전역 함수로 노출
window.showLoading = showLoading;
window.hideLoading = hideLoading;

// ============ 폼 제출 시 로딩 표시 ============
document.querySelectorAll('form[data-loading]').forEach(form => {
    form.addEventListener('submit', function() {
        showLoading();
    });
});
