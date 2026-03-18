// ============================================
// 챗봇 문의 위젯
// ============================================

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

    const widgetBtn      = document.getElementById('widgetInquiryBtn');
    const footerBtn      = document.getElementById('footerInquiryBtn');
    const panel          = document.getElementById('chatPanel');
    const closeBtn       = document.getElementById('chatPanelClose');
    const startBtn       = document.getElementById('chatStartBtn');
    const backBtn        = document.getElementById('chatBackBtn');
    const anotherBtn     = document.getElementById('chatAnotherBtn');
    const form           = document.getElementById('chatInquiryForm');
    const submitBtn      = document.getElementById('chatSubmitBtn');
    const submitText     = document.getElementById('chatSubmitText');
    const submitSpinner  = document.getElementById('chatSubmitSpinner');
    const formError      = document.getElementById('chatFormError');

    const bodyWelcome = document.getElementById('chatBodyWelcome');
    const bodyForm    = document.getElementById('chatBodyForm');
    const bodySuccess = document.getElementById('chatBodySuccess');

    // 모바일 사이드 위젯 접기용
    const sideWidget = document.getElementById('sideWidget');

    if (!panel) return;

    let isOpen = false;

    function collapseWidgetOnMobile() {
        if (window.innerWidth <= 768 && sideWidget && !sideWidget.classList.contains('widget-collapsed')) {
            sideWidget.classList.add('widget-collapsed');
        }
    }

    function openPanel() {
        collapseWidgetOnMobile();
        isOpen = true;
        panel.classList.add('active');
        panel.setAttribute('aria-hidden', 'false');
        if (widgetBtn) widgetBtn.classList.add('is-active');
    }

    function closePanel() {
        isOpen = false;
        panel.classList.remove('active');
        panel.setAttribute('aria-hidden', 'true');
        if (widgetBtn) widgetBtn.classList.remove('is-active');
    }

    function showScreen(screen) {
        bodyWelcome.style.display = 'none';
        bodyForm.style.display    = 'none';
        bodySuccess.style.display = 'none';
        screen.style.display = '';
    }

    function setSubmitting(loading) {
        submitBtn.disabled = loading;
        submitText.style.display    = loading ? 'none' : '';
        submitSpinner.style.display = loading ? '' : 'none';
    }

    function showError(msg) {
        formError.textContent = msg;
        formError.style.display = '';
    }

    function hideError() {
        formError.style.display = 'none';
    }

    // 사이드 위젯 문의 버튼
    if (widgetBtn) {
        widgetBtn.addEventListener('click', function () {
            if (isOpen) closePanel();
            else openPanel();
        });
    }

    // 푸터 문의 버튼
    if (footerBtn) {
        footerBtn.addEventListener('click', function () {
            if (isOpen) closePanel();
            else openPanel();
        });
    }

    // 닫기 버튼
    closeBtn.addEventListener('click', closePanel);

    // 패널 외부 클릭 시 닫기
    document.addEventListener('click', function (e) {
        if (!isOpen) return;
        const triggers = [widgetBtn, footerBtn].filter(Boolean);
        const clickedOutside =
            !panel.contains(e.target) &&
            !triggers.some(t => e.target === t || t.contains(e.target));
        if (clickedOutside) closePanel();
    });

    // ESC 키로 닫기
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isOpen) closePanel();
    });

    // 문의 작성 시작
    startBtn.addEventListener('click', function () {
        showScreen(bodyForm);
    });

    // 돌아가기
    backBtn.addEventListener('click', function () {
        hideError();
        showScreen(bodyWelcome);
    });

    // 또 다른 문의
    anotherBtn.addEventListener('click', function () {
        form.reset();
        hideError();
        showScreen(bodyForm);
    });

    // 폼 제출
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError();

        const name    = document.getElementById('chatName').value.trim();
        const email   = document.getElementById('chatEmail').value.trim();
        const message = document.getElementById('chatMessage').value.trim();

        if (!name || !email || !message) {
            showError('이름, 이메일, 문의 내용을 모두 입력해주세요.');
            return;
        }

        if (!email.includes('@')) {
            showError('올바른 이메일 주소를 입력해주세요.');
            return;
        }

        setSubmitting(true);

        try {
            const res = await fetch('/api/inquiry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, message })
            });

            const data = await res.json();

            if (data.success) {
                form.reset();
                showScreen(bodySuccess);
            } else {
                showError(data.message || '오류가 발생했습니다. 다시 시도해주세요.');
            }
        } catch (err) {
            showError('네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
        } finally {
            setSubmitting(false);
        }
    });

    }); // DOMContentLoaded
})();
