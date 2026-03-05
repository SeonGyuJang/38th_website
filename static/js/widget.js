// ============================================
// 우측 고정 위젯 - 셔틀버스 & 식단표
// kus_bus_website 로직 포팅 + 38th_website 디자인 적용
// ============================================

(function () {
    'use strict';

    // ── 공통 유틸 ──────────────────────────────────────────────────────────

    function openModal(overlay) {
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal(overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    function setupModal(openBtnId, overlayId, closeBtnId, onOpen) {
        const openBtn   = document.getElementById(openBtnId);
        const overlay   = document.getElementById(overlayId);
        const closeBtn  = document.getElementById(closeBtnId);
        if (!openBtn || !overlay || !closeBtn) return;

        openBtn.addEventListener('click', () => {
            openModal(overlay);
            if (onOpen) onOpen();
        });
        closeBtn.addEventListener('click', () => closeModal(overlay));
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal(overlay);
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && overlay.classList.contains('active')) {
                closeModal(overlay);
            }
        });
    }

    // ── 셔틀버스 로직 ──────────────────────────────────────────────────────

    let _busScheduleData = null;
    let _busTimerInterval = null;

    async function loadBusScheduleData() {
        if (_busScheduleData) return _busScheduleData;
        try {
            const res = await fetch(`/schedules/bus_time.csv?v=${Date.now()}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const csv = await res.text();
            const rows = csv.split('\n').slice(1);

            const data = {
                weekday: { schoolToStation: [], stationToSchool: [], osong: [] },
                sunday:  { schoolToStation: [], stationToSchool: [] }
            };

            rows.forEach(row => {
                if (!row.trim()) return;
                const [departure, route, type, note] = row.split(',');
                const item = { departure: departure.trim(), note: (note || '').trim() };
                if (type === 'Weekday') {
                    if      (route === 'School_to_Station')           data.weekday.schoolToStation.push(item);
                    else if (route === 'Station_to_School')           data.weekday.stationToSchool.push(item);
                    else if (route && route.includes('Osong'))        data.weekday.osong.push(item);
                } else if (type === 'Sunday') {
                    if      (route === 'School_to_Station')           data.sunday.schoolToStation.push(item);
                    else if (route === 'Station_to_School')           data.sunday.stationToSchool.push(item);
                }
            });

            _busScheduleData = data;
            return data;
        } catch (e) {
            console.error('버스 시간표 로드 실패:', e);
            return null;
        }
    }

    function getRemainingTime(departure) {
        const now = new Date();
        const [h, m] = departure.split(':').map(Number);
        if (isNaN(h) || isNaN(m)) return null;
        const dep = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m);
        if (dep < now) return null;
        const diff = dep - now;
        return {
            hours:   Math.floor(diff / 3600000),
            minutes: Math.floor((diff % 3600000) / 60000),
            seconds: Math.floor((diff % 60000) / 1000)
        };
    }

    const FRIDAY_NO_SERVICE = {
        schoolToStation: [
            { h: 19, m: 10 }, { h: 19, m: 40 }, { h: 20, m: 10 }, { h: 20, m: 50 }
        ],
        stationToSchool: [
            { h: 19, m: 20 }, { h: 19, m: 50 }, { h: 20, m: 20 }, { h: 21, m: 0 }
        ]
    };

    function isFridayNoService(routeKey, departure) {
        const [h, m] = departure.split(':').map(Number);
        return (FRIDAY_NO_SERVICE[routeKey] || []).some(t => t.h === h && t.m === m);
    }

    function findNextBuses(list, count, routeKey) {
        const now = new Date();
        const cur = now.getHours() * 60 + now.getMinutes();
        const isFri = now.getDay() === 5;
        return list
            .filter(s => {
                const [h, m] = s.departure.split(':').map(Number);
                const t = h * 60 + m;
                if (isFri && routeKey && isFridayNoService(routeKey, s.departure)) {
                    s._fridayNoService = true;
                }
                return t >= cur;
            })
            .slice(0, count);
    }

    function renderBusList(buses, containerId, routeKey) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';

        if (!buses || buses.length === 0) {
            el.innerHTML = '<div class="bus-no-service">운행 예정 버스가 없습니다.</div>';
            return;
        }

        buses.forEach(bus => {
            const div = document.createElement('div');
            if (bus._fridayNoService) {
                div.className = 'bus-item bus-friday';
                div.innerHTML = `
                    <span class="bus-departure">${bus.departure}</span>
                    <span class="bus-note">금요일 미운행</span>
                `;
            } else {
                const rem = getRemainingTime(bus.departure);
                if (!rem) return;
                const isImminent = rem.hours === 0 && rem.minutes <= 4;
                div.className = `bus-item${isImminent ? ' bus-imminent' : ''}`;

                let countdown;
                if (rem.hours > 0) {
                    countdown = `${pad(rem.hours)}:${pad(rem.minutes)}:${pad(rem.seconds)}`;
                } else {
                    countdown = `${pad(rem.minutes)}:${pad(rem.seconds)}`;
                }

                div.innerHTML = `
                    <span class="bus-departure">${bus.departure}</span>
                    <span class="bus-countdown">${countdown}</span>
                    ${bus.note ? `<span class="bus-note">${bus.note}</span>` : ''}
                `;
            }
            el.appendChild(div);
        });
    }

    function pad(n) { return String(n).padStart(2, '0'); }

    async function refreshBusDisplay() {
        const data = await loadBusScheduleData();
        const timeEl = document.getElementById('widgetCurrentTime');

        if (timeEl) {
            const now = new Date();
            timeEl.textContent = now.toLocaleString('ko-KR', {
                month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit',
                hour12: false
            });
        }

        if (!data) return;

        const day = new Date().getDay();
        const isSat = day === 6;
        const isSun = day === 0;
        const noMsg = '<div class="bus-no-service">토요일은 셔틀버스 운행이 없습니다.</div>';

        if (isSat) {
            ['widgetSchoolToStation', 'widgetStationToSchool', 'widgetOsongBuses'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = noMsg;
            });
            return;
        }

        const src = isSun ? data.sunday : data.weekday;
        const buses1 = findNextBuses(src.schoolToStation, 3, 'schoolToStation');
        const buses2 = findNextBuses(src.stationToSchool, 3, 'stationToSchool');
        const buses3 = isSun ? [] : findNextBuses(data.weekday.osong, 3, 'osong');

        renderBusList(buses1, 'widgetSchoolToStation', 'schoolToStation');
        renderBusList(buses2, 'widgetStationToSchool', 'stationToSchool');
        renderBusList(buses3, 'widgetOsongBuses', 'osong');
    }

    function startBusTimer() {
        refreshBusDisplay();
        if (!_busTimerInterval) {
            _busTimerInterval = setInterval(refreshBusDisplay, 500);
        }
    }

    function stopBusTimer() {
        if (_busTimerInterval) {
            clearInterval(_busTimerInterval);
            _busTimerInterval = null;
        }
    }

    // ── 식단표 로직 ──────────────────────────────────────────────────────────

    let _menuLoaded = false;

    async function loadAndRenderMenu() {
        const loading = document.getElementById('menuLoadingIndicator');
        const errorEl = document.getElementById('menuErrorMessage');
        const content = document.getElementById('menuContent');
        if (!loading || !errorEl || !content) return;

        loading.style.display = 'block';
        errorEl.style.display = 'none';
        content.style.display = 'none';

        try {
            const res = await fetch('/api/menu');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            if (!json.success) throw new Error(json.message || '식단표 로드 실패');

            const menuData = json.data;
            if (menuData.학생식당 && menuData.학생식당.기간) {
                const p = menuData.학생식당.기간;
                const weekEl = document.getElementById('menuWeekInfo');
                if (weekEl) weekEl.textContent = `${p.시작일} ~ ${p.종료일}`;
            }

            renderStudentMenu(menuData.학생식당);
            renderStaffMenu(menuData.교직원식당);

            loading.style.display = 'none';
            content.style.display = 'block';
            _menuLoaded = true;
        } catch (e) {
            console.error('식단표 로드 오류:', e);
            loading.style.display = 'none';
            errorEl.style.display = 'block';
            errorEl.textContent = `식단표를 불러오는데 실패했습니다. (${e.message})`;
        }
    }

    const DAY_ORDER = ['월', '화', '수', '목', '금'];
    const STUDENT_MEAL_TYPES = [
        { type: '조식',      time: '07:30~09:00' },
        { type: '중식-한식', time: '11:30~13:30' },
        { type: '중식-일품', time: '11:30~13:30' },
        { type: '중식-plus', time: '11:30~13:30' },
        { type: '중식-분식', time: '11:30~13:30' },
        { type: '석식',      time: '17:30~18:30' }
    ];

    function renderStudentMenu(data) {
        const tbody = document.querySelector('#studentMenuTable tbody');
        if (!tbody || !data || !data.메뉴) return;
        tbody.innerHTML = '';

        STUDENT_MEAL_TYPES.forEach(meal => {
            const tr = document.createElement('tr');
            const th = document.createElement('th');
            th.innerHTML = `${meal.type}<br><small>${meal.time}</small>`;
            tr.appendChild(th);
            for (let i = 0; i < 5; i++) tr.appendChild(document.createElement('td'));
            tbody.appendChild(tr);
        });

        Object.entries(data.메뉴).forEach(([dateStr, dayMenus]) => {
            if (dateStr === '기간') return;
            const match = dateStr.match(/\(([월화수목금])\)/);
            if (!match) return;
            const dayIdx = DAY_ORDER.indexOf(match[1]);
            if (dayIdx === -1) return;
            STUDENT_MEAL_TYPES.forEach((meal, rowIdx) => {
                if (dayMenus[meal.type] && dayMenus[meal.type].메뉴) {
                    const cell = tbody.rows[rowIdx]?.cells[dayIdx + 1];
                    if (cell) {
                        cell.innerHTML = dayMenus[meal.type].메뉴
                            .map(item => `<span class="widget-menu-item">${item}</span>`)
                            .join('');
                    }
                }
            });
        });
    }

    function renderStaffMenu(data) {
        const tbody = document.querySelector('#staffMenuTable tbody');
        if (!tbody || !data || !data.메뉴) return;
        tbody.innerHTML = `
            <tr>
                <th>중식<br><small>11:30~13:30</small></th>
                <td></td><td></td><td></td><td></td><td></td>
            </tr>`;

        Object.entries(data.메뉴).forEach(([dateStr, dayMenus]) => {
            if (dateStr === '기간') return;
            const match = dateStr.match(/\(([월화수목금])\)/);
            if (!match) return;
            const dayIdx = DAY_ORDER.indexOf(match[1]);
            if (dayIdx === -1) return;
            if (dayMenus.중식 && dayMenus.중식.메뉴) {
                const cell = tbody.rows[0]?.cells[dayIdx + 1];
                if (cell) {
                    cell.innerHTML = dayMenus.중식.메뉴
                        .map(item => `<span class="widget-menu-item">${item}</span>`)
                        .join('');
                }
            }
        });
    }

    // ── 탭 전환 ───────────────────────────────────────────────────────────

    function initMenuTabs() {
        const tabs = document.querySelectorAll('.menu-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const target = tab.dataset.tab;
                document.getElementById('studentMenuContent').style.display = target === 'student' ? 'block' : 'none';
                document.getElementById('staffMenuContent').style.display   = target === 'staff'   ? 'block' : 'none';
            });
        });
    }

    // ── 초기화 ────────────────────────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', () => {
        // 버스 모달
        setupModal('widgetBusBtn', 'busModal', 'busModalClose', () => {
            startBusTimer();
        });

        // 버스 모달 닫힐 때 타이머 중지
        const busOverlay = document.getElementById('busModal');
        const busCloseBtn = document.getElementById('busModalClose');
        if (busOverlay) {
            busOverlay.addEventListener('click', (e) => {
                if (e.target === busOverlay) stopBusTimer();
            });
        }
        if (busCloseBtn) {
            busCloseBtn.addEventListener('click', () => stopBusTimer());
        }
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && busOverlay && busOverlay.classList.contains('active')) {
                stopBusTimer();
            }
        });

        // 식단표 모달
        setupModal('widgetMenuBtn', 'menuModal', 'menuModalClose', () => {
            if (!_menuLoaded) loadAndRenderMenu();
        });

        initMenuTabs();
    });
})();
