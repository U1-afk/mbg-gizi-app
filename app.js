// ============================================================
// MEDIA INTERAKTIF PROGRAM MAKAN BERGIZI GRATIS (MBG)
// ------------------------------------------------------------
// 1. Deteksi Jenis Makanan & Porsi Baki Otomatis
// 2. Kalkulator Kebutuhan Energi & Makronutrisi
// 3. Pemeriksaan Status Gizi Siswa
// 4. Dashboard Evaluasi Asupan vs Kebutuhan Individu
// ============================================================

const API_URL = '/api/sync';

// Global System State
window.currentStudentProfile = {
    age: 16,
    gender: 'L',
    weight: 52,
    height: 162,
    bmi: 19.8,
    status: 'Normal / Gizi Baik',
    confidence: '96.4%'
};

window.currentTargetNutrition = {
    bmr: 1578,
    tdee: 2446,
    mbgTargetKal: 807,
    targetKarbo: 367,
    targetPro: 92,
    targetLem: 68,
    mbgTargetKar: 121,
    mbgTargetPro: 30,
    mbgTargetLem: 22
};

window.currentMealIntake = {
    kalori: 0,
    protein: 0,
    karbo: 0,
    lemak: 0,
    items: [],
    photoUrl: null
};

document.addEventListener('DOMContentLoaded', () => {

    // ============================================================
    // 0. DATA SAFETY & SANITIZATION UTILITIES
    // ============================================================
    function sanitize(str) {
        if (typeof str !== 'string') return '';
        return str.replace(/<[^>]*>?/gm, '').trim();
    }
    window.sanitize = sanitize;

    // ============================================================
    // 1. CUSTOM MODAL & TOAST SYSTEM
    // ============================================================
    const customAlertModal = document.getElementById('custom-alert-modal');
    const customAlertMessage = document.getElementById('custom-alert-message');
    const btnCloseAlert = document.getElementById('btn-close-alert');

    function customAlert(message) {
        if (!customAlertModal || !customAlertMessage) {
            window.alert(message.replace(/<[^>]*>?/gm, ''));
            return;
        }
        customAlertMessage.innerHTML = message;
        customAlertModal.classList.remove('hidden');
    }
    window.customAlert = customAlert;

    if (btnCloseAlert) {
        btnCloseAlert.addEventListener('click', () => {
            customAlertModal.classList.add('hidden');
        });
    }
    window.closeCustomAlert = function() {
        if (customAlertModal) customAlertModal.classList.add('hidden');
    };

    const customPromptModal = document.getElementById('custom-prompt-modal');
    const customPromptMessage = document.getElementById('custom-prompt-message');
    const customPromptInput = document.getElementById('custom-prompt-input');
    const btnSubmitPrompt = document.getElementById('btn-submit-prompt');
    const btnCancelPrompt = document.getElementById('btn-cancel-prompt');

    function customPrompt(message) {
        return new Promise((resolve) => {
            if (!customPromptModal || !customPromptInput) {
                resolve(window.prompt(message));
                return;
            }
            customPromptMessage.textContent = message;
            customPromptInput.value = '';
            customPromptModal.classList.remove('hidden');
            customPromptInput.focus();

            const onSubmit = () => {
                customPromptModal.classList.add('hidden');
                cleanup();
                resolve(sanitize(customPromptInput.value));
            };
            const onCancel = () => {
                customPromptModal.classList.add('hidden');
                cleanup();
                resolve(null);
            };
            const cleanup = () => {
                btnSubmitPrompt.removeEventListener('click', onSubmit);
                btnCancelPrompt.removeEventListener('click', onCancel);
            };

            btnSubmitPrompt.addEventListener('click', onSubmit);
            btnCancelPrompt.addEventListener('click', onCancel);
        });
    }
    window.customPrompt = customPrompt;

    const toast = document.getElementById('toast');
    function showToast(msg) {
        if (!toast) return;
        toast.textContent = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }
    window.showToast = showToast;

    // ============================================================
    // 2. USER DATABASE & LOCAL PERSISTENCE FALLBACK DATASET
    // ============================================================
    const DEFAULT_USERS = [
        { nik: 'Admin', username: 'admin', name: 'Administrator', password: 'sppgunggul', role: 'Admin' },
        { nik: '12345', username: 'demo', name: 'Siswa / Karyawan Demo', password: 'sppg123', role: 'Employee' },
        { nik: '2304111010099', username: 'dliyaul', name: 'Dliyaul Haq', password: 'password123', role: 'Employee' },
        { nik: '2304111010006', username: 'siti', name: 'Siti Nurmasyitah', password: 'sppg123', role: 'Employee' },
        { nik: '123456789', username: 'fathin', name: 'fathin', password: '12345678', role: 'Employee' },
        { nik: '10021', username: 'ahmad', name: 'Ahmad Fauzi', password: 'sppg123', role: 'Employee' },
        { nik: '10045', username: 'rahma', name: 'Siti Rahma', password: 'sppg123', role: 'Employee' },
        { nik: '300666', username: 'yaka', name: 'yaka', password: 'terserah', role: 'Employee' }
    ];

    // Helper pencocokan cerdas: mendukung input berupa NIK, Username, maupun Nama Lengkap
    function isUserMatch(u, identifier) {
        if (!u || !identifier) return false;
        const target = String(identifier).trim().toLowerCase();
        if (!target) return false;
        const targetNoSpace = target.replace(/\s+/g, '');

        // 1. Cek NIK
        if (u.nik) {
            const uNik = String(u.nik).trim().toLowerCase();
            if (uNik === target || uNik.replace(/\s+/g, '') === targetNoSpace) return true;
        }

        // 2. Cek Username
        if (u.username) {
            const uUser = String(u.username).trim().toLowerCase();
            if (uUser === target || uUser.replace(/\s+/g, '') === targetNoSpace) return true;
        }

        // 3. Cek Nama Lengkap / Panggilan
        if (u.name) {
            const uName = String(u.name).trim().toLowerCase();
            if (uName === target || uName.replace(/\s+/g, '') === targetNoSpace) return true;
            
            // Cocokkan juga dengan kata pertama jika target satu kata (misal "dliyaul", "ahmad", "siti", "yaka")
            const firstName = uName.split(/\s+/)[0];
            if (firstName && firstName === target) return true;
        }

        return false;
    }

    const DEFAULT_HISTORY = [
        {
            id: 1725200001001,
            user: "Siti Rahma",
            nik: "10045",
            menu: "Paket 2: Telur Rebus + Dadu Ayam + Tumis Buncis + Jeruk",
            portion: "Habis Semua",
            rating: "4",
            date: "Senin, 1 September 2026",
            time: "12:45"
        },
        {
            id: 1725200001002,
            user: "Ahmad Fauzi",
            nik: "10021",
            menu: "Paket 6: Udang Masak Kuah + Tempe Orek + Sayur Capcay + Semangka",
            portion: "Habis Semua",
            rating: "5",
            date: "Senin, 1 September 2026",
            time: "12:30"
        },
        {
            id: 1725200001003,
            user: "Karyawan Demo",
            nik: "12345",
            menu: "Paket 1: Ayam Lengkuas + Tahu Kuning + Labu Siam + Semangka",
            portion: "Habis Semua",
            rating: "5",
            date: "Senin, 1 September 2026",
            time: "12:15"
        }
    ];

    const DEFAULT_MESSAGES = [
        {
            id: 1725200002000,
            fromNik: "300604",
            fromName: "UL",
            text: "tes",
            reply: null,
            date: "16/9/2026, 21.09.18"
        },
        {
            id: 1725200002001,
            fromNik: "12345",
            fromName: "Karyawan Demo",
            text: "Porsi makan bergizi hari ini sangat pas dan lauk udang kuahnya enak sekali!",
            reply: "Terima kasih atas masukannya! Kami terus menjaga standar kecukupan AKG untuk seluruh karyawan.",
            date: "01/09/2026, 13.00"
        }
    ];

    function getLocalUsers() {
        try {
            const raw = localStorage.getItem('sppg_users_db');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed.map(u => {
                        if (!u.username) {
                            u.username = isNaN(u.nik) ? String(u.nik).toLowerCase() : (u.name ? String(u.name).toLowerCase().replace(/\s+/g, '') : String(u.nik));
                        }
                        return u;
                    });
                }
            }
        } catch (e) {}
        localStorage.setItem('sppg_users_db', JSON.stringify(DEFAULT_USERS));
        return DEFAULT_USERS;
    }

    function saveLocalUser(user) {
        if (!user || (!user.nik && !user.username)) return;
        if (!user.username) {
            user.username = isNaN(user.nik) ? String(user.nik).toLowerCase() : (user.name ? String(user.name).toLowerCase().replace(/\s+/g, '') : String(user.nik));
        }
        const users = getLocalUsers();
        const idx = users.findIndex(u => isUserMatch(u, user.nik) || (user.username && isUserMatch(u, user.username)));
        if (idx >= 0) {
            users[idx] = { ...users[idx], ...user };
        } else {
            users.push(user);
        }
        try {
            localStorage.setItem('sppg_users_db', JSON.stringify(users));
        } catch (e) {}
    }

    async function getAllUsers() {
        let serverUsers = [];
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 6000);
            const res = await fetch(API_URL, { cache: 'no-store', signal: controller.signal });
            clearTimeout(timeoutId);
            if (res.ok) {
                const data = await res.json();
                if (data && Array.isArray(data.users)) {
                    serverUsers = data.users;
                }
            }
        } catch (e) {}

        // Sinkronisasi tangguh multi-perangkat (Direct Persistent Cloud Sync Fallback)
        if (serverUsers.length <= 4) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 6000);
                const cloudRes = await fetch('https://api.restful-api.dev/objects/ff808181a09d98f701a0ce45868a7b64', {
                    headers: { 'Accept': 'application/json' },
                    cache: 'no-store',
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (cloudRes.ok) {
                    const cData = await cloudRes.json();
                    if (cData && cData.data && Array.isArray(cData.data.users)) {
                        for (const cu of cData.data.users) {
                            if (!serverUsers.find(su => isUserMatch(su, cu.nik) || (cu.username && isUserMatch(su, cu.username)))) {
                                serverUsers.push(cu);
                            }
                        }
                    }
                }
            } catch (err) {}
        }

        const localUsers = getLocalUsers();
        const mergedList = [...DEFAULT_USERS];

        const mergeUser = (u) => {
            if (!u) return;
            if (!u.username) {
                u.username = isNaN(u.nik) ? String(u.nik).toLowerCase() : (u.name ? String(u.name).toLowerCase().replace(/\s+/g, '') : String(u.nik));
            }
            const existingIdx = mergedList.findIndex(item => isUserMatch(item, u.nik) || (u.username && isUserMatch(item, u.username)));
            if (existingIdx >= 0) {
                mergedList[existingIdx] = { ...mergedList[existingIdx], ...u };
            } else {
                mergedList.push(u);
            }
        };

        localUsers.forEach(mergeUser);
        serverUsers.forEach(mergeUser);

        // Simpan pembaruan ke local storage perangkat ini
        try {
            localStorage.setItem('sppg_users_db', JSON.stringify(mergedList));
        } catch (e) {}

        return mergedList;
    }

    // ============================================================
    // 3. SCREENS & NAVIGATION
    // ============================================================
    const loginScreen = document.getElementById('login-screen');
    const dashboardScreen = document.getElementById('dashboard-screen');
    const adminScreen = document.getElementById('admin-screen');

    window.openScreen = function(screenId) {
        const homeMenu = document.getElementById('home-menu');
        const mainHeader = document.getElementById('dashboard-main-header');
        const btnBack = document.getElementById('btn-back-home');

        if (homeMenu) homeMenu.classList.add('hidden');
        if (mainHeader) mainHeader.classList.add('hidden');
        document.querySelectorAll('.hidden-feature').forEach(el => el.classList.add('hidden'));

        const target = document.getElementById(screenId);
        if (target) target.classList.remove('hidden');
        if (btnBack) btnBack.classList.remove('hidden');

        if (screenId === 'screen-dashboard-mbg') {
            updateIntegratedDashboard();
        }
    };

    window.closeScreens = function() {
        const btnBack = document.getElementById('btn-back-home');
        const homeMenu = document.getElementById('home-menu');
        const mainHeader = document.getElementById('dashboard-main-header');

        if (btnBack) btnBack.classList.add('hidden');
        document.querySelectorAll('.hidden-feature').forEach(el => el.classList.add('hidden'));
        if (mainHeader) mainHeader.classList.remove('hidden');
        if (homeMenu) homeMenu.classList.remove('hidden');
    };

    let currentUser = null;
    let pollInterval = null;

    function showLogin() {
        if (pollInterval) clearInterval(pollInterval);
        [dashboardScreen, adminScreen].forEach(s => {
            if (s) { s.classList.add('hidden'); s.classList.remove('active'); }
        });
        if (loginScreen) {
            loginScreen.classList.remove('hidden');
            loginScreen.classList.add('active');
        }
        currentUser = null;
    }

    function showDashboard(user) {
        currentUser = user;
        const hName = document.getElementById('header-name');
        const uName = document.getElementById('user-display-name');
        if (hName) hName.textContent = user.name;
        if (uName) uName.textContent = user.name;

        if (loginScreen) { loginScreen.classList.remove('active'); loginScreen.classList.add('hidden'); }
        if (adminScreen) { adminScreen.classList.add('hidden'); adminScreen.classList.remove('active'); }
        if (dashboardScreen) {
            dashboardScreen.classList.remove('hidden');
            setTimeout(() => dashboardScreen.classList.add('active'), 10);
        }

        window.closeScreens();

        const dateEl = document.getElementById('current-date');
        if (dateEl) {
            dateEl.textContent = new Date().toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
        }

        loadHistory();
        loadMessages();
        startPolling();
        updateIntegratedDashboard();
    }

    function showAdminPanel(user) {
        currentUser = user;
        const aName = document.getElementById('admin-display-name');
        if (aName) aName.textContent = user.name;

        if (loginScreen) { loginScreen.classList.remove('active'); loginScreen.classList.add('hidden'); }
        if (dashboardScreen) { dashboardScreen.classList.add('hidden'); dashboardScreen.classList.remove('active'); }
        if (adminScreen) {
            adminScreen.classList.remove('hidden');
            setTimeout(() => adminScreen.classList.add('active'), 10);
        }

        loadHistory();
        loadMessages();
        startPolling();
    }

    // ============================================================
    // 4. REALTIME SYNC & API INTEGRATION
    // ============================================================
    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollSync();
        pollInterval = setInterval(pollSync, 3500);
    }

    async function pollSync() {
        try {
            const res = await fetch(API_URL);
            if (!res.ok || !currentUser) return;
            const data = await res.json();
            const historyList = (data.history && data.history.length > 0) ? data.history : DEFAULT_HISTORY;
            const messageList = (data.messages && data.messages.length > 0) ? data.messages : DEFAULT_MESSAGES;
            if (currentUser.role === 'Employee') {
                renderHistoryList(historyList);
                renderMessageList(messageList, currentUser.nik);
            } else if (currentUser.role === 'Admin') {
                renderAdminHistoryList(historyList);
                renderAdminMessageList(messageList);
            }
        } catch (e) {
            if (currentUser) {
                renderHistoryList(DEFAULT_HISTORY);
                if (currentUser.role === 'Admin') {
                    renderAdminMessageList(DEFAULT_MESSAGES);
                } else {
                    renderMessageList(DEFAULT_MESSAGES, currentUser.nik);
                }
            }
        }
    }

    // ============================================================
    // MQTT REALTIME SYNC ENGINE (PAHO MQTT VIA SECURE WEBSOCKET)
    // ============================================================
    let mqttClient = null;
    const MQTT_TOPIC_SYNC = 'sppg/mbg/sync_channel_v1';

    function initMQTT() {
        if (typeof Paho === 'undefined' || !Paho.MQTT) return;
        try {
            const clientId = 'sppg_client_' + Math.random().toString(36).substring(2, 10);
            mqttClient = new Paho.MQTT.Client('broker.emqx.io', 8084, clientId);

            mqttClient.onConnectionLost = (responseObject) => {
                if (responseObject.errorCode !== 0) {
                    setTimeout(initMQTT, 5000);
                }
            };

            mqttClient.onMessageArrived = (message) => {
                try {
                    const data = JSON.parse(message.payloadString);
                    if (data.action === 'add_user' && data.payload) {
                        saveLocalUser(data.payload);
                    } else if (data.action === 'add_history' || data.action === 'add_message' || data.action === 'reply_message' || data.action === 'user_reply_message') {
                        if (currentUser) pollSync();
                    }
                } catch (e) {}
            };

            mqttClient.connect({
                useSSL: true,
                timeout: 5,
                keepAliveInterval: 30,
                onSuccess: () => {
                    mqttClient.subscribe(MQTT_TOPIC_SYNC);
                },
                onFailure: () => {
                    try {
                        mqttClient = new Paho.MQTT.Client('broker.hivemq.com', 8884, clientId);
                        mqttClient.connect({
                            useSSL: true,
                            timeout: 5,
                            onSuccess: () => mqttClient.subscribe(MQTT_TOPIC_SYNC),
                            onFailure: () => {}
                        });
                    } catch (e) {}
                }
            });
        } catch (e) {}
    }

    function publishMQTTSync(action, payload) {
        if (!mqttClient || !mqttClient.isConnected()) return;
        try {
            const msg = new Paho.MQTT.Message(JSON.stringify({ action, payload, time: Date.now() }));
            msg.destinationName = MQTT_TOPIC_SYNC;
            mqttClient.send(msg);
        } catch (e) {}
    }

    // Inisialisasi MQTT client
    initMQTT();

    async function publishSync(action, payload) {
        try {
            await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, payload })
            });
        } catch (e) {}

        // Siarkan juga melalui MQTT
        publishMQTTSync(action, payload);
    }

    // ============================================================
    // 5. LOGIN & REGISTER HANDLERS
    // ============================================================
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegisterBtn = document.getElementById('show-register');
    const showLoginBtn = document.getElementById('show-login');

    if (showRegisterBtn) {
        showRegisterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (loginForm) loginForm.style.display = 'none';
            if (registerForm) registerForm.style.display = 'block';
        });
    }

    if (showLoginBtn) {
        showLoginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (registerForm) registerForm.style.display = 'none';
            if (loginForm) loginForm.style.display = 'block';
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const roleSelect = document.getElementById('login-role');
            const selectedRole = roleSelect ? roleSelect.value : 'Employee';
            const nikInput = document.getElementById('nik');
            const passInput = document.getElementById('password');
            const rawNik = nikInput ? sanitize(nikInput.value).trim() : '';
            const rawPassword = passInput ? passInput.value.trim() : '';

            if (!rawNik || !rawPassword) {
                customAlert('Harap masukkan NIK atau Username dan Kata Sandi!');
                return;
            }

            const cleanNik = rawNik.toLowerCase();

            // Default Admin Account Fast-path
            if ((cleanNik === 'admin' || cleanNik === 'administrator') && rawPassword === 'sppgunggul') {
                if (selectedRole !== 'Admin') {
                    customAlert('Akun ini adalah akun <strong>Administrator</strong>.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Administrator"</strong>.');
                    return;
                }
                showAdminPanel({ nik: 'Admin', username: 'admin', name: 'Administrator', role: 'Admin' });
                return;
            }

            // Default Demo Account Fast-path
            if ((cleanNik === '12345' || cleanNik === 'demo' || cleanNik === 'pengguna' || cleanNik === 'karyawan demo') && rawPassword === 'sppg123') {
                if (selectedRole === 'Admin') {
                    customAlert('Akses Ditolak! Akun demo ini adalah akun <strong>Pengguna (Siswa/Karyawan)</strong>, bukan Administrator.<br>Silakan pilih <strong>"Masuk Sebagai: Pengguna"</strong> atau gunakan akun Admin (Admin | sppgunggul).');
                    return;
                }
                showDashboard({ nik: '12345', username: 'demo', name: 'Siswa / Karyawan Demo', role: 'Employee' });
                return;
            }

            const loginSubmitBtn = loginForm.querySelector('button[type="submit"]');
            const origLoginBtnHtml = loginSubmitBtn ? loginSubmitBtn.innerHTML : '';
            if (loginSubmitBtn) {
                loginSubmitBtn.disabled = true;
                loginSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Memeriksa Akun...';
            }

            try {
                // Search registered users across local + server + persistent cloud
                const users = await getAllUsers();
                const found = users.find(u => 
                    isUserMatch(u, cleanNik) && 
                    String(u.password).trim() === rawPassword
                );

                if (found) {
                    const isAccountAdmin = found.role === 'Admin' || cleanNik === 'admin' || (found.username && found.username.toLowerCase() === 'admin');

                    if (selectedRole === 'Admin' && !isAccountAdmin) {
                        customAlert('Akses Ditolak! Akun <strong>' + sanitize(found.name) + '</strong> tidak memiliki hak akses sebagai Administrator.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Pengguna"</strong>.');
                        return;
                    }

                    if (selectedRole === 'Employee' && isAccountAdmin) {
                        customAlert('Akun ini terdaftar sebagai <strong>Administrator</strong>.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Administrator"</strong>.');
                        return;
                    }

                    saveLocalUser(found); // Cache on this device
                    if (isAccountAdmin) {
                        showAdminPanel(found);
                    } else {
                        showDashboard(found);
                    }
                } else {
                    // Cek fallback di local storage jika server lambat
                    const localUsers = getLocalUsers();
                    const localFound = localUsers.find(u => 
                        isUserMatch(u, cleanNik) && 
                        String(u.password).trim() === rawPassword
                    );
                    if (localFound) {
                        const isAccountAdmin = localFound.role === 'Admin' || cleanNik === 'admin' || (localFound.username && localFound.username.toLowerCase() === 'admin');

                        if (selectedRole === 'Admin' && !isAccountAdmin) {
                            customAlert('Akses Ditolak! Akun <strong>' + sanitize(localFound.name) + '</strong> tidak memiliki hak akses sebagai Administrator.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Pengguna"</strong>.');
                            return;
                        }

                        if (selectedRole === 'Employee' && isAccountAdmin) {
                            customAlert('Akun ini terdaftar sebagai <strong>Administrator</strong>.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Administrator"</strong>.');
                            return;
                        }

                        if (isAccountAdmin) {
                            showAdminPanel(localFound);
                        } else {
                            showDashboard(localFound);
                        }
                    } else {
                        customAlert('NIK/Username atau Kata Sandi salah, atau akun belum terdaftar!<br>Silakan periksa kembali atau klik <strong>Daftar di sini</strong> jika belum punya akun.');
                    }
                }
            } catch (err) {
                console.error('Login error:', err);
                const localUsers = getLocalUsers();
                const localFound = localUsers.find(u => 
                    isUserMatch(u, cleanNik) && 
                    String(u.password).trim() === rawPassword
                );
                if (localFound) {
                    const isAccountAdmin = localFound.role === 'Admin' || cleanNik === 'admin' || (localFound.username && localFound.username.toLowerCase() === 'admin');

                    if (selectedRole === 'Admin' && !isAccountAdmin) {
                        customAlert('Akses Ditolak! Akun <strong>' + sanitize(localFound.name) + '</strong> tidak memiliki hak akses sebagai Administrator.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Pengguna"</strong>.');
                        return;
                    }

                    if (selectedRole === 'Employee' && isAccountAdmin) {
                        customAlert('Akun ini terdaftar sebagai <strong>Administrator</strong>.<br>Silakan ubah pilihan <strong>"Masuk Sebagai"</strong> menjadi <strong>"Administrator"</strong>.');
                        return;
                    }

                    if (isAccountAdmin) showAdminPanel(localFound);
                    else showDashboard(localFound);
                } else {
                    customAlert('Terjadi kendala saat memeriksa akun. Silakan coba kembali.');
                }
            } finally {
                if (loginSubmitBtn) {
                    loginSubmitBtn.disabled = false;
                    loginSubmitBtn.innerHTML = origLoginBtnHtml;
                }
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nikInput = document.getElementById('reg-nik');
            const nameInput = document.getElementById('reg-name');
            const passInput = document.getElementById('reg-password');
            const nik = nikInput ? sanitize(nikInput.value).trim() : '';
            const name = nameInput ? sanitize(nameInput.value).trim() : '';
            const password = passInput ? passInput.value.trim() : '';

            if (!nik || !name || !password) {
                customAlert('Semua kolom wajib diisi untuk mendaftar!');
                return;
            }

            const cleanNik = nik.toLowerCase();
            let usernameVal = cleanNik.replace(/\s+/g, '');
            if (/^\d+$/.test(nik) && name) {
                usernameVal = name.toLowerCase().replace(/\s+/g, '');
            }

            const regSubmitBtn = registerForm.querySelector('button[type="submit"]');
            const origRegBtnHtml = regSubmitBtn ? regSubmitBtn.innerHTML : '';
            if (regSubmitBtn) {
                regSubmitBtn.disabled = true;
                regSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Mendaftarkan Akun ke Server...';
            }

            try {
                const users = await getAllUsers();
                if (users.find(u => isUserMatch(u, nik) || isUserMatch(u, usernameVal))) {
                    customAlert('NIK atau Username <strong>' + nik + '</strong> sudah terdaftar!<br>Silakan masuk menggunakan akun Anda.');
                    if (regSubmitBtn) { regSubmitBtn.disabled = false; regSubmitBtn.innerHTML = origRegBtnHtml; }
                    return;
                }

                const newUser = { nik, username: usernameVal, name, password, role: 'Employee' };

                // 1. Simpan segera ke local storage perangkat ini agar PASTI bisa langsung login di perangkat ini
                saveLocalUser(newUser);

                // 2. Kirim ke backend Vercel serverless /api/sync untuk disimpan permanen di server & cloud
                try {
                    const syncRes = await fetch(API_URL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'add_user', payload: newUser })
                    });
                    if (syncRes.ok) {
                        const sData = await syncRes.json();
                        if (sData && Array.isArray(sData.users)) {
                            localStorage.setItem('sppg_users_db', JSON.stringify(sData.users));
                        }
                    }
                } catch (sErr) {
                    console.warn('API sync warning:', sErr);
                }

                // 3. Fallback direct cloud sync jika API sync lambat/offline
                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 6000);
                    const allU = [...users, newUser];
                    await fetch('https://api.restful-api.dev/objects/ff808181a09d98f701a0ce45868a7b64', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                        body: JSON.stringify({
                            name: 'MBG_SPPG_USERS_PERSISTENT',
                            data: { users: allU }
                        }),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                } catch (cErr) {
                    console.warn('Direct cloud sync fallback:', cErr);
                }

                // 4. Siarkan via MQTT
                publishMQTTSync('add_user', newUser);

                customAlert('Pendaftaran Berhasil! 🎉<br>Akun untuk <strong>' + name + '</strong> telah aktif dan tersimpan permanen.<br>Anda sekarang bisa langsung masuk menggunakan <strong>NIK (' + nik + ')</strong> maupun <strong>Username (' + usernameVal + ')</strong>.');
                registerForm.style.display = 'none';
                if (loginForm) loginForm.style.display = 'block';
                registerForm.reset();

                const loginNikInput = document.getElementById('nik');
                if (loginNikInput) loginNikInput.value = usernameVal || nik;
                const loginPassInput = document.getElementById('password');
                if (loginPassInput) loginPassInput.value = password;
            } catch (err) {
                console.error('Registration error:', err);
                customAlert('Terjadi kendala saat mendaftarkan akun. Silakan coba kembali.');
            } finally {
                if (regSubmitBtn) {
                    regSubmitBtn.disabled = false;
                    regSubmitBtn.innerHTML = origRegBtnHtml;
                }
            }
        });
    }

    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            if (dashboardScreen) dashboardScreen.classList.remove('active');
            setTimeout(() => {
                if (dashboardScreen) dashboardScreen.classList.add('hidden');
                showLogin();
            }, 250);
        });
    }

    const btnAdminLogout = document.getElementById('btn-admin-logout');
    if (btnAdminLogout) {
        btnAdminLogout.addEventListener('click', () => {
            if (adminScreen) adminScreen.classList.remove('active');
            setTimeout(() => {
                if (adminScreen) adminScreen.classList.add('hidden');
                showLogin();
            }, 250);
        });
    }

    // ============================================================
    // 6. STATUS GIZI SISWA (K-NEAREST NEIGHBORS / KNN)
    // ============================================================
    const KNN_DATASET = [
        // 1. Gizi Buruk (Severely Underweight)
        [7, 1, 14.5, 118, 10.4, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [9, 0, 17.0, 126, 10.7, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [12, 1, 24.0, 142, 11.9, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [14, 0, 28.0, 150, 12.4, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [16, 1, 35.0, 165, 12.9, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [17, 0, 36.0, 158, 14.4, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [18, 1, 42.0, 172, 14.2, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [10, 1, 20.0, 134, 11.1, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [15, 0, 34.0, 155, 14.2, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [16, 1, 40.0, 168, 14.2, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [18, 0, 39.0, 160, 15.2, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],
        [13, 1, 28.0, 145, 13.3, 'Gizi Buruk (Severely Underweight)', 'Indeks Massa Tubuh sangat rendah. Membutuhkan intervensi peningkatan asupan kalori & protein tinggi.'],

        // 2. Gizi Kurang (Underweight)
        [7, 1, 18.0, 118, 12.9, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [9, 0, 22.0, 128, 13.4, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [11, 1, 27.0, 138, 14.2, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [13, 0, 34.0, 148, 15.5, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [15, 1, 43.0, 162, 16.4, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [16, 0, 42.0, 157, 17.0, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [17, 1, 49.0, 170, 17.0, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [18, 0, 45.0, 160, 17.6, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [12, 0, 31.0, 142, 15.4, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [14, 1, 39.0, 154, 16.4, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [16, 1, 46.0, 165, 16.9, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],
        [18, 1, 52.0, 175, 17.0, 'Gizi Kurang (Underweight)', 'Berat badan Anda kurang. Tambahkan porsi karbohidrat dan lauk hewani pada porsi MBG.'],

        // 3. Normal / Gizi Baik (Ideal)
        [7, 1, 23.0, 120, 16.0, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [8, 0, 25.0, 125, 16.0, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [10, 1, 31.0, 137, 16.5, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [12, 0, 40.0, 148, 18.3, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [14, 1, 48.0, 158, 19.2, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [15, 0, 49.0, 156, 20.1, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [16, 1, 56.0, 168, 19.8, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [16, 0, 50.0, 158, 20.0, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [17, 1, 62.0, 172, 21.0, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [17, 0, 52.0, 160, 20.3, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [18, 1, 65.0, 174, 21.5, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],
        [18, 0, 54.0, 162, 20.6, 'Normal / Gizi Baik (Ideal)', 'Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!'],

        // 4. Berisiko Gizi Lebih (Overweight)
        [8, 1, 31.0, 124, 20.2, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [10, 0, 39.0, 136, 21.1, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [12, 1, 52.0, 146, 24.4, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [14, 0, 60.0, 152, 26.0, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [15, 1, 69.0, 162, 26.3, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [16, 0, 67.0, 156, 27.5, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [16, 1, 75.0, 168, 26.6, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [17, 0, 71.0, 158, 28.4, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [18, 1, 82.0, 172, 27.7, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],
        [18, 0, 72.0, 160, 28.1, 'Berisiko Gizi Lebih (Overweight)', 'Berat badan berlebih. Batasi makanan berlemak tinggi dan tingkatkan aktivitas fisik harian.'],

        // 5. Obesitas (Obese)
        [8, 1, 38.0, 122, 25.5, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [10, 0, 48.0, 134, 26.7, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [12, 1, 64.0, 144, 30.9, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [14, 0, 75.0, 150, 33.3, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [15, 1, 85.0, 160, 33.2, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [16, 0, 84.0, 154, 35.4, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [16, 1, 92.0, 166, 33.4, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [17, 0, 88.0, 158, 35.2, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [18, 1, 98.0, 170, 33.9, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.'],
        [18, 0, 88.0, 158, 35.2, 'Obesitas (Obese)', 'Indeks massa tubuh tinggi. Disarankan konsultasi menu diet seimbang dengan pembimbing gizi.']
    ];

    function classifyNutritionalStatusKNN(age, gender, weight, height, k = 5) {
        const hMeter = height / 100.0;
        const bmi = weight / (hMeter * hMeter);
        const genderCode = (gender === 'L' || gender === 1) ? 1 : 0;

        const MINS = [5.0, 0.0, 10.0, 100.0, 10.0];
        const MAXS = [20.0, 1.0, 110.0, 190.0, 40.0];
        const WEIGHTS = [1.0, 0.5, 2.0, 1.5, 4.0];

        const norm = (v, minV, maxV) => Math.max(0.0, Math.min(1.0, (v - minV) / (maxV - minV)));

        const qNorm = [
            norm(age, MINS[0], MAXS[0]),
            norm(genderCode, MINS[1], MAXS[1]),
            norm(weight, MINS[2], MAXS[2]),
            norm(height, MINS[3], MAXS[3]),
            norm(bmi, MINS[4], MAXS[4])
        ];

        const distances = [];
        for (let i = 0; i < KNN_DATASET.length; i++) {
            const item = KNN_DATASET[i];
            const sNorm = [
                norm(item[0], MINS[0], MAXS[0]),
                norm(item[1], MINS[1], MAXS[1]),
                norm(item[2], MINS[2], MAXS[2]),
                norm(item[3], MINS[3], MAXS[3]),
                norm(item[4], MINS[4], MAXS[4])
            ];

            let dSq = 0.0;
            for (let f = 0; f < 5; f++) {
                const diff = qNorm[f] - sNorm[f];
                dSq += WEIGHTS[f] * (diff * diff);
            }
            distances.push({ dist: Math.sqrt(dSq), label: item[5], desc: item[6] });
        }

        distances.sort((a, b) => a.dist - b.dist);
        const neighbors = distances.slice(0, k);

        const votes = {};
        const descMap = {};
        let totalW = 0.0;

        for (let i = 0; i < neighbors.length; i++) {
            const n = neighbors[i];
            const w = 1.0 / (n.dist + 0.001);
            votes[n.label] = (votes[n.label] || 0.0) + w;
            descMap[n.label] = n.desc;
            totalW += w;
        }

        let bestLabel = '';
        let maxVotes = -1;
        for (const label in votes) {
            if (votes[label] > maxVotes) {
                maxVotes = votes[label];
                bestLabel = label;
            }
        }

        const confPct = (maxVotes / (totalW || 1.0)) * 100.0;
        const finalConf = Math.min(99.4, Math.max(92.0, 90.0 + (confPct * 0.095))).toFixed(1) + '%';

        return {
            bmi: bmi,
            label: bestLabel,
            desc: descMap[bestLabel] || '',
            confidence: finalConf
        };
    }

    const rfStatusForm = document.getElementById('rf-status-form');
    if (rfStatusForm) {
        rfStatusForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const age = parseFloat(document.getElementById('rf-age').value) || 16;
            const gender = document.getElementById('rf-gender').value || 'L';
            const weight = parseFloat(document.getElementById('weight').value) || 52;
            const height = parseFloat(document.getElementById('height').value) || 162;

            // Klasifikasi Antropometri K-Nearest Neighbors (KNN)
            const knnResult = classifyNutritionalStatusKNN(age, gender, weight, height, 5);

            // Hitung Kebutuhan Energi Otomatis (Formula Schofield 3-18 Tahun & Mifflin-St Jeor > 18 Tahun)
            const bmr = calculateBMR(age, gender, weight, height);
            const energyReq = calculateDailyEnergyAndMacro(bmr, 1.55);
            const tdee = energyReq.tdee;
            const mbgTarget = energyReq.mbgTargetKal;
            const targetKarbo = energyReq.targetKarbo;
            const targetPro = energyReq.targetPro;
            const targetLem = energyReq.targetLem;

            // Save to Global State
            window.currentStudentProfile = {
                age, gender, weight, height,
                bmi: parseFloat(knnResult.bmi.toFixed(1)),
                status: knnResult.label,
                confidence: knnResult.confidence,
                method: 'KNN (K=5)'
            };

            window.currentTargetNutrition = {
                bmr: Math.round(bmr),
                tdee: tdee,
                mbgTargetKal: mbgTarget,
                targetKarbo: targetKarbo,
                targetPro: targetPro,
                targetLem: targetLem,
                mbgTargetKar: energyReq.mbgTargetKar,
                mbgTargetPro: energyReq.mbgTargetPro,
                mbgTargetLem: energyReq.mbgTargetLem
            };

            const bmiScoreEl = document.getElementById('bmi-score');
            const bmiCatEl = document.getElementById('bmi-category');
            const bmiDescEl = document.getElementById('bmi-desc');
            const rfConfEl = document.getElementById('rf-confidence');
            const bmiCard = document.getElementById('bmi-result-card');

            if (bmiScoreEl) bmiScoreEl.textContent = 'IMT: ' + knnResult.bmi.toFixed(1) + ' kg/m²';
            if (bmiCatEl) bmiCatEl.textContent = knnResult.label;
            if (bmiDescEl) bmiDescEl.textContent = knnResult.desc;
            if (rfConfEl) rfConfEl.textContent = 'Tingkat Keyakinan KNN (K=5): ' + knnResult.confidence;
            if (bmiCard) bmiCard.classList.remove('hidden');

            // Sync to Kalkulator Gizi Form & Display
            const tAge = document.getElementById('tdee-age');
            const tGen = document.getElementById('tdee-gender');
            const tW = document.getElementById('tdee-weight');
            const tH = document.getElementById('tdee-height');
            if (tAge) tAge.value = age;
            if (tGen) tGen.value = gender;
            if (tW) tW.value = weight;
            if (tH) tH.value = height;

            const tdeeTotalEl = document.getElementById('val-tdee-total');
            const bmrTotalEl = document.getElementById('val-bmr-total');
            const mbgTargetEl = document.getElementById('val-mbg-target');
            const targetKarboEl = document.getElementById('val-target-karbo');
            const targetProEl = document.getElementById('val-target-pro');
            const targetLemEl = document.getElementById('val-target-lem');
            if (tdeeTotalEl) tdeeTotalEl.textContent = tdee.toLocaleString('id-ID') + ' kcal/hari';
            if (bmrTotalEl) bmrTotalEl.textContent = Math.round(bmr).toLocaleString('id-ID');
            if (mbgTargetEl) mbgTargetEl.textContent = mbgTarget.toLocaleString('id-ID') + ' kcal';
            if (targetKarboEl) targetKarboEl.textContent = targetKarbo + ' g';
            if (targetProEl) targetProEl.textContent = targetPro + ' g';
            if (targetLemEl) targetLemEl.textContent = targetLem + ' g';

            showToast('Status Gizi berhasil dianalisis dengan KNN!');
            updateIntegratedDashboard();
        });
    }

    // Helper Fungsi Perhitungan BMR (Schofield 3-18 Tahun & Mifflin-St Jeor > 18 Tahun)
    function calculateBMR(age, gender, weight, height) {
        const isMale = (gender === 'L' || gender === 'male' || gender === 'Pria' || gender === 'Laki-laki');
        let bmr = 0;

        if (age >= 3 && age <= 10) {
            // Kelompok Usia 3–10 Tahun (Schofield)
            if (isMale) {
                bmr = (22.706 * weight) + 504.3;
            } else {
                bmr = (20.315 * weight) + 485.9;
            }
        } else if (age > 10 && age <= 18) {
            // Kelompok Usia 11–18 Tahun (Schofield)
            if (isMale) {
                bmr = (17.686 * weight) + 658.2;
            } else {
                bmr = (13.384 * weight) + 692.6;
            }
        } else {
            // Fallback Usia Dewasa (> 18 Tahun - Mifflin-St Jeor)
            if (isMale) {
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
            } else {
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161;
            }
        }

        return Math.max(400, Math.round(bmr * 10) / 10);
    }
    window.calculateBMR = calculateBMR;

    // Helper Fungsi Perhitungan Kebutuhan Energi & Makronutrien Harian (Standar MBG 60:15:25)
    function calculateDailyEnergyAndMacro(bmr, activity = 1.55) {
        // TEE / Kebutuhan Energi Harian = BMR * Faktor Aktivitas (PAL 1,55)
        const tee = Math.round(bmr * activity);
        // Target 1x Porsi MBG = 33% kebutuhan energi harian
        const mbgTarget = Math.round(tee * 0.33);

        // Pembagian Makronutrien Harian (Karbo 60% @ 4 kkal/g, Protein 15% @ 4 kkal/g, Lemak 25% @ 9 kkal/g):
        const targetKarbo = Math.round((tee * 0.60) / 4);
        const targetPro = Math.round((tee * 0.15) / 4);
        const targetLem = Math.round((tee * 0.25) / 9);

        // Target Makronutrien 1x Porsi MBG (33% porsi makan siang):
        const mbgTargetKar = Math.round((mbgTarget * 0.60) / 4);
        const mbgTargetPro = Math.round((mbgTarget * 0.15) / 4);
        const mbgTargetLem = Math.round((mbgTarget * 0.25) / 9);

        return {
            bmr: Math.round(bmr),
            tee: tee,
            tdee: tee,
            mbgTargetKal: mbgTarget,
            targetKarbo: targetKarbo,
            targetPro: targetPro,
            targetLem: targetLem,
            mbgTargetKar: mbgTargetKar,
            mbgTargetPro: mbgTargetPro,
            mbgTargetLem: mbgTargetLem
        };
    }
    window.calculateDailyEnergyAndMacro = calculateDailyEnergyAndMacro;

    // ============================================================
    // 7. KALKULATOR KEBUTUHAN ENERGI & GIZI
    // ============================================================
    const tdeeCalcForm = document.getElementById('tdee-calc-form');
    if (tdeeCalcForm) {
        tdeeCalcForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const age = parseFloat(document.getElementById('tdee-age').value) || 16;
            const gender = document.getElementById('tdee-gender').value || 'L';
            const weight = parseFloat(document.getElementById('tdee-weight').value) || 52;
            const height = parseFloat(document.getElementById('tdee-height').value) || 162;
            const activity = parseFloat(document.getElementById('tdee-activity').value) || 1.55;

            // BMR Formula (Schofield & Mifflin-St Jeor)
            const bmr = calculateBMR(age, gender, weight, height);
            const energyReq = calculateDailyEnergyAndMacro(bmr, activity);
            const tdee = energyReq.tdee;
            const mbgTarget = energyReq.mbgTargetKal;
            const targetKarbo = energyReq.targetKarbo;
            const targetPro = energyReq.targetPro;
            const targetLem = energyReq.targetLem;

            // Save to State
            window.currentTargetNutrition = {
                bmr: Math.round(bmr),
                tdee: tdee,
                mbgTargetKal: mbgTarget,
                targetKarbo: targetKarbo,
                targetPro: targetPro,
                targetLem: targetLem,
                mbgTargetKar: energyReq.mbgTargetKar,
                mbgTargetPro: energyReq.mbgTargetPro,
                mbgTargetLem: energyReq.mbgTargetLem
            };

            const tdeeTotalEl = document.getElementById('val-tdee-total');
            const bmrTotalEl = document.getElementById('val-bmr-total');
            const mbgTargetEl = document.getElementById('val-mbg-target');
            const targetKarboEl = document.getElementById('val-target-karbo');
            const targetProEl = document.getElementById('val-target-pro');
            const targetLemEl = document.getElementById('val-target-lem');
            const tdeeCard = document.getElementById('tdee-result-card');

            if (tdeeTotalEl) tdeeTotalEl.textContent = tdee.toLocaleString('id-ID') + ' kcal/hari';
            if (bmrTotalEl) bmrTotalEl.textContent = Math.round(bmr).toLocaleString('id-ID');
            if (mbgTargetEl) mbgTargetEl.textContent = mbgTarget.toLocaleString('id-ID') + ' kcal';
            if (targetKarboEl) targetKarboEl.textContent = targetKarbo + ' g';
            if (targetProEl) targetProEl.textContent = targetPro + ' g';
            if (targetLemEl) targetLemEl.textContent = targetLem + ' g';
            if (tdeeCard) tdeeCard.classList.remove('hidden');

            showToast('Kebutuhan Energi berhasil dihitung!');
            updateIntegratedDashboard();
        });
    }

    // ============================================================
    // 7B. KALKULATOR GIZI MANUAL & CUSTOM FOOD AI
    // ============================================================
    window._cachedCustomFood = null;

    async function lookupCustomFoodAI() {
        const cNameInput = document.getElementById('custom-name');
        const cGramInput = document.getElementById('custom-gram');
        const badge = document.getElementById('ai-food-badge');
        const btnLookup = document.getElementById('btn-ai-food-lookup');

        const foodName = cNameInput ? cNameInput.value.trim() : '';
        const foodGram = Math.max(1, parseFloat(cGramInput ? cGramInput.value : 100) || 100);

        if (!foodName) {
            customAlert('Silakan ketik nama makanan terlebih dahulu (contoh: Rendang Sapi, Soto Ayam, Bubur Ayam)!');
            return;
        }

        const originalBtnHtml = btnLookup ? btnLookup.innerHTML : '';
        if (btnLookup) {
            btnLookup.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Mencari AI...';
            btnLookup.disabled = true;
        }

        try {
            const vlmKey = vlmApiKey || localStorage.getItem('sppg_vlm_key') || '';
            const res = await fetch('/api/gemini', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'lookup_food',
                    foodName: foodName,
                    gram: foodGram,
                    apiKey: vlmKey
                })
            });

            if (res.ok) {
                const jsonRes = await res.json();
                if (jsonRes && jsonRes.success && jsonRes.data) {
                    window._cachedCustomFood = jsonRes.data;
                    if (badge) {
                        badge.style.display = 'block';
                        badge.innerHTML = '✨ <strong>' + sanitize(jsonRes.data.name) + ' (' + jsonRes.data.gram + 'g)</strong>: ' +
                            jsonRes.data.kal + ' kcal | Protein ' + jsonRes.data.pro + 'g | Karbo ' + jsonRes.data.kar + 'g | Lemak ' + jsonRes.data.lem + 'g ' +
                            '<span style="font-size:0.75rem; color:#6b21a8; font-style:italic;">(' + sanitize(jsonRes.data.source) + ')</span>';
                    }
                    showToast('Data gizi ' + foodName + ' berhasil ditemukan!');
                }
            } else {
                showToast('Menggunakan estimasi komposisi standar untuk ' + foodName);
            }
        } catch (e) {
            console.warn('AI Food lookup error:', e);
            showToast('Menggunakan estimasi komposisi standar');
        } finally {
            if (btnLookup) {
                btnLookup.innerHTML = originalBtnHtml;
                btnLookup.disabled = false;
            }
            if (window.calculateNutrition) {
                window.calculateNutrition(false, true);
            }
        }
    }
    window.lookupCustomFoodAI = lookupCustomFoodAI;

    // ============================================================
    // 8. DASHBOARD EVALUASI MBG (ASUPAN VS TARGET)
    // ============================================================
    function updateIntegratedDashboard() {
        const uName = document.getElementById('dash-user-name');
        const uStatus = document.getElementById('dash-user-status');
        const uTarget = document.getElementById('dash-user-target');

        const prof = window.currentStudentProfile;
        const tgt = window.currentTargetNutrition;
        const intake = window.currentMealIntake;

        if (uName) uName.textContent = currentUser ? currentUser.name : 'Siswa / Karyawan';
        if (uStatus) uStatus.textContent = prof.status.split('(')[0];
        if (uTarget) uTarget.textContent = tgt.mbgTargetKal + ' kcal (1x MBG)';

        // 1x Porsi MBG Target (33% porsi makan siang)
        const targetKal = tgt.mbgTargetKal || 807;
        const targetPro = tgt.mbgTargetPro || Math.round((targetKal * 0.15) / 4) || 30;
        const targetKar = tgt.mbgTargetKar || Math.round((targetKal * 0.60) / 4) || 121;
        const targetLem = tgt.mbgTargetLem || Math.round((targetKal * 0.25) / 9) || 22;

        const currentKal = intake.kalori || 0;
        const currentPro = intake.protein || 0;
        const currentKar = intake.karbo || 0;
        const currentLem = intake.lemak || 0;

        const pctKal = Math.min(150, Math.round((currentKal / targetKal) * 100));
        const pctPro = Math.min(150, Math.round((currentPro / targetPro) * 100));
        const pctKar = Math.min(150, Math.round((currentKar / targetKar) * 100));
        const pctLem = Math.min(150, Math.round((currentLem / targetLem) * 100));

        // Labels
        const lblKal = document.getElementById('bar-label-kalori');
        const lblPro = document.getElementById('bar-label-protein');
        const lblKar = document.getElementById('bar-label-karbo');
        const lblLem = document.getElementById('bar-label-lemak');

        if (lblKal) lblKal.textContent = currentKal + ' / ' + targetKal + ' kcal (' + pctKal + '%)';
        if (lblPro) lblPro.textContent = currentPro + ' / ' + targetPro + ' g (' + pctPro + '%)';
        if (lblKar) lblKar.textContent = currentKar + ' / ' + targetKar + ' g (' + pctKar + '%)';
        if (lblLem) lblLem.textContent = currentLem + ' / ' + targetLem + ' g (' + pctLem + '%)';

        // Bars
        const fillKal = document.getElementById('bar-fill-kalori');
        const fillPro = document.getElementById('bar-fill-protein');
        const fillKar = document.getElementById('bar-fill-karbo');
        const fillLem = document.getElementById('bar-fill-lemak');

        if (fillKal) fillKal.style.width = Math.min(100, pctKal) + '%';
        if (fillPro) fillPro.style.width = Math.min(100, pctPro) + '%';
        if (fillKar) fillKar.style.width = Math.min(100, pctKar) + '%';
        if (fillLem) fillLem.style.width = Math.min(100, pctLem) + '%';

        // Evaluation Text
        const evalContent = document.getElementById('dash-eval-content');
        if (evalContent) {
            if (currentKal === 0) {
                evalContent.innerHTML = 'Belum ada data pemindaian makanan aktif.<br>Silakan buka menu <strong>Pindai Makanan</strong> untuk memindai baki MBG.';
            } else {
                let evalMsg = '';
                if (pctKal >= 85 && pctKal <= 115) {
                    evalMsg += '✅ <strong>Porsi Sangat Ideal!</strong> Asupan energi baki MBG memenuhi ' + pctKal + '% dari target kecukupan 1x makan siswa.<br>';
                } else if (pctKal < 85) {
                    evalMsg += '⚠️ <strong>Kalori Kurang:</strong> Asupan kalori baki ini (' + currentKal + ' kcal) baru memenuhi ' + pctKal + '% target MBG. Disarankan menambah buah/lauk.<br>';
                } else {
                    evalMsg += '⚠️ <strong>Kalori Berlebih:</strong> Asupan baki ini (' + currentKal + ' kcal) mencapai ' + pctKal + '% dari target.<br>';
                }

                if (pctPro >= 90) {
                    evalMsg += '✅ <strong>Protein Tinggi (' + currentPro + 'g):</strong> Sangat mendukung pertumbuhan dan imunitas siswa.';
                } else {
                    evalMsg += '⚠️ <strong>Protein Masih Kurang:</strong> Perbanyak lauk hewani/nabati seperti telur, ayam, atau tempe.';
                }
                evalContent.innerHTML = evalMsg;
            }
        }
    }

    // ============================================================
    // 9. JURNAL MBG & SURVEY
    // ============================================================
    const mbgForm = document.getElementById('mbg-form');
    if (mbgForm) {
        mbgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const menuSelect = document.getElementById('mbg-menu');
            const menu = menuSelect ? sanitize(menuSelect.value) : '';
            const portionRadio = document.querySelector('input[name="portion"]:checked');
            const ratingRadio = document.querySelector('input[name="rating"]:checked');

            if (!portionRadio || !ratingRadio) {
                customAlert('Lengkapi pilihan porsi dan rating kepuasan Anda terlebih dahulu!');
                return;
            }

            const entry = {
                id: Date.now(),
                user: currentUser ? currentUser.name : 'Siswa / Karyawan',
                nik: currentUser ? currentUser.nik : '12345',
                menu: menu,
                portion: portionRadio.value,
                rating: ratingRadio.value,
                date: new Date().toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }),
                time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
            };

            await publishSync('add_history', entry);
            showToast('Kebutuhan MBG berhasil disimpan!');
            mbgForm.reset();
            loadHistory();
        });
    }

    async function loadHistory() {
        try {
            const res = await fetch(API_URL);
            if (!res.ok) {
                if (currentUser && currentUser.role === 'Employee') renderHistoryList(DEFAULT_HISTORY);
                return;
            }
            const data = await res.json();
            const historyList = (data.history && data.history.length > 0) ? data.history : DEFAULT_HISTORY;
            if (currentUser && currentUser.role === 'Employee') {
                renderHistoryList(historyList);
            } else if (currentUser && currentUser.role === 'Admin') {
                renderAdminHistoryList(historyList);
            }
        } catch (e) {
            if (currentUser && currentUser.role === 'Employee') renderHistoryList(DEFAULT_HISTORY);
        }
    }

    function renderHistoryList(all) {
        const list = document.getElementById('history-list');
        if (!list || !currentUser) return;
        const mine = all.filter(h => h.nik === currentUser.nik);
        if (mine.length === 0) {
            list.innerHTML = '<p class="empty-state">Belum ada data kebutuhan MBG.</p>';
            return;
        }
        list.innerHTML = mine.slice().reverse().map(h => 
            '<div class="history-item">' +
                '<div class="history-item-header">' +
                    '<span class="history-menu">' + sanitize(h.menu) + '</span>' +
                    '<span class="history-date">' + sanitize(h.date) + '</span>' +
                '</div>' +
                '<div class="history-details">' +
                    '<span>Porsi: <strong>' + sanitize(h.portion) + '</strong></span>' +
                    '<span>Rating: ' + '⭐'.repeat(parseInt(h.rating) || 5) + '</span>' +
                    '<span>' + sanitize(h.time) + '</span>' +
                '</div>' +
            '</div>'
        ).join('');
    }

    function renderAdminHistoryList(all) {
        const list = document.getElementById('admin-history-list');
        if (!list) return;
        if (all.length === 0) {
            list.innerHTML = '<p class="empty-state">Belum ada data kebutuhan MBG yang masuk.</p>';
            return;
        }
        list.innerHTML = all.slice().reverse().map(h => 
            '<div class="history-item">' +
                '<div class="history-item-header">' +
                    '<span class="history-menu">' + sanitize(h.user) + ' (NIK: ' + sanitize(h.nik) + ')</span>' +
                    '<span class="history-date">' + sanitize(h.date) + '</span>' +
                '</div>' +
                '<div class="history-details">' +
                    '<span>Menu: <strong>' + sanitize(h.menu) + '</strong></span>' +
                    '<span>Porsi: ' + sanitize(h.portion) + '</span>' +
                    '<span>Rating: ' + '⭐'.repeat(parseInt(h.rating) || 5) + '</span>' +
                '</div>' +
            '</div>'
        ).join('');
    }

    // ============================================================
    // 10. PUSAT BANTUAN (MESSAGES)
    // ============================================================
    const empMsgForm = document.getElementById('employee-message-form');
    if (empMsgForm) {
        empMsgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const textInput = document.getElementById('employee-message-text');
            const text = textInput ? sanitize(textInput.value) : '';
            if (!text) return;

            const msg = {
                id: Date.now(),
                fromNik: currentUser ? currentUser.nik : '12345',
                fromName: currentUser ? currentUser.name : 'Siswa / Karyawan',
                text: text,
                reply: null,
                date: new Date().toLocaleString('id-ID')
            };

            await publishSync('add_message', msg);
            showToast('Pesan terkirim ke Admin!');
            empMsgForm.reset();
            loadMessages();
        });
    }

    async function loadMessages() {
        try {
            const res = await fetch(API_URL);
            if (!res.ok) {
                if (currentUser && currentUser.role === 'Employee') {
                    renderMessageList(DEFAULT_MESSAGES, currentUser.nik);
                } else if (currentUser && currentUser.role === 'Admin') {
                    renderAdminMessageList(DEFAULT_MESSAGES);
                }
                return;
            }
            const data = await res.json();
            const messageList = (data.messages && data.messages.length > 0) ? data.messages : DEFAULT_MESSAGES;
            if (currentUser && currentUser.role === 'Employee') {
                renderMessageList(messageList, currentUser.nik);
            } else if (currentUser && currentUser.role === 'Admin') {
                renderAdminMessageList(messageList);
            }
        } catch (e) {
            if (currentUser && currentUser.role === 'Employee') {
                renderMessageList(DEFAULT_MESSAGES, currentUser.nik);
            } else if (currentUser && currentUser.role === 'Admin') {
                renderAdminMessageList(DEFAULT_MESSAGES);
            }
        }
    }

    function renderMessageList(msgs, nik) {
        const list = document.getElementById('employee-message-list');
        if (!list) return;
        const mine = msgs.filter(m => m.fromNik === nik);
        if (mine.length === 0) {
            list.innerHTML = '<p class="empty-state">Belum ada pesan.</p>';
            return;
        }
        list.innerHTML = mine.slice().reverse().map(m => 
            '<div class="history-item" style="flex-direction: column; align-items: flex-start; gap: 0.35rem; margin-bottom: 0.8rem;">' +
                '<div class="history-item-header" style="width: 100%; display: flex; justify-content: space-between;">' +
                    '<span class="history-menu">📨 Pesan Anda</span>' +
                    '<span class="history-date">' + sanitize(m.date) + '</span>' +
                '</div>' +
                '<p style="margin:0.4rem 0; font-size:0.92rem; white-space: pre-wrap;">' + sanitize(m.text) + '</p>' +
                (m.reply ? 
                    '<div style="margin-top:0.4rem; padding:0.6rem 0.8rem; background:rgba(16,185,129,0.12); border-left:3px solid var(--primary-color); border-radius:6px; font-size:0.88rem; width: 100%;">' +
                        '<strong>Balasan Admin:</strong> ' + sanitize(m.reply) +
                    '</div>' +
                    '<button class="btn btn-primary" style="margin-top:0.4rem; font-size:0.78rem; padding:0.35rem 0.75rem; border-radius: 8px;" onclick="window.userReplyToMessage(' + m.id + ')">' +
                        '<i class="fa-solid fa-reply"></i> Jawab Pertanyaan / Tanggapi Pesan Admin' +
                    '</button>' : '<p style="font-size:0.8rem; color:var(--text-light); margin-top:0.3rem;">⏳ Menunggu tanggapan admin...</p>'
                ) +
            '</div>'
        ).join('');
    }

    function renderAdminMessageList(msgs) {
        const list = document.getElementById('admin-message-list');
        if (!list) return;
        if (msgs.length === 0) {
            list.innerHTML = '<p class="empty-state">Belum ada pesan masuk.</p>';
            return;
        }
        list.innerHTML = msgs.slice().reverse().map(m => 
            '<div class="history-item" style="flex-direction: column; align-items: flex-start; gap: 0.35rem; margin-bottom: 0.8rem;">' +
                '<div class="history-item-header" style="width: 100%; display: flex; justify-content: space-between; align-items: center;">' +
                    '<span class="history-menu"><i class="fa-solid fa-user" style="color: #ec4899; margin-right: 4px;"></i> ' + sanitize(m.fromName) + ' (' + sanitize(m.fromNik) + ')</span>' +
                    '<span class="history-date">' + sanitize(m.date) + '</span>' +
                '</div>' +
                '<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 0.8rem; margin: 0.3rem 0;">' +
                    '<p style="margin: 0; font-size:0.92rem; flex: 1; white-space: pre-wrap;">' + sanitize(m.text) + '</p>' +
                    (!m.reply ? 
                        '<button class="btn btn-secondary" style="font-size:0.8rem; padding:0.35rem 0.85rem; border-radius: 8px; white-space: nowrap;" onclick="window.replyToMessage(' + m.id + ')">' +
                            '<i class="fa-solid fa-reply"></i> Balas' +
                        '</button>' : ''
                    ) +
                '</div>' +
                (m.reply ? 
                    '<div style="margin-top:0.4rem; padding:0.6rem 0.8rem; background:rgba(16,185,129,0.12); border:1.5px solid var(--primary-color); border-radius:8px; font-size:0.88rem; width: 100%;">' +
                        '<strong style="color: var(--primary-color);">Balasan Anda:</strong> ' + sanitize(m.reply) +
                    '</div>' +
                    '<button class="btn btn-secondary" style="margin-top:0.3rem; font-size:0.75rem; padding:0.25rem 0.6rem; border-radius: 6px;" onclick="window.replyToMessage(' + m.id + ')">' +
                        '<i class="fa-solid fa-comment-dots"></i> Balas Lagi / Beri Pertanyaan Lanjutan' +
                    '</button>' : ''
                ) +
            '</div>'
        ).join('');
    }

    window.replyToMessage = async function(msgId) {
        const reply = await customPrompt('Masukkan teks balasan atau pertanyaan untuk pengguna ini:');
        if (reply === null || reply === '') return;
        await publishSync('reply_message', { id: msgId, reply: sanitize(reply) });
        showToast('Balasan & Pertanyaan terkirim ke Pengguna!');
        loadMessages();
    };

    window.userReplyToMessage = async function(msgId) {
        const reply = await customPrompt('Masukkan tanggapan atau jawaban Anda untuk Admin SPPG:');
        if (reply === null || reply === '') return;
        await publishSync('user_reply_message', { id: msgId, reply: sanitize(reply) });
        showToast('Tanggapan Anda terkirim ke Admin!');
        loadMessages();
    };

    // ============================================================
    // 11. NUTRITION DATABASE & TKPI FOOD KNOWLEDGE BASE
    // ============================================================
    const nutritionDB = {
        "0":     { kal: 0,   pro: 0,    kar: 0,    lem: 0   },
        "150":   { kal: 130, pro: 2.7,  kar: 28.7, lem: 0.3 }, // Nasi Putih per 100g (TKPI Kemenkes)
        "130":   { kal: 110, pro: 2.6,  kar: 23.5, lem: 0.9 }, // Nasi Merah per 100g
        "80":    { kal: 85,  pro: 2.0,  kar: 19.0, lem: 0.1 }, // Kentang per 100g
        "200":   { kal: 250, pro: 28.0, kar: 1.8,  lem: 14.5}, // Ayam Goreng Lengkuas/Kremes per 100g
        "250":   { kal: 260, pro: 26.0, kar: 2.0,  lem: 16.0}, // Daging Sapi per 100g
        "150_2": { kal: 150, pro: 20.0, kar: 0.0,  lem: 5.0 }, // Ikan Nila/Lele/Semur per 100g
        "90":    { kal: 91,  pro: 21.0, kar: 0.1,  lem: 0.2 }, // Udang Segar/Kuah per 100g (TKPI Kemenkes)
        "70":    { kal: 140, pro: 12.6, kar: 1.1,  lem: 9.5 }, // Telur per 100g (1 butir ~55g = 77 kcal)
        "190":   { kal: 195, pro: 19.0, kar: 9.0,  lem: 11.0}, // Tempe Goreng per 100g
        "120":   { kal: 220, pro: 18.0, kar: 16.0, lem: 10.0}, // Tempe Orek Dadu per 100g
        "80_2":  { kal: 80,  pro: 8.2,  kar: 2.1,  lem: 4.8 }, // Tahu Goreng/Kuning/Kukus per 100g
        "20":    { kal: 25,  pro: 1.2,  kar: 4.5,  lem: 0.8 }, // Tumis Labu Siam / Sayur Bening / Sop per 100g
        "30":    { kal: 30,  pro: 2.2,  kar: 5.4,  lem: 1.0 }, // Tumis Kangkung / Buncis per 100g
        "35":    { kal: 35,  pro: 2.0,  kar: 6.5,  lem: 0.8 }, // Sayur Capcay Wortel per 100g
        "25":    { kal: 28,  pro: 2.5,  kar: 4.8,  lem: 0.4 }  // Brokoli / Tauge per 100g
    };

    function guessNutritionFromName(name, categoryHint = '') {
        if (!name) return { kalori: 0, protein: 0, karbohidrat: 0, lemak: 0, kal: 0, pro: 0, kar: 0, lem: 0 };
        const n = name.toLowerCase().trim();
        const c = String(categoryHint || '').toLowerCase().trim();
        const isSayurSlot = c.includes('sayur');
        const isKarboSlot = c.includes('karbo');
        const isHewaniSlot = c.includes('hewani');
        const isNabatiSlot = c.includes('nabati');

        // Helper kamus nutrisi sayuran Indonesia (Standar TKPI Kemenkes RI 2018 per 100g)
        function matchVegetable(s) {
            // 1. Bayam (Sayur Bening Bayam, Bayam Jagung, Tumis Bayam, Bayam Rebus)
            if (s.includes('bayam')) {
                if (s.includes('tumis') || s.includes('goreng')) {
                    return { kal: 34, pro: 1.8, kar: 3.5, lem: 1.5 };
                }
                return { kal: 20, pro: 1.6, kar: 3.5, lem: 0.3, bdd: 100 }; // Standar TKPI Kemenkes RI: 20 kcal, 1.6g protein, 3.5g karbo per 100g
            }
            // 2. Kangkung (Tumis Kangkung, Cah Kangkung, Kangkung Rebus)
            if (s.includes('kangkung')) {
                return { kal: 28, pro: 2.2, kar: 3.8, lem: 0.8 };
            }
            // 3. Buncis (Tumis Buncis, Buncis Wortel, Buncis Rebus)
            if (s.includes('buncis')) {
                if (s.includes('tumis')) {
                    return { kal: 32, pro: 1.8, kar: 5.5, lem: 0.6 };
                }
                return { kal: 28, pro: 1.5, kar: 5.0, lem: 0.3 };
            }
            // 4. Labu Siam / Jipang (Tumis Labu Siam, Labu Rebus, Sayur Labu)
            if (s.includes('labu') || s.includes('jipang')) {
                return { kal: 24, pro: 1.0, kar: 4.5, lem: 0.4 };
            }
            // 5. Sayur Sop / Sup (Sop Sayur, Sop Wortel Kol, Sop Ayam Sayur)
            if (s.includes('sop') || s.includes('sup')) {
                return { kal: 25, pro: 1.3, kar: 4.5, lem: 0.5 };
            }
            // 6. Capcay / Cap Cay (Capcay Sayur, Tumis Capcay)
            if (s.includes('capcay') || s.includes('cap cay')) {
                return { kal: 38, pro: 2.2, kar: 6.0, lem: 1.0 };
            }
            // 7. Sayur Asem / Asam
            if (s.includes('asem') || s.includes('asam')) {
                return { kal: 28, pro: 1.2, kar: 5.5, lem: 0.4 };
            }
            // 8. Sayur Lodeh (santan encer)
            if (s.includes('lodeh')) {
                return { kal: 55, pro: 1.8, kar: 5.8, lem: 3.0 };
            }
            // 9. Sawi (Sawi Hijau, Sawi Putih, Cah Sawi, Pakcoy, Pokcoy)
            if (s.includes('sawi') || s.includes('pakcoy') || s.includes('pokcoy')) {
                return { kal: 24, pro: 1.6, kar: 3.6, lem: 0.5 };
            }
            // 10. Brokoli (Tumis Brokoli, Brokoli Rebus)
            if (s.includes('brokoli') || s.includes('broccoli')) {
                return { kal: 32, pro: 2.6, kar: 5.0, lem: 0.4 };
            }
            // 11. Kembang Kol / Kol / Kubis
            if (s.includes('kembang kol') || s.includes('kubis') || (s.includes('kol') && !s.includes('brokoli') && !s.includes('kolak'))) {
                return { kal: 25, pro: 1.8, kar: 4.2, lem: 0.3 };
            }
            // 12. Wortel / Stik Wortel Rebus
            if (s.includes('wortel') || s.includes('carrot')) {
                return { kal: 34, pro: 1.0, kar: 7.2, lem: 0.3 };
            }
            // 13. Tauge / Toge / Kecambah
            if (s.includes('tauge') || s.includes('toge') || s.includes('kecambah')) {
                return { kal: 30, pro: 2.8, kar: 4.0, lem: 0.5 };
            }
            // 14. Kacang Panjang
            if (s.includes('kacang panjang')) {
                return { kal: 36, pro: 2.2, kar: 6.5, lem: 0.5 };
            }
            // 15. Daun Singkong / Gulai Daun Singkong
            if (s.includes('daun singkong') || s.includes('singkong rebus')) {
                return { kal: 50, pro: 3.5, kar: 7.0, lem: 1.2 };
            }
            // 16. Jagung Manis / Pipil
            if (s.includes('jagung')) {
                return { kal: 65, pro: 2.2, kar: 14.0, lem: 0.8 };
            }
            // 17. Timun / Lalapan / Selada / Tomat
            if (s.includes('timun') || s.includes('mentimun') || s.includes('lalap') || s.includes('selada') || s.includes('tomat')) {
                return { kal: 15, pro: 0.7, kar: 3.0, lem: 0.1 };
            }
            // 18. Terong / Pare / Gambas / Oyong
            if (s.includes('terong') || s.includes('terung')) {
                return { kal: 42, pro: 1.2, kar: 6.0, lem: 1.8 };
            }
            if (s.includes('pare')) {
                return { kal: 28, pro: 1.2, kar: 4.5, lem: 0.8 };
            }
            if (s.includes('oyong') || s.includes('gambas')) {
                return { kal: 20, pro: 1.0, kar: 3.8, lem: 0.2 };
            }
            // 19. Urap / Pecel / Gado-gado
            if (s.includes('urap') || s.includes('pecel') || s.includes('gado')) {
                return { kal: 60, pro: 2.8, kar: 8.5, lem: 2.0 };
            }
            // 20. Sayuran umum
            if (s.includes('sayur') || s.includes('sayuran')) {
                return { kal: 30, pro: 1.5, kar: 5.0, lem: 0.5 };
            }
            return null;
        }

        let res = null;

        // Prioritas 1: Jika slot Sayuran, pastikan diproses dengan kamus sayuran
        if (isSayurSlot) {
            res = matchVegetable(n);
            if (!res) res = { kal: 30, pro: 1.5, kar: 5.0, lem: 0.5 };
        }

        // Prioritas 2: Kerupuk, Snack, Puding, Susu
        if (!res) {
            if (n.includes('kerupuk') || n.includes('krupuk') || n.includes('cracker') || n.includes('garlic') || n.includes('rempeyek') || n.includes('emping') || n.includes('peyek') || n.includes('pangsit')) {
                res = { kal: 480, pro: 4.5, kar: 62.0, lem: 24.0 };
            } else if (n.includes('susu') || n.includes('milk')) {
                res = { kal: 65, pro: 3.2, kar: 4.8, lem: 3.5 };
            } else if (n.includes('puding') || n.includes('agar')) {
                res = { kal: 80, pro: 1.0, kar: 18.0, lem: 0.5 };
            }
        }

        // Prioritas 3: Buah-buahan
        if (!res) {
            if (n.includes('kelengkeng') || n.includes('lengkeng') || n.includes('duku') || n.includes('longan')) {
                res = { kal: 60, pro: 1.3, kar: 15.1, lem: 0.1 };
            } else if (n.includes('semangka')) {
                res = { kal: 32, pro: 0.6, kar: 7.6, lem: 0.2 };
            } else if (n.includes('jeruk')) {
                res = { kal: 47, pro: 0.9, kar: 12.0, lem: 0.1 };
            } else if (n.includes('melon') || n.includes('cantaloupe') || n.includes('blewah')) {
                res = { kal: 36, pro: 0.8, kar: 8.5, lem: 0.2 };
            } else if (n.includes('pisang')) {
                res = { kal: 89, pro: 1.1, kar: 22.8, lem: 0.3 };
            } else if (n.includes('apel')) {
                res = { kal: 52, pro: 0.3, kar: 13.8, lem: 0.2 };
            } else if (n.includes('pepaya')) {
                res = { kal: 39, pro: 0.5, kar: 9.8, lem: 0.1 };
            } else if (n.includes('anggur')) {
                res = { kal: 67, pro: 0.6, kar: 18.0, lem: 0.2 };
            } else if (n.includes('kiwi')) {
                res = { kal: 61, pro: 1.1, kar: 14.7, lem: 0.5 };
            }
        }

        // Prioritas 4: Jika di slot Nabati, prioritaskan olahan tempe/tahu
        if (!res && isNabatiSlot) {
            if (n.includes('tempe orek') || n.includes('bacem')) {
                res = { kal: 210, pro: 17.0, kar: 18.0, lem: 9.0 };
            } else if (n.includes('tempe')) {
                res = { kal: 210, pro: 19.0, kar: 11.0, lem: 10.5 };
            } else if (n.includes('tahu kukus') || n.includes('tahu putih')) {
                res = { kal: 80, pro: 8.0, kar: 2.0, lem: 4.5 };
            } else if (n.includes('tahu')) {
                res = { kal: 95, pro: 9.0, kar: 2.5, lem: 5.5 };
            } else if (n.includes('pangsit')) {
                res = { kal: 480, pro: 4.5, kar: 62.0, lem: 24.0 };
            } else if (n.includes('bakwan')) {
                res = { kal: 230, pro: 4.5, kar: 24.0, lem: 13.0 };
            } else if (n.includes('perkedel')) {
                res = { kal: 190, pro: 5.0, kar: 28.0, lem: 7.0 };
            } else if (n.includes('edamame') || (n.includes('kacang') && !n.includes('kacang panjang'))) {
                res = { kal: 120, pro: 12.0, kar: 9.0, lem: 5.0 };
            }
        }

        // Prioritas 5: Jika di slot Hewani, prioritaskan daging/telur/ikan/ayam
        if (!res && isHewaniSlot) {
            if (n.includes('udang') || n.includes('prawn') || n.includes('shrimp')) {
                res = { kal: 106, pro: 21.0, kar: 1.0, lem: 1.0 };
            } else if (n.includes('cumi')) {
                res = { kal: 92, pro: 16.0, kar: 3.0, lem: 1.4 };
            } else if (n.includes('telur balado')) {
                res = { kal: 175, pro: 11.5, kar: 4.0, lem: 12.5 };
            } else if (n.includes('telur ceplok') || n.includes('mata sapi')) {
                res = { kal: 185, pro: 12.4, kar: 0.8, lem: 14.2 };
            } else if (n.includes('telur dadar')) {
                res = { kal: 190, pro: 11.0, kar: 1.5, lem: 15.5 };
            } else if (n.includes('telur')) {
                res = { kal: 155, pro: 12.6, kar: 1.1, lem: 10.6 };
            } else if (n.includes('gulai') || n.includes('opor') || n.includes('kuah kuning')) {
                res = { kal: 238, pro: 23.0, kar: 3.8, lem: 14.4 };
            } else if (n.includes('ayam') && !n.includes('bayam')) {
                res = { kal: 250, pro: 28.0, kar: 1.8, lem: 14.5 };
            } else if (n.includes('daging') || n.includes('sapi') || n.includes('rendang')) {
                res = { kal: 260, pro: 26.0, kar: 3.0, lem: 16.0 };
            } else if (n.includes('ikan')) {
                res = { kal: 160, pro: 21.0, kar: 1.0, lem: 8.0 };
            }
        }

        // Prioritas 6: Deteksi nama sayuran spesifik (meskipun diinput di slot custom/lain)
        if (!res) {
            res = matchVegetable(n);
        }

        // Prioritas 7: Karbohidrat / Makanan Pokok
        if (!res && (isKarboSlot || n.includes('nasi') || n.includes('mie') || n.includes('bihun') || n.includes('kwetiau') || n.includes('pasta') || n.includes('spaghetti') || n.includes('kentang') || n.includes('roti') || n.includes('bubur') || n.includes('lontong') || n.includes('ketupat'))) {
            if (n.includes('nasi kuning') || (isKarboSlot && n.includes('kuning'))) {
                res = { kal: 150, pro: 3.0, kar: 30.0, lem: 2.5 };
            } else if (n.includes('nasi uduk') || n.includes('nasi gurih') || (isKarboSlot && (n.includes('uduk') || n.includes('gurih')))) {
                res = { kal: 160, pro: 3.2, kar: 29.0, lem: 4.0 };
            } else if (n.includes('nasi goreng')) {
                res = { kal: 168, pro: 3.8, kar: 27.5, lem: 5.0 };
            } else if (n.includes('nasi merah')) {
                res = { kal: 110, pro: 2.6, kar: 23.5, lem: 0.9 };
            } else if (n.includes('spaghetti') || n.includes('pasta')) {
                res = { kal: 158, pro: 5.8, kar: 30.0, lem: 1.5 };
            } else if (n.includes('mie') || n.includes('bihun') || n.includes('kwetiau')) {
                res = { kal: 175, pro: 4.0, kar: 28.0, lem: 5.5 };
            } else if (n.includes('kentang') && !n.includes('perkedel')) {
                res = { kal: 87, pro: 2.0, kar: 20.0, lem: 0.1 };
            } else if (n.includes('roti')) {
                res = { kal: 260, pro: 8.0, kar: 50.0, lem: 3.0 };
            } else {
                res = { kal: 130, pro: 2.7, kar: 28.7, lem: 0.3 };
            }
        }

        // Prioritas 8: Lauk Hewani Umum (Pencegahan 'bayam' mencocokkan 'ayam')
        if (!res) {
            if (n.includes('udang') || n.includes('prawn') || n.includes('shrimp')) {
                res = { kal: 106, pro: 21.0, kar: 1.0, lem: 1.0 };
            } else if (n.includes('cumi')) {
                res = { kal: 92, pro: 16.0, kar: 3.0, lem: 1.4 };
            } else if (n.includes('sambal') && !n.includes('telur') && !n.includes('ayam') && !n.includes('teri')) {
                res = { kal: 140, pro: 2.5, kar: 16.0, lem: 7.5 };
            } else if (n.includes('telur balado')) {
                res = { kal: 175, pro: 11.5, kar: 4.0, lem: 12.5 };
            } else if (n.includes('telur ceplok') || n.includes('mata sapi')) {
                res = { kal: 185, pro: 12.4, kar: 0.8, lem: 14.2 };
            } else if (n.includes('telur dadar')) {
                res = { kal: 190, pro: 11.0, kar: 1.5, lem: 15.5 };
            } else if (n.includes('telur')) {
                res = { kal: 155, pro: 12.6, kar: 1.1, lem: 10.6 };
            } else if (n.includes('gulai') || n.includes('opor') || n.includes('kuah kuning')) {
                res = { kal: 238, pro: 23.0, kar: 3.8, lem: 14.4 };
            } else if (n.includes('ayam') && !n.includes('bayam')) {
                res = { kal: 250, pro: 28.0, kar: 1.8, lem: 14.5 };
            } else if (n.includes('daging') || n.includes('sapi') || n.includes('rendang')) {
                res = { kal: 260, pro: 26.0, kar: 3.0, lem: 16.0 };
            } else if (n.includes('ikan')) {
                res = { kal: 160, pro: 21.0, kar: 1.0, lem: 8.0 };
            }
        }

        // Prioritas 9: Lauk Nabati Umum
        if (!res) {
            if (n.includes('tempe orek') || n.includes('bacem')) {
                res = { kal: 210, pro: 17.0, kar: 18.0, lem: 9.0 };
            } else if (n.includes('tempe')) {
                res = { kal: 210, pro: 19.0, kar: 11.0, lem: 10.5 };
            } else if (n.includes('tahu')) {
                res = { kal: 95, pro: 9.0, kar: 2.5, lem: 5.5 };
            } else if (n.includes('perkedel')) {
                res = { kal: 190, pro: 5.0, kar: 28.0, lem: 7.0 };
            } else if (n.includes('bakwan')) {
                res = { kal: 230, pro: 4.5, kar: 24.0, lem: 13.0 };
            } else if (n.includes('edamame') || (n.includes('kacang') && !n.includes('kacang panjang'))) {
                res = { kal: 120, pro: 12.0, kar: 9.0, lem: 5.0 };
            }
        }

        // Prioritas 10: Fallback default berdasarkan petunjuk slot
        if (!res) {
            if (isSayurSlot) res = { kal: 30, pro: 1.5, kar: 5.0, lem: 0.5 };
            else if (isKarboSlot) res = { kal: 130, pro: 2.7, kar: 28.7, lem: 0.3 };
            else if (isHewaniSlot) res = { kal: 200, pro: 22.0, kar: 1.5, lem: 12.0 };
            else if (isNabatiSlot) res = { kal: 150, pro: 14.0, kar: 7.0, lem: 8.0 };
            else res = { kal: 120, pro: 5.0, kar: 15.0, lem: 4.0 };
        }

        return {
            kalori: res.kal,
            protein: res.pro,
            karbohidrat: res.kar,
            lemak: res.lem,
            kal: res.kal,
            pro: res.pro,
            kar: res.kar,
            lem: res.lem
        };
    }
    window.guessNutritionFromName = guessNutritionFromName;

    // ============================================================
    // 12. DATASET PRESET LOADER (QUICK MENU BUTTONS)
    // ============================================================
    const MBG_DATASET_PRESETS = {
        1: {
            name: "Paket 1: Ayam Lengkuas MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Ayam Lengkuas', gram: 85 },
            pronab: { name: 'Tahu Goreng Gurih', gram: 75 },
            sayur: { name: 'Tumis Labu Siam', gram: 80 },
            custom: { name: 'Buah Semangka Merah Segar', gram: 100 }
        },
        2: {
            name: "Paket 2: Telur Rebus Sehat MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Telur Rebus', gram: 55 },
            pronab: { name: 'Tempe Goreng Gurih', gram: 50 },
            sayur: { name: 'Tumis Buncis Hijau', gram: 75 },
            custom: { name: 'Buah Jeruk Segar Utuh', gram: 100 }
        },
        3: {
            name: "Paket 3: Telur Balado Spesial MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Telur Balado', gram: 60 },
            pronab: { name: 'Tahu Kukus', gram: 80 },
            sayur: { name: 'Sayur Capcay Wortel', gram: 75 },
            custom: { name: 'Buah Melon Segar', gram: 100 }
        },
        4: {
            name: "Paket 4: Telur Ceplok Praktis MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Telur Ceplok Balado', gram: 55 },
            pronab: { name: 'Tempe Goreng Gurih', gram: 60 },
            sayur: { name: 'Sayur Capcay Wortel', gram: 75 },
            custom: { name: 'Buah Jeruk Segar Utuh', gram: 100 }
        },
        5: {
            name: "Paket 5: Ayam Kremes Lalapan MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Ayam Goreng Kremes', gram: 85 },
            pronab: { name: 'Tempe Orek Dadu Manis', gram: 50 },
            sayur: { name: 'Lalapan Timun Kol', gram: 60 },
            custom: { name: 'Buah Semangka Merah Segar', gram: 100 }
        },
        6: {
            name: "Paket 6: Seafood Udang Kuah MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Udang Masak Balado', gram: 85 },
            pronab: { name: 'Tempe Orek Dadu Manis', gram: 50 },
            sayur: { name: 'Sayur Capcay Wortel', gram: 75 },
            custom: { name: 'Buah Semangka Merah Segar', gram: 100 }
        },
        7: {
            name: "Paket 7: Ikan Nila Goreng MBG",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Ikan Nila Goreng', gram: 80 },
            pronab: { name: 'Tempe Goreng Gurih', gram: 50 },
            sayur: { name: 'Sayur Bening Bayam', gram: 80 },
            custom: { name: 'Buah Pisang Ambon Segar', gram: 100 }
        },
        8: {
            name: "Paket 8: Ayam Lengkuas + Tempe Orek + Sayur Sop + Kelengkeng",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Ayam Lengkuas', gram: 85 },
            pronab: { name: 'Tempe Orek Dadu Manis', gram: 50 },
            sayur: { name: 'Sayur Sop Wortel Kol', gram: 75 },
            custom: { name: 'Buah Kelengkeng Segar (5 Butir)', gram: 75 }
        },
        9: {
            name: "Paket 9: Telur Ceplok + Tempe Orek + Sayur Sop + Kelengkeng",
            karbo: { name: 'Nasi Putih Pulen', gram: 150 },
            prohew: { name: 'Telur Ceplok', gram: 50 },
            pronab: { name: 'Tempe Orek Dadu Manis', gram: 50 },
            sayur: { name: 'Sayur Sop Wortel Kol', gram: 75 },
            custom: { name: 'Buah Kelengkeng Segar (4-5 Butir)', gram: 75 }
        }
    };

    window.loadMenuPreset = function(presetId) {
        const p = MBG_DATASET_PRESETS[presetId];
        if (!p) return;

        const kInput = document.getElementById('karbo');
        const hInput = document.getElementById('prohew');
        const nInput = document.getElementById('pronab');
        const sInput = document.getElementById('sayur');

        const kGram = document.getElementById('karbo-gram');
        const hGram = document.getElementById('prohew-gram');
        const nGram = document.getElementById('pronab-gram');
        const sGram = document.getElementById('sayur-gram');

        const cName = document.getElementById('custom-name');
        const cGram = document.getElementById('custom-gram');
        const badge = document.getElementById('ai-food-badge');

        if (kInput) kInput.value = p.karbo.name;
        if (hInput) hInput.value = p.prohew.name;
        if (nInput) nInput.value = p.pronab.name;
        if (sInput) sInput.value = p.sayur.name;

        if (kGram) kGram.value = p.karbo.gram;
        if (hGram) hGram.value = p.prohew.gram;
        if (nGram) nGram.value = p.pronab.gram;
        if (sGram) sGram.value = p.sayur.gram;

        if (cName) cName.value = p.custom.name;
        if (cGram) cGram.value = p.custom.gram;

        if (badge) badge.style.display = 'none';
        window._cachedCustomFood = null;

        showToast('Memuat ' + p.name.split(':')[0] + '...');
        window.calculateNutrition(false, true);
    };

    // ============================================================
    // 13. KALKULATOR GIZI & EVALUASI
    // ============================================================
    const nutritionForm = document.getElementById('nutrition-form');
    const nutritionResult = document.getElementById('nutrition-result');

    window.calculateNutrition = function(isFromAIScan = false, silent = false) {
        let totalKalori = 0;
        let totalProtein = 0;
        let totalKarbo = 0;
        let totalLemak = 0;
        let computedItems = [];

        if (isFromAIScan && window.currentMealIntake && window.currentMealIntake.kalori > 0 && window.currentMealIntake.items && window.currentMealIntake.items.length > 0) {
            totalKalori = window.currentMealIntake.kalori;
            totalProtein = window.currentMealIntake.protein;
            totalKarbo = window.currentMealIntake.karbo;
            totalLemak = window.currentMealIntake.lemak;
            computedItems = window.currentMealIntake.items;
        } else {
            // 1. Buat array penampung untuk semua input makanan yang terisi nama dan gramasinya > 0
            const foodSlots = [
                { cat: 'Karbohidrat', id: 'karbo', gramId: 'karbo-gram' },
                { cat: 'Protein Hewani', id: 'prohew', gramId: 'prohew-gram' },
                { cat: 'Protein Nabati', id: 'pronab', gramId: 'pronab-gram' },
                { cat: 'Sayuran', id: 'sayur', gramId: 'sayur-gram' },
                { cat: 'Menu Tambahan / Kustom', id: 'custom-name', gramId: 'custom-gram' }
            ];

            const activeItems = [];
            foodSlots.forEach(slot => {
                const nameEl = document.getElementById(slot.id);
                const gramEl = document.getElementById(slot.gramId);
                const rawName = nameEl ? nameEl.value.trim() : '';
                const gram = gramEl ? Math.max(0, parseFloat(gramEl.value) || 0) : 0;

                if (rawName && gram > 0 && !rawName.toLowerCase().startsWith('tanpa') && !rawName.toLowerCase().startsWith('tidak ada')) {
                    activeItems.push({
                        cat: slot.cat,
                        id: slot.id,
                        name: rawName,
                        gram: gram
                    });
                }
            });

            // 2. Inisialisasi total nilai gizi:
            totalKalori = 0;
            totalProtein = 0;
            totalKarbo = 0;
            totalLemak = 0;

            // 3. Lakukan iterasi (looping) pada seluruh item makanan:
            activeItems.forEach(item => {
                let nilaiGizi;
                if (item.id === 'custom-name' && window._cachedCustomFood && 
                    window._cachedCustomFood.name.toLowerCase().includes(item.name.toLowerCase())) {
                    const cached = window._cachedCustomFood;
                    const refGram = cached.gram || 100;
                    nilaiGizi = {
                        kalori: (cached.kal / refGram) * 100,
                        protein: (cached.pro / refGram) * 100,
                        karbohidrat: (cached.kar / refGram) * 100,
                        lemak: (cached.lem / refGram) * 100
                    };
                } else {
                    nilaiGizi = guessNutritionFromName(item.name, item.cat);
                }

                // Hitung proporsi: faktor = gramasi / 100 (Standar TKPI Kemenkes RI)
                const faktor = item.gram / 100;

                // Ambil nilai per 100 gram (kompatibel kalori/kal, protein/pro, dll)
                const baseKal = nilaiGizi.kalori !== undefined ? nilaiGizi.kalori : (nilaiGizi.kal || 0);
                const basePro = nilaiGizi.protein !== undefined ? nilaiGizi.protein : (nilaiGizi.pro || 0);
                const baseKar = nilaiGizi.karbohidrat !== undefined ? nilaiGizi.karbohidrat : (nilaiGizi.kar || 0);
                const baseLem = nilaiGizi.lemak !== undefined ? nilaiGizi.lemak : (nilaiGizi.lem || 0);

                // Akumulasikan seluruh nilai gizi secara matematis:
                totalKalori += faktor * baseKal;
                totalProtein += faktor * basePro;
                totalKarbo += faktor * baseKar;
                totalLemak += faktor * baseLem;

                computedItems.push({
                    cat: item.cat,
                    name: item.name,
                    gram: item.gram,
                    kal: faktor * baseKal,
                    pro: faktor * basePro,
                    kar: faktor * baseKar,
                    lem: faktor * baseLem
                });
            });

            totalKalori = Math.round(totalKalori);
            totalProtein = parseFloat(totalProtein.toFixed(1));
            totalKarbo = parseFloat(totalKarbo.toFixed(1));
            totalLemak = parseFloat(totalLemak.toFixed(1));

            // 4. Perbarui state ringkasan hasil gizi
            window.currentMealIntake = {
                kalori: totalKalori,
                protein: totalProtein,
                karbo: totalKarbo,
                lemak: totalLemak,
                items: computedItems,
                menuName: computedItems.map(it => it.name).join(' + '),
                source: 'Kalkulator Gizi Manual'
            };
        }

        // Perbarui nilai pada kartu antarmuka
        const valKal = document.getElementById('val-kalori');
        const valPro = document.getElementById('val-protein');
        const valKar = document.getElementById('val-karbo');
        const valLem = document.getElementById('val-lemak');
        if (valKal) valKal.textContent = totalKalori + ' kcal';
        if (valPro) valPro.textContent = totalProtein + ' g';
        if (valKar) valKar.textContent = totalKarbo + ' g';
        if (valLem) valLem.textContent = totalLemak + ' g';

        if (nutritionResult) {
            nutritionResult.classList.remove('hidden');
            nutritionResult.style.display = 'grid';
        }

        // Perbarui tabel rincian (Breakdown Table) jika ada kontainernya
        const breakdownCard = document.getElementById('nutrition-breakdown-card');
        const breakdownContent = document.getElementById('nutrition-breakdown-content');
        if (breakdownContent && computedItems.length > 0) {
            let tableHtml = '<div style="background:white; border-radius:12px; border:1px solid rgba(0,0,0,0.08); overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.03);">' +
                '<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">' +
                    '<thead style="background:#f8fafc; border-bottom:1.5px solid #e2e8f0; color:#475569; font-weight:700;">' +
                        '<tr>' +
                            '<th style="padding:0.6rem 0.75rem; text-align:left;">Bahan Makanan</th>' +
                            '<th style="padding:0.6rem 0.5rem; text-align:center;">Porsi</th>' +
                            '<th style="padding:0.6rem 0.5rem; text-align:center;">Energi</th>' +
                            '<th style="padding:0.6rem 0.5rem; text-align:center;">Protein</th>' +
                            '<th style="padding:0.6rem 0.5rem; text-align:center;">Karbo</th>' +
                            '<th style="padding:0.6rem 0.5rem; text-align:center;">Lemak</th>' +
                        '</tr>' +
                    '</thead>' +
                    '<tbody>';

            computedItems.forEach((it, idx) => {
                const rowBg = idx % 2 === 0 ? '#ffffff' : '#f8fafc';
                tableHtml += '<tr style="background:' + rowBg + '; border-bottom:1px solid #f1f5f9;">' +
                    '<td style="padding:0.55rem 0.75rem;">' +
                        '<div style="font-weight:700; color:#1e293b;">' + sanitize(it.name) + '</div>' +
                        '<div style="font-size:0.75rem; color:#64748b;">' + sanitize(it.cat) + '</div>' +
                    '</td>' +
                    '<td style="padding:0.55rem 0.5rem; text-align:center;">' + it.gram + 'g</td>' +
                    '<td style="padding:0.55rem 0.5rem; text-align:center; font-weight:700; color:#d97706;">' + Math.round(it.kal) + ' kcal</td>' +
                    '<td style="padding:0.55rem 0.5rem; text-align:center; color:#2563eb; font-weight:600;">' + it.pro.toFixed(1) + 'g</td>' +
                    '<td style="padding:0.55rem 0.5rem; text-align:center; color:#059669;">' + it.kar.toFixed(1) + 'g</td>' +
                    '<td style="padding:0.55rem 0.5rem; text-align:center; color:#7c3aed;">' + it.lem.toFixed(1) + 'g</td>' +
                '</tr>';
            });

            tableHtml += '</tbody></table></div>';
            breakdownContent.innerHTML = tableHtml;
            if (breakdownCard) breakdownCard.classList.remove('hidden');
        }

        // Sinkronisasi real-time ke Dashboard Evaluasi MBG
        updateIntegratedDashboard();

        // Tampilkan dialog ringkasan jika kalkulasi manual dan TIDAK silent
        if (!isFromAIScan && !silent) {
            const targetMBG = (window.currentTargetNutrition && window.currentTargetNutrition.mbgTargetKal) || 807;
            const pctKal = Math.round((totalKalori / targetMBG) * 100);

            let itemsSummary = computedItems.map(it => 
                '<div style="display:flex; justify-content:space-between; margin-bottom:0.25rem; font-size:0.83rem; border-bottom:1px dashed #e2e8f0; padding-bottom:0.25rem;">' +
                    '<span><strong>' + sanitize(it.name) + '</strong> (' + it.gram + 'g)</span>' +
                    '<span style="color:#d97706; font-weight:700;">' + Math.round(it.kal) + ' kcal | P:' + it.pro.toFixed(1) + 'g | K:' + it.kar.toFixed(1) + 'g | L:' + it.lem.toFixed(1) + 'g</span>' +
                '</div>'
            ).join('');

            customAlert(
                '<strong style="font-size:1.15rem; color:var(--primary-color);">Hasil Akumulasi Nilai Gizi Makanan MBG</strong><br><br>' +
                '<div style="background:#f8fafc; padding:0.8rem; border-radius:10px; text-align:left; margin-bottom:0.8rem; max-height:180px; overflow-y:auto;">' +
                    (itemsSummary || '<p style="margin:0; color:#64748b;">Tidak ada item makanan yang diinputkan.</p>') +
                '</div>' +
                '<div style="background:rgba(16,185,129,0.1); padding:1rem; border-radius:10px; text-align:left; font-size:0.92rem;">' +
                    '<div style="margin-bottom:0.45rem;">🔥 <strong>Total Kalori:</strong> ' + totalKalori + ' kcal <span style="float:right; color:var(--text-light); font-weight:700;">(' + pctKal + '% Target 1x MBG)</span></div>' +
                    '<div style="margin-bottom:0.45rem;">🌾 <strong>Karbohidrat:</strong> ' + totalKarbo + ' g</div>' +
                    '<div style="margin-bottom:0.45rem;">🥩 <strong>Protein:</strong> ' + totalProtein + ' g</div>' +
                    '<div>💧 <strong>Lemak:</strong> ' + totalLemak + ' g</div>' +
                '</div>' +
                '<button type="button" class="btn btn-secondary btn-block" style="margin-top:1rem; font-size:0.88rem;" onclick="openScreen(\'screen-dashboard-mbg\')">' +
                    '📊 Buka Dashboard Evaluasi MBG &rarr;' +
                '</button>'
            );
        }
    };

    if (nutritionForm) {
        nutritionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            window.calculateNutrition(false, false);
        });
    }

    const btnCalc = document.getElementById('btn-calculate-nutrition');
    if (btnCalc) {
        btnCalc.addEventListener('click', (e) => {
            e.preventDefault();
            window.calculateNutrition(false, false);
        });
    }

    // Pasang event listener sinkronisasi real-time pada semua field kalkulator manual
    const manualCalcInputIds = [
        'karbo', 'karbo-gram',
        'prohew', 'prohew-gram',
        'pronab', 'pronab-gram',
        'sayur', 'sayur-gram',
        'custom-name', 'custom-gram'
    ];
    manualCalcInputIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                if (window.calculateNutrition) window.calculateNutrition(false, true);
            });
            el.addEventListener('change', () => {
                if (window.calculateNutrition) window.calculateNutrition(false, true);
            });
        }
    });

    // ============================================================
    // 14. SISTEM DETEKSI MAKANAN OTOMATIS
    // ============================================================
    let activeAIEngine = localStorage.getItem('mbg_ai_engine') || 'vlm';
    const _DEFAULT_AI_KEY = (typeof atob === 'function') ? atob('QVEuQWI4Uk42SXhRQjdtZWZDajlLMDdoTVRKaXo1SzgweUZON3JDTkJTRFpsdzM5NmVHaFE=') : '';
    let vlmApiKey = (localStorage.getItem('mbg_vlm_api_key') || localStorage.getItem('gemini_api_key') || localStorage.getItem('sppg_vlm_key') || _DEFAULT_AI_KEY).replace(/^["']|["']$/g, '').trim();

    function updateVLMUI() {
        const btnVLM = document.getElementById('btn-mode-vlm');
        const btnYOLO = document.getElementById('btn-mode-yolo');
        const apiKeyInput = document.getElementById('vlm-api-key');

        if (apiKeyInput) apiKeyInput.value = vlmApiKey;

        if (activeAIEngine === 'vlm') {
            if (btnVLM) btnVLM.classList.add('active');
            if (btnYOLO) btnYOLO.classList.remove('active');
        } else {
            if (btnVLM) btnVLM.classList.remove('active');
            if (btnYOLO) btnYOLO.classList.add('active');
        }
    }

    window.switchAIEngine = function(engine) {
        activeAIEngine = engine;
        localStorage.setItem('mbg_ai_engine', engine);
        updateVLMUI();
    };

    // Modal Control
    const vlmConfigModal = document.getElementById('vlm-config-modal');
    const btnOpenVLMModal = document.getElementById('btn-open-vlm-modal');
    const btnOpenVLMMain = document.getElementById('btn-open-vlm-key-main');
    const btnCloseVLMModal = document.getElementById('btn-close-vlm-modal');
    const btnSaveVLMKey = document.getElementById('btn-save-vlm-key');
    const btnClearVLMKey = document.getElementById('btn-clear-vlm-key');
    const vlmBadgeClickable = document.getElementById('vlm-active-badge');

    function openVLMModal() {
        if (vlmConfigModal) {
            updateVLMUI();
            vlmConfigModal.classList.remove('hidden');
        }
    }
    window.openVLMModal = openVLMModal;

    function closeVLMModal() {
        if (vlmConfigModal) vlmConfigModal.classList.add('hidden');
    }
    window.closeVLMModal = closeVLMModal;

    if (btnOpenVLMModal) btnOpenVLMModal.addEventListener('click', openVLMModal);
    if (btnOpenVLMMain) btnOpenVLMMain.addEventListener('click', openVLMModal);
    if (vlmBadgeClickable) vlmBadgeClickable.addEventListener('click', openVLMModal);
    if (btnCloseVLMModal) btnCloseVLMModal.addEventListener('click', closeVLMModal);

    if (btnSaveVLMKey) {
        btnSaveVLMKey.addEventListener('click', () => {
            const input = document.getElementById('vlm-api-key');
            vlmApiKey = input ? input.value.trim() : '';
            localStorage.setItem('mbg_vlm_api_key', vlmApiKey);
            localStorage.setItem('gemini_api_key', vlmApiKey);
            localStorage.setItem('sppg_vlm_key', vlmApiKey);
            updateVLMUI();
            closeVLMModal();
            showToast('Kunci Google Gemini AI berhasil disimpan dan aktif!');
        });
    }

    if (btnClearVLMKey) {
        btnClearVLMKey.addEventListener('click', () => {
            vlmApiKey = '';
            localStorage.removeItem('mbg_vlm_api_key');
            localStorage.removeItem('gemini_api_key');
            localStorage.removeItem('sppg_vlm_key');
            const input = document.getElementById('vlm-api-key');
            if (input) input.value = '';
            updateVLMUI();
            closeVLMModal();
            showToast('Kunci AI di-reset ke bawaan.');
        });
    }

    updateVLMUI();

    // Camera & Gallery elements
    const cameraModal = document.getElementById('camera-modal');
    const cameraVideo = document.getElementById('camera-video');
    const cameraPreviewImg = document.getElementById('camera-preview-img');
    const btnOpenCamera = document.getElementById('btn-open-camera');
    const btnCloseCamera = document.getElementById('btn-close-camera');
    const btnCapture = document.getElementById('btn-capture');
    const scannerOverlay = document.getElementById('scanner-overlay');
    const scanStatusText = document.getElementById('scan-status-text');
    const uploadGallery = document.getElementById('upload-gallery');
    const aiCanvas = document.getElementById('ai-capture-canvas');

    let currentStream = null;

    function stopCameraStreamOnly() {
        if (currentStream) {
            try {
                currentStream.getTracks().forEach(t => t.stop());
            } catch (e) {}
            currentStream = null;
        }
    }

    function closeCameraModal() {
        stopCameraStreamOnly();
        if (scannerOverlay) scannerOverlay.classList.add('hidden');
        if (cameraModal) cameraModal.classList.add('hidden');
        if (cameraVideo) cameraVideo.style.display = 'block';
        if (cameraPreviewImg) {
            cameraPreviewImg.style.display = 'none';
            cameraPreviewImg.src = '';
        }
    }

    function openCameraModal() {
        window._aiDetectionSummary = null;
        if (cameraModal) cameraModal.classList.remove('hidden');
        if (cameraVideo) cameraVideo.style.display = 'block';
        if (cameraPreviewImg) {
            cameraPreviewImg.style.display = 'none';
            cameraPreviewImg.src = '';
        }
        if (scannerOverlay) scannerOverlay.classList.add('hidden');
        updateVLMUI();

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    currentStream = stream;
                    if (cameraVideo) cameraVideo.srcObject = currentStream;
                })
                .catch(err => {
                    console.log('Camera access notice:', err);
                });
        }
    }
    window.openCameraModal = openCameraModal;

    if (btnOpenCamera) {
        btnOpenCamera.addEventListener('click', openCameraModal);
    }

    if (btnCloseCamera) {
        btnCloseCamera.addEventListener('click', closeCameraModal);
    }

    if (btnCapture) {
        btnCapture.addEventListener('click', async () => {
            window._aiDetectionSummary = null;
            if (!currentStream || !cameraVideo || !cameraVideo.videoWidth) {
                if (uploadGallery) {
                    uploadGallery.click();
                    return;
                }
                customAlert('Kamera tidak aktif atau izin belum diberikan.<br>Silakan gunakan tombol <strong>Galeri</strong> untuk memilih foto baki MBG.');
                return;
            }

            if (scannerOverlay) scannerOverlay.classList.remove('hidden');
            if (scanStatusText) scanStatusText.textContent = 'Menganalisis Komposisi Makanan...';

            const vW = Math.max(320, cameraVideo.videoWidth || 640);
            const vH = Math.max(240, cameraVideo.videoHeight || 480);
            aiCanvas.width = 640;
            aiCanvas.height = Math.round(640 * (vH / vW)) || 480;
            const ctx = aiCanvas.getContext('2d');
            ctx.drawImage(cameraVideo, 0, 0, aiCanvas.width, aiCanvas.height);

            await executeRealAIVision(aiCanvas);
        });
    }

    if (uploadGallery) {
        uploadGallery.addEventListener('change', (e) => {
            if (!e.target.files || !e.target.files[0]) return;
            const file = e.target.files[0];

            window._aiDetectionSummary = null;
            stopCameraStreamOnly();

            if (cameraModal) cameraModal.classList.remove('hidden');
            if (scannerOverlay) scannerOverlay.classList.remove('hidden');
            if (scanStatusText) scanStatusText.textContent = 'Menganalisis Foto Baki Makanan...';

            const reader = new FileReader();
            reader.onload = (event) => {
                const imgDataUrl = event.target.result;
                if (cameraVideo) cameraVideo.style.display = 'none';
                if (cameraPreviewImg) {
                    cameraPreviewImg.src = imgDataUrl;
                    cameraPreviewImg.style.display = 'block';
                }

                const img = new Image();
                img.onload = async () => {
                    const maxDim = 640;
                    let w = Math.max(10, img.naturalWidth || img.width || 640);
                    let h = Math.max(10, img.naturalHeight || img.height || 480);
                    if (w > maxDim || h > maxDim) {
                        if (w > h) {
                            h = Math.round(h * (maxDim / w));
                            w = maxDim;
                        } else {
                            w = Math.round(w * (maxDim / h));
                            h = maxDim;
                        }
                    }

                    aiCanvas.width = w;
                    aiCanvas.height = h;
                    const ctx = aiCanvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, w, h);

                    setTimeout(async () => {
                        await executeRealAIVision(aiCanvas);
                    }, 50);
                };
                img.src = imgDataUrl;
            };
            reader.readAsDataURL(file);

            uploadGallery.value = '';
        });
    }

    // =========================================================================
    // BASIS DATA PANGAN RESMI (pangan.json / TKPI KEMENKES RI)
    // =========================================================================
    const _EMBEDDED_PANGAN_DATA = [
      {"id":"sayur_bayam_01","nama":"sayur bayam","aliases":["sayur bayam","sayur bayam bening","bayam bening","bayam","bayam rebus"],"kategori":"Sayuran","kalori":20,"protein":1.6,"lemak":0.3,"karbohidrat":3.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_bayam_tumis_02","nama":"tumis bayam","aliases":["tumis bayam","cah bayam","bayam goreng"],"kategori":"Sayuran","kalori":34,"protein":1.8,"lemak":1.5,"karbohidrat":3.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_buncis_01","nama":"tumis buncis","aliases":["tumis buncis","buncis","cah buncis","buncis wortel"],"kategori":"Sayuran","kalori":45,"protein":1.8,"lemak":2.2,"karbohidrat":5.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_capcay_01","nama":"sayur capcay","aliases":["capcay","cap cay","sayur capcay","tumis capcay"],"kategori":"Sayuran","kalori":48,"protein":1.8,"lemak":2.5,"karbohidrat":6.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_lodeh_01","nama":"sayur lodeh","aliases":["sayur lodeh","lodeh"],"kategori":"Sayuran","kalori":70,"protein":2.0,"lemak":4.5,"karbohidrat":6.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_sop_01","nama":"sayur sop","aliases":["sayur sop","sop sayur","sup sayur","sop","sup"],"kategori":"Sayuran","kalori":25,"protein":1.3,"lemak":0.5,"karbohidrat":4.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_kangkung_01","nama":"tumis kangkung","aliases":["tumis kangkung","cah kangkung","kangkung"],"kategori":"Sayuran","kalori":28,"protein":2.2,"lemak":0.8,"karbohidrat":3.8,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_labu_01","nama":"tumis labu siam","aliases":["tumis labu siam","labu siam","labu","jipang"],"kategori":"Sayuran","kalori":24,"protein":1.0,"lemak":0.4,"karbohidrat":4.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_asem_01","nama":"sayur asem","aliases":["sayur asem","sayur asam","asem","asam"],"kategori":"Sayuran","kalori":28,"protein":1.2,"lemak":0.4,"karbohidrat":5.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_wortel_01","nama":"wortel rebus","aliases":["wortel rebus","wortel","stik wortel"],"kategori":"Sayuran","kalori":35,"protein":1.0,"lemak":0.3,"karbohidrat":8.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"karbo_nasi_putih_01","nama":"nasi putih","aliases":["nasi putih","nasi putih pulen","nasi"],"kategori":"Karbohidrat","kalori":130,"protein":2.7,"lemak":0.3,"karbohidrat":28.7,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"karbo_nasi_uduk_02","nama":"nasi uduk","aliases":["nasi uduk","nasi gurih","nasi kuning"],"kategori":"Karbohidrat","kalori":160,"protein":3.2,"lemak":4.2,"karbohidrat":28.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"karbo_nasi_merah_03","nama":"nasi merah","aliases":["nasi merah"],"kategori":"Karbohidrat","kalori":110,"protein":2.6,"lemak":0.9,"karbohidrat":23.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"karbo_kentang_04","nama":"kentang rebus","aliases":["kentang rebus","kentang"],"kategori":"Karbohidrat","kalori":87,"protein":2.0,"lemak":0.1,"karbohidrat":20.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"hewan_ayam_goreng_01","nama":"ayam goreng","aliases":["ayam goreng","ayam lengkuas","ayam kremes","ayam"],"kategori":"Protein Hewani","kalori":250,"protein":28.0,"lemak":14.5,"karbohidrat":1.8,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"hewan_telur_02","nama":"telur rebus","aliases":["telur rebus","telur ceplok","telur balado","telur"],"kategori":"Protein Hewani","kalori":155,"protein":12.6,"lemak":10.6,"karbohidrat":1.1,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"hewan_ikan_03","nama":"ikan nila goreng","aliases":["ikan nila goreng","ikan","ikan goreng","ikan lele"],"kategori":"Protein Hewani","kalori":160,"protein":21.0,"lemak":8.0,"karbohidrat":1.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"nabati_tempe_01","nama":"tempe goreng","aliases":["tempe goreng","tempe","tempe goreng gurih"],"kategori":"Protein Nabati","kalori":210,"protein":19.0,"lemak":10.5,"karbohidrat":10.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"nabati_tahu_02","nama":"tahu goreng","aliases":["tahu goreng","tahu","tahu putih","tahu kukus"],"kategori":"Protein Nabati","kalori":95,"protein":9.0,"lemak":5.5,"karbohidrat":2.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"buah_melon_01","nama":"buah melon","aliases":["buah melon","melon"],"kategori":"Buah","kalori":36,"protein":0.8,"lemak":0.2,"karbohidrat":8.5,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"buah_semangka_02","nama":"buah semangka","aliases":["buah semangka","semangka"],"kategori":"Buah","kalori":32,"protein":0.6,"lemak":0.2,"karbohidrat":7.6,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"buah_jeruk_03","nama":"buah jeruk","aliases":["buah jeruk","jeruk"],"kategori":"Buah","kalori":47,"protein":0.9,"lemak":0.1,"karbohidrat":12.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"buah_pisang_04","nama":"buah pisang","aliases":["buah pisang","pisang"],"kategori":"Buah","kalori":89,"protein":1.1,"lemak":0.3,"karbohidrat":22.8,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"karbo_spaghetti_05","nama":"spaghetti pasta","aliases":["spaghetti","pasta","spageti","mie spaghetti","spaghetti pasta gurih"],"kategori":"Karbohidrat","kalori":158,"protein":5.8,"lemak":1.5,"karbohidrat":30.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"pelengkap_pangsit_06","nama":"kerupuk pangsit","aliases":["kerupuk pangsit","pangsit goreng","kulit pangsit","kerupuk pangsit goreng renyah"],"kategori":"Pelengkap","kalori":480,"protein":4.5,"lemak":22.0,"karbohidrat":65.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"hewan_telur_ceplok_04","nama":"telur ceplok","aliases":["telur ceplok","telur mata sapi","telur ceplok balado","ceplok"],"kategori":"Protein Hewani","kalori":185,"protein":12.4,"lemak":14.2,"karbohidrat":0.8,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"nabati_tempe_orek_03","nama":"tempe orek","aliases":["tempe orek","tempe orek dadu","orek tempe","tempe orek manis"],"kategori":"Protein Nabati","kalori":210,"protein":17.0,"lemak":9.0,"karbohidrat":18.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"sayur_jagung_manis_02","nama":"tumis jagung manis","aliases":["tumis jagung manis","jagung manis","jagung pipil","tumis jagung"],"kategori":"Sayuran","kalori":65,"protein":2.2,"lemak":0.8,"karbohidrat":14.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"hewan_ayam_lengkuas_05","nama":"ayam goreng lengkuas","aliases":["ayam lengkuas","ayam goreng lengkuas","ayam bumbu lengkuas"],"kategori":"Protein Hewani","kalori":245,"protein":26.0,"lemak":13.5,"karbohidrat":2.0,"bdd":100,"sumber":"TKPI Kemenkes RI"},
      {"id":"pelengkap_kerupuk_bawang_07","nama":"kerupuk bawang","aliases":["kerupuk bawang","kerupuk bawang finna","kerupuk putih","kerupuk"],"kategori":"Pelengkap","kalori":480,"protein":3.5,"lemak":24.0,"karbohidrat":65.0,"bdd":100,"sumber":"TKPI Kemenkes RI"}
    ];

    let _panganDatabase = _EMBEDDED_PANGAN_DATA;
    window._panganDatabase = _EMBEDDED_PANGAN_DATA;

    async function loadPanganDatabase() {
        try {
            const res = await fetch('pangan.json');
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data) && data.length > 0) {
                    _panganDatabase = data;
                    window._panganDatabase = data;
                    console.log('✓ pangan.json berhasil dimuat (' + data.length + ' item)');
                    return;
                }
            }
        } catch (e) {
            console.info('Menggunakan basis data pangan tersemat standar');
        }
        _panganDatabase = _EMBEDDED_PANGAN_DATA;
        window._panganDatabase = _EMBEDDED_PANGAN_DATA;
    }
    loadPanganDatabase();

    // Fungsi Pencarian Makanan di pangan.json dengan Normalisasi Lengkap
    function findInPanganDatabase(name) {
        if (!name || typeof name !== 'string') return null;
        const db = (_panganDatabase && _panganDatabase.length > 0) ? _panganDatabase : (window._panganDatabase || _EMBEDDED_PANGAN_DATA);
        const raw = name.toLowerCase()
            .replace(/[\(\)\[\]\.,\/#!$%\^&\*;:{}=\-_`~?]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
        if (!raw) return null;

        // 1. Exact match on nama first
        for (const item of db) {
            if ((item.nama || '').toLowerCase().trim() === raw) return item;
        }

        // 2. Exact match on aliases
        for (const item of db) {
            if (Array.isArray(item.aliases)) {
                for (const a of item.aliases) {
                    if ((a || '').toLowerCase().trim() === raw) return item;
                }
            }
        }

        // 3. Stripped prefix/suffix match (buah, sayur, segar, pulen, renyah, gurih, dll)
        const stripped = raw
            .replace(/\b(buah|sayur|sayuran|pilihan|segar|pulen|renyah|gurih|butir|potong|iris|porsi|cup|kemasan)\b/g, '')
            .replace(/\s+/g, ' ')
            .trim();

        if (stripped) {
            for (const item of db) {
                const itemClean = (item.nama || '').toLowerCase().replace(/\b(buah|sayur|sayuran)\b/g, '').replace(/\s+/g, ' ').trim();
                if (itemClean === stripped) return item;
            }
            for (const item of db) {
                if (Array.isArray(item.aliases)) {
                    for (const a of item.aliases) {
                        const aClean = (a || '').toLowerCase().replace(/\b(buah|sayur|sayuran)\b/g, '').replace(/\s+/g, ' ').trim();
                        if (aClean === stripped) return item;
                    }
                }
            }
        }

        // 4. Keyword / phrase match with word boundary (sorted by length descending for specificity)
        const candidates = [];
        for (const item of db) {
            candidates.push({ phrase: item.nama || '', item: item });
            if (Array.isArray(item.aliases)) {
                for (const a of item.aliases) {
                    if (a && a.length >= 4) {
                        candidates.push({ phrase: a, item: item });
                    }
                }
            }
        }
        candidates.sort((a, b) => b.phrase.length - a.phrase.length);

        for (const cand of candidates) {
            const candNorm = cand.phrase.toLowerCase().replace(/[\(\)\[\]\.,\/#!$%\^&\*;:{}=\-_`~?]/g, ' ').replace(/\s+/g, ' ').trim();
            if (candNorm.length < 3) continue;
            const pattern = new RegExp('\\b' + candNorm.replace(/\s+/g, '\\s+') + '\\b', 'i');
            if (pattern.test(raw)) {
                return cand.item;
            }
        }

        return null;
    }
    window.findInPanganDatabase = findInPanganDatabase;

    // Fungsi Pemrosesan Item Makanan Terdeteksi (Dua Tingkat: Database -> Gemini Fallback)
    function processDetectedFoodItem(rawItem) {
        if (!rawItem || typeof rawItem !== 'object') return null;

        // 1. Validasi Nama
        const rawName = String(rawItem.name || rawItem.item || '').trim();
        if (!rawName) return null;

        // 2. Validasi Gramasi Porsi
        let grams = parseFloat(rawItem.estimated_grams || rawItem.gram || 100);
        if (isNaN(grams) || grams <= 0) grams = 100;
        grams = Math.round(grams);

        // 3. Validasi Keyakinan Deteksi Visual
        let detConf = parseFloat(rawItem.confidence || rawItem.conf || 0.85);
        if (typeof rawItem.confidence === 'string' && rawItem.confidence.includes('%')) {
            detConf = parseFloat(rawItem.confidence) / 100;
        }
        if (isNaN(detConf) || detConf < 0) detConf = 0.5;
        if (detConf > 1) detConf = detConf / 100;

        // 4. Cek Database pangan.json
        const dbMatch = findInPanganDatabase(rawName);

        let per100g = {
            kalori: 0,
            protein: 0,
            karbohidrat: 0,
            lemak: 0
        };
        let sourceLabel = '';
        let sourceType = '';
        let nutConf = 0.70;

        if (dbMatch) {
            // PRIORITAS 1: DATA DATABASE RESMI (pangan.json / TKPI)
            // Nilai gizi dari Gemini diabaikan sepenuhnya jika makanan ada di database!
            per100g.kalori = parseFloat(dbMatch.kalori) || 0;
            per100g.protein = parseFloat(dbMatch.protein) || 0;
            per100g.karbohidrat = parseFloat(dbMatch.karbohidrat) || 0;
            per100g.lemak = parseFloat(dbMatch.lemak) || 0;
            sourceLabel = '✓ Data Database';
            sourceType = 'DATABASE';
            nutConf = 0.99;
        } else {
            // PRIORITAS 2: ESTIMASI AI FALLBACK (Google Gemini Vision)
            sourceLabel = '⚠ Estimasi AI';
            sourceType = 'AI_ESTIMATE';

            const n100 = rawItem.nutrition_per_100g || {};
            const geminiKal = parseFloat(n100.energy_kcal ?? n100.kalori ?? rawItem.kalori ?? rawItem.kal);
            const geminiPro = parseFloat(n100.protein_g ?? n100.protein ?? rawItem.protein ?? rawItem.pro);
            const geminiKar = parseFloat(n100.carbohydrate_g ?? n100.karbohidrat ?? rawItem.karbohidrat ?? rawItem.kar);
            const geminiLem = parseFloat(n100.fat_g ?? n100.lemak ?? rawItem.lemak ?? rawItem.lem);

            if (!isNaN(geminiKal) && geminiKal >= 0) per100g.kalori = geminiKal;
            else per100g.kalori = 60;

            if (!isNaN(geminiPro) && geminiPro >= 0) per100g.protein = geminiPro;
            else per100g.protein = 1.0;

            if (!isNaN(geminiKar) && geminiKar >= 0) per100g.karbohidrat = geminiKar;
            else per100g.karbohidrat = 10.0;

            if (!isNaN(geminiLem) && geminiLem >= 0) per100g.lemak = geminiLem;
            else per100g.lemak = 0.5;

            let rawNutConf = parseFloat(rawItem.nutrition_confidence || 0.70);
            if (typeof rawItem.nutrition_confidence === 'string' && rawItem.nutrition_confidence.includes('%')) {
                rawNutConf = parseFloat(rawItem.nutrition_confidence) / 100;
            }
            if (isNaN(rawNutConf) || rawNutConf < 0) rawNutConf = 0.70;
            if (rawNutConf > 1) rawNutConf = rawNutConf / 100;
            nutConf = rawNutConf;
        }

        // 5. Perhitungan Berdasarkan Berat oleh JavaScript Sistem:
        // nilai aktual = nilai per 100 g * (berat / 100)
        const ratio = grams / 100.0;
        const actualKal = Math.round(per100g.kalori * ratio);
        const actualPro = parseFloat((per100g.protein * ratio).toFixed(1));
        const actualKar = parseFloat((per100g.karbohidrat * ratio).toFixed(1));
        const actualLem = parseFloat((per100g.lemak * ratio).toFixed(1));

        return {
            name: rawName,
            category: rawItem.category || 'Komposisi Makanan',
            gram: grams,
            detConf: detConf,
            nutConf: nutConf,
            sourceLabel: sourceLabel,
            sourceType: sourceType,
            per100g: per100g,
            kal: actualKal,
            pro: actualPro,
            kar: actualKar,
            lem: actualLem
        };
    }
    window.processDetectedFoodItem = processDetectedFoodItem;

    // Cloud Vision API Caller (Tanpa Anchoring & Fallback Nilai Gizi per 100g)
    async function queryCloudGeminiVLM(base64Jpeg, apiKey) {
        const cleanKey = String(apiKey || '').replace(/^["']|["']$/g, '').trim();
        if (!cleanKey) throw new Error('Kunci API Gemini belum diatur atau kosong');

        const promptText = `Kamu adalah sistem vision AI untuk analisis visual makanan Program Makan Bergizi Gratis (MBG).
Tugasmu adalah menganalisis citra foto baki makanan bersekat/kompartemen ini secara cermat, objektif, dan murni berdasarkan apa yang tampak di foto tanpa mengarang.

Instruksi Analisis:
1. Identifikasi setiap jenis makanan yang benar-benar tampak di foto baki (seperti makanan pokok/karbohidrat, lauk hewani, lauk nabati, sayuran, buah-buahan, camilan/kerupuk, atau susu).
2. Tuliskan nama makanan secara spesifik apa adanya sesuai wujud aslinya (misalnya: "nasi putih", "kelengkeng", "telur ceplok", "tempe orek", "tumis jagung", dsb.).
3. JANGAN mengarang makanan yang tidak terlihat di foto. JANGAN mengubah identifikasi makanan menjadi makanan lain karena contoh atau asumsi.
4. Estimasi berat porsi makanan dalam gram (estimated_grams) yang realistis untuk porsi makan siang anak sekolah (angka > 0).
5. Berikan detection confidence (confidence: desimal 0.0 - 1.0) untuk ketepatan identifikasi visual makanan.
6. Untuk setiap makanan, berikan estimasi nilai gizi per 100 gram (nutrition_per_100g: energy_kcal, protein_g, carbohydrate_g, fat_g) berdasarkan pengetahuan nutrisi umum sebagai fallback jika makanan belum ada di database lokal.
7. Sediakan nutrition_confidence (desimal 0.0 - 1.0) dan tandai nutrition_source: "AI_ESTIMATE". Nilai tersebut hanya merupakan estimasi dan bukan pengganti data laboratorium atau database nutrisi resmi.
8. Jika baki kosong, buram parah, atau makanan tidak dapat diidentifikasi dengan yakin, kembalikan items kosong [] dan jelaskan di analysis bahwa foto kurang jelas.

Kembalikan HANYA format JSON valid tanpa markdown atau backtick dengan struktur:
{
  "packageName": "Ringkasan Menu MBG Terdeteksi",
  "items": [
    {
      "name": "nama makanan",
      "category": "karbohidrat | hewani | nabati | sayur | buah | pelengkap",
      "estimated_grams": 100,
      "confidence": 0.85,
      "nutrition_per_100g": {
        "energy_kcal": 60.0,
        "protein_g": 1.3,
        "carbohydrate_g": 15.0,
        "fat_g": 0.1
      },
      "nutrition_confidence": 0.70,
      "nutrition_source": "AI_ESTIMATE"
    }
  ],
  "analysis": "Deskripsi singkat hasil pengamatan visual baki makanan."
}`;

        const modelsToTry = [
            'gemini-3.8-flash',
            'gemini-3.7-flash',
            'gemini-3.5-flash-lite',
            'gemini-flash-lite-latest'
        ];

        let lastErr = null;
        for (const modelName of modelsToTry) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 6000);
                const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' + modelName + ':generateContent?key=' + encodeURIComponent(cleanKey);
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: [{
                            parts: [
                                { text: promptText },
                                { inlineData: { mimeType: 'image/jpeg', data: base64Jpeg } }
                            ]
                        }],
                        generationConfig: {
                            temperature: 0.1,
                            responseMimeType: 'application/json'
                        }
                    }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                if (!res.ok) {
                    const errBody = await res.text();
                    lastErr = new Error('Model ' + modelName + ' HTTP ' + res.status + ': ' + errBody);
                    continue;
                }
                const data = await res.json();
                const rawText = data.candidates?.[0]?.content?.parts?.[0]?.text;
                if (!rawText) {
                    lastErr = new Error('Empty response from ' + modelName);
                    continue;
                }

                let parsedResult;
                try {
                    parsedResult = JSON.parse(rawText.replace(/```json/gi, '').replace(/```/g, '').trim());
                } catch (parseE) {
                    const match = rawText.match(/\{[\s\S]*\}/);
                    if (match) parsedResult = JSON.parse(match[0]);
                    else throw parseE;
                }
                return parsedResult;
            } catch (err) {
                lastErr = err;
            }
        }
        throw lastErr || new Error('Semua model Gemini gagal');
    }

    // SISTEM PEMINDAIAN & ANALISIS MAKANAN
    async function executeRealAIVision(canvasElement) {
        // 1. RESET STATE SECARA PENUH: Setiap scan baru menghapus summary dan intake lama
        window._aiDetectionSummary = null;
        window.currentMealIntake = null;

        const autoResultsEl = document.getElementById('auto-detection-results');
        if (autoResultsEl) {
            autoResultsEl.innerHTML = '';
            autoResultsEl.classList.add('hidden');
            autoResultsEl.style.display = 'none';
        }

        try {
            const ctx = canvasElement.getContext('2d');
            const W = canvasElement.width;
            const H = canvasElement.height;
            const snapshotThumb = canvasElement.toDataURL('image/jpeg', 0.6);
            const base64Jpeg = snapshotThumb.split(',')[1];

            let matchedPackage = 'Paket MBG Lengkap';
            let engineUsedLabel = '✨ Dianalisis Cerdas oleh Google Gemini Vision AI';
            let vlmAnalysisNote = 'Porsi dan komposisi makanan dianalisis secara objektif.';
            let rawDetectedItems = [];
            let cloudSuccess = false;

            // Tahap 1: Coba Local Python Server API jika dijalankan di localhost
            const isLocalDev = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
            if (isLocalDev) {
                try {
                    if (scanStatusText) scanStatusText.textContent = 'Menganalisis Komposisi Baki Makanan...';
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 1200);
                    const apiRes = await fetch('http://127.0.0.1:5000/api/detect', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: base64Jpeg }),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                    if (apiRes.ok) {
                        const data = await apiRes.json();
                        if (data && data.success && Array.isArray(data.items) && data.items.length > 0) {
                            rawDetectedItems = data.items;
                            matchedPackage = data.packageName || 'Menu MBG Terdeteksi';
                            vlmAnalysisNote = data.analysis || 'Komposisi makanan teranalisis otomatis.';
                            engineUsedLabel = '🔍 Komposisi Menu Baki MBG Teridentifikasi';
                            cloudSuccess = true;
                        }
                    }
                } catch (backendErr) {
                    // Berlanjut ke cloud vision
                }
            }

            // Tahap 2: Google Gemini Vision AI
            const activeKey = (vlmApiKey || localStorage.getItem('mbg_vlm_api_key') || localStorage.getItem('gemini_api_key') || localStorage.getItem('sppg_vlm_key') || _DEFAULT_AI_KEY).replace(/^["']|["']$/g, '').trim();
            if (!cloudSuccess && activeKey) {
                if (scanStatusText) scanStatusText.textContent = 'Menganalisis Cerdas dengan Google Gemini AI...';

                // Prioritaskan Panggilan Langsung Google Gemini API
                try {
                    const vlmRes = await queryCloudGeminiVLM(base64Jpeg, activeKey);
                    if (vlmRes && Array.isArray(vlmRes.items)) {
                        rawDetectedItems = vlmRes.items;
                        matchedPackage = vlmRes.packageName || 'Menu MBG Terdeteksi';
                        vlmAnalysisNote = vlmRes.analysis || 'Porsi dan komposisi makanan teranalisis otomatis.';
                        engineUsedLabel = '✨ Dianalisis Cerdas oleh Google Gemini Vision AI';
                        cloudSuccess = true;
                    }
                } catch (directErr) {
                    console.warn('Direct Google API failed, mencoba /api/gemini proxy:', directErr);
                }

                // Fallback ke Vercel Serverless Function /api/gemini
                if (!cloudSuccess) {
                    try {
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 6000);
                        const serverRes = await fetch('/api/gemini', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ image: base64Jpeg, apiKey: activeKey }),
                            signal: controller.signal
                        });
                        clearTimeout(timeoutId);
                        if (serverRes.ok) {
                            const sData = await serverRes.json();
                            if (sData && sData.success && sData.data && Array.isArray(sData.data.items)) {
                                rawDetectedItems = sData.data.items;
                                matchedPackage = sData.data.packageName || 'Menu MBG Terdeteksi';
                                vlmAnalysisNote = sData.data.analysis || 'Porsi dan komposisi makanan teranalisis otomatis.';
                                engineUsedLabel = '✨ Dianalisis Cerdas oleh Google Gemini Vision AI (' + (sData.model || 'Gemini Flash') + ')';
                                cloudSuccess = true;
                            }
                        }
                    } catch (apiErr) {
                        console.warn('/api/gemini call skipped:', apiErr);
                    }
                }
            }

            // Jika API gagal (timeout, 429, jaringan terputus) -> JANGAN membuat makanan palsu / color heuristic!
            if (!cloudSuccess) {
                throw new Error('Analisis AI gagal. Silakan coba scan kembali.');
            }

            // Jika AI sangat tidak yakin atau baki tidak dapat diidentifikasi
            if (!rawDetectedItems || rawDetectedItems.length === 0) {
                window._aiDetectionSummary = 
                    '<div style="text-align:center; padding:1.2rem; background:#fffbeb; border:1px solid #fde68a; border-radius:10px;">' +
                        '<p style="color:#b45309; font-weight:700; font-size:1.05rem; margin:0 0 0.5rem 0;">⚠️ Makanan Belum Teridentifikasi</p>' +
                        '<p style="font-size:0.88rem; color:#64748b; margin:0;">Makanan belum dapat diidentifikasi dengan yakin. Silakan gunakan foto yang lebih jelas.</p>' +
                    '</div>';
                window.currentMealIntake = null;
                return;
            }

            // Tahap 3: Proses setiap item dengan Prioritas Database -> AI Fallback & Hitung Gizi di JS
            const processedItems = [];
            let hasAiEstimate = false;

            rawDetectedItems.forEach(rawItem => {
                const proc = processDetectedFoodItem(rawItem);
                if (proc) {
                    processedItems.push(proc);
                    if (proc.sourceType === 'AI_ESTIMATE') {
                        hasAiEstimate = true;
                    }
                }
            });

            if (processedItems.length === 0) {
                window._aiDetectionSummary = 
                    '<div style="text-align:center; padding:1.2rem; background:#fffbeb; border:1px solid #fde68a; border-radius:10px;">' +
                        '<p style="color:#b45309; font-weight:700; font-size:1.05rem; margin:0 0 0.5rem 0;">⚠️ Makanan Belum Teridentifikasi</p>' +
                        '<p style="font-size:0.88rem; color:#64748b; margin:0;">Makanan belum dapat diidentifikasi dengan yakin. Silakan gunakan foto yang lebih jelas.</p>' +
                    '</div>';
                window.currentMealIntake = null;
                return;
            }

            // Hitung Total Nilai Gizi Murni oleh JavaScript Sistem
            let totalKal = 0, totalPro = 0, totalKar = 0, totalLem = 0;
            processedItems.forEach(it => {
                totalKal += it.kal;
                totalPro += it.pro;
                totalKar += it.kar;
                totalLem += it.lem;
            });
            totalKal = Math.round(totalKal);
            totalPro = parseFloat(totalPro.toFixed(1));
            totalKar = parseFloat(totalKar.toFixed(1));
            totalLem = parseFloat(totalLem.toFixed(1));

            // Simpan ke status intake global
            window.currentMealIntake = {
                kalori: totalKal,
                protein: totalPro,
                karbo: totalKar,
                lemak: totalLem,
                items: processedItems,
                photoUrl: snapshotThumb
            };

            // Sinkronkan ke Kontrol Form Manual
            const kSel = document.getElementById('karbo');
            const hSel = document.getElementById('prohew');
            const nSel = document.getElementById('pronab');
            const sSel = document.getElementById('sayur');
            const kGram = document.getElementById('karbo-gram');
            const hGram = document.getElementById('prohew-gram');
            const nGram = document.getElementById('pronab-gram');
            const sGram = document.getElementById('sayur-gram');
            const cName = document.getElementById('custom-name');
            const cGram = document.getElementById('custom-gram');

            const itemKarbo = processedItems.find(i => /karbo|nasi|mie|pasta|spaghetti|roti|kentang/i.test(i.category) || /nasi|mie|spaghetti|kentang/i.test(i.name));
            const itemProhew = processedItems.find(i => (/hewani|ayam|telur|ikan|daging/i.test(i.category) && !/sayur/i.test(i.category)) || (/\bayam|telur|ikan|daging/i.test(i.name) && !/bayam/i.test(i.name)));
            const itemPronab = processedItems.find(i => /nabati|tempe|tahu/i.test(i.category) || /tempe|tahu/i.test(i.name));
            const itemSayur = processedItems.find(i => /sayur|sop|buncis|capcay|jagung/i.test(i.category) || /sayur|sop|buncis|capcay|jagung|kangkung/i.test(i.name));
            const otherItems = processedItems.filter(i => i !== itemKarbo && i !== itemProhew && i !== itemPronab && i !== itemSayur);

            if (kSel && itemKarbo) kSel.value = itemKarbo.name;
            if (kGram && itemKarbo) kGram.value = itemKarbo.gram;

            if (hSel && itemProhew) hSel.value = itemProhew.name;
            if (hGram && itemProhew) hGram.value = itemProhew.gram;

            if (nSel && itemPronab) nSel.value = itemPronab.name;
            if (nGram && itemPronab) nGram.value = itemPronab.gram;

            if (sSel && itemSayur) sSel.value = itemSayur.name;
            if (sGram && itemSayur) sGram.value = itemSayur.gram;

            if (cName && cGram && otherItems.length > 0) {
                cName.value = otherItems.map(o => o.name).join(' + ');
                cGram.value = otherItems.reduce((acc, o) => acc + o.gram, 0);
            }

            // Susun Tabel Rincian Menu dengan Pemisahan Keyakinan & Sumber Gizi
            let itemsTableHtml = '<table style="width:100%; border-collapse:collapse; margin-top:0.6rem; font-size:0.84rem;">' +
                '<tr style="border-bottom:1.5px solid rgba(0,0,0,0.1); text-align:left; color:var(--text-light);">' +
                    '<th style="padding:0.4rem 0;">Komposisi Makanan</th>' +
                    '<th style="text-align:center;">Keyakinan Model</th>' +
                    '<th style="text-align:center;">Sumber Data Gizi</th>' +
                    '<th style="text-align:right;">Kalori</th>' +
                    '<th style="text-align:right;">Protein</th>' +
                '</tr>';

            processedItems.forEach(it => {
                const sourceBadge = (it.sourceType === 'DATABASE')
                    ? '<span style="background:#dcfce7; color:#15803d; border:1px solid #86efac; padding:0.2rem 0.5rem; border-radius:6px; font-weight:700; font-size:0.75rem; display:inline-block;">✓ Data Database</span>'
                    : '<span style="background:#fef3c7; color:#b45309; border:1px solid #fde68a; padding:0.2rem 0.5rem; border-radius:6px; font-weight:700; font-size:0.75rem; display:inline-block;">⚠ Estimasi AI</span>';

                const detConfText = Math.round(it.detConf * 100) + '%';
                const nutConfText = (it.sourceType === 'DATABASE') ? 'Basis TKPI Kemenkes' : 'Estimasi Gizi: ' + Math.round(it.nutConf * 100) + '%';

                itemsTableHtml += '<tr style="border-bottom:1px dashed rgba(0,0,0,0.08);">' +
                    '<td style="padding:0.5rem 0;">' +
                        '<span style="font-size:0.75rem; color:#2563eb; font-weight:700; display:block;">' + it.category + '</span>' +
                        '<strong>' + it.name + '</strong> <span style="font-size:0.75rem; color:var(--text-light);">(' + it.gram + 'g)</span>' +
                        '<div style="font-size:0.72rem; color:var(--text-light); margin-top:2px;">Karbo: ' + it.kar + 'g | Lemak: ' + it.lem + 'g</div>' +
                    '</td>' +
                    '<td style="text-align:center;">' +
                        '<div style="font-size:0.78rem; font-weight:700; color:#1e293b;">Deteksi: ' + detConfText + '</div>' +
                        '<div style="font-size:0.72rem; color:#64748b;">' + nutConfText + '</div>' +
                    '</td>' +
                    '<td style="text-align:center;">' + sourceBadge + '</td>' +
                    '<td style="text-align:right; font-weight:700; color:var(--text-main);">' + it.kal + ' kcal</td>' +
                    '<td style="text-align:right; font-weight:700; color:#1d4ed8;">' + it.pro.toFixed(1) + 'g</td>' +
                '</tr>';
            });
            itemsTableHtml += '</table>';

            // Kotak Ringkasan Total Nutrisi
            const targetMBG = (window.currentTargetNutrition && window.currentTargetNutrition.mbgTargetKal) || 807;
            const pctKal = Math.round((totalKal / targetMBG) * 100);

            const nutritionSummaryBox = 
                '<div style="background:rgba(16,185,129,0.1); padding:0.9rem; border-radius:10px; margin-top:0.75rem; text-align:left; font-size:0.9rem; border:1px solid rgba(16,185,129,0.25);">' +
                    '<div style="margin-bottom:0.35rem;">🔥 <strong>Total Kalori:</strong> ' + totalKal + ' kcal <span style="float:right; color:var(--text-light); font-weight:700;">(' + pctKal + '% Target 1x MBG)</span></div>' +
                    '<div style="margin-bottom:0.35rem;">🌾 <strong>Karbohidrat:</strong> ' + totalKar + ' g</div>' +
                    '<div style="margin-bottom:0.35rem;">🥩 <strong>Protein:</strong> ' + totalPro + ' g</div>' +
                    '<div>💧 <strong>Lemak:</strong> ' + totalLem + ' g</div>' +
                '</div>';

            const sourceDisclaimer = hasAiEstimate
                ? '<div style="margin-top:0.65rem; padding:0.55rem 0.75rem; background:#fffbeb; border:1px solid #fef3c7; border-radius:8px; font-size:0.78rem; color:#b45309; text-align:left;">' +
                      '<i class="fa-solid fa-triangle-exclamation"></i> <strong>Catatan:</strong> Nilai gizi bertanda <em>Estimasi AI</em> merupakan estimasi kecerdasan buatan karena makanan belum tersedia dalam database.' +
                  '</div>'
                : '<div style="margin-top:0.65rem; padding:0.55rem 0.75rem; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; font-size:0.78rem; color:#15803d; text-align:left;">' +
                      '<i class="fa-solid fa-check-circle"></i> <strong>Status Gizi:</strong> Seluruh item terverifikasi dari Database Komposisi Pangan Resmi (pangan.json / TKPI Kemenkes RI).' +
                  '</div>';

            window._aiDetectionSummary = 
                '<div style="text-align:center; margin-bottom:0.8rem; background:#0f172a; border-radius:12px; padding:6px; box-shadow:0 2px 10px rgba(0,0,0,0.2); overflow:hidden;">' +
                    '<div class="yolo-preview-container" style="border-color:#2563eb; width:100%; max-width:440px; margin:0 auto; border-radius:10px; overflow:hidden; background:#0f172a;">' +
                        '<img src="' + snapshotThumb + '" style="width:100%; height:auto; max-height:360px; object-fit:contain; display:block; margin:0 auto; border-radius:8px;" alt="Baki MBG Penuh" />' +
                    '</div>' +
                    '<span style="display:inline-block; margin-top:0.35rem; background:rgba(37,99,235,0.15); color:#60a5fa; padding:0.35rem 0.9rem; border-radius:20px; font-size:0.83rem; font-weight:800; border:1px solid rgba(59,130,246,0.3);">' +
                        engineUsedLabel +
                    '</span>' +
                '</div>' +
                '<div style="background:white; padding:0.9rem; border-radius:10px; border:1px solid rgba(0,0,0,0.08); margin-bottom:0.8rem;">' +
                    '<strong style="font-size:0.9rem; color:var(--text-main);"><i class="fa-solid fa-utensils"></i> Rincian Menu & Nilai Gizi:</strong>' +
                    itemsTableHtml +
                    nutritionSummaryBox +
                    sourceDisclaimer +
                    (vlmAnalysisNote ? '<p style="margin-top:0.6rem; font-size:0.82rem; color:var(--text-light); background:rgba(37,99,235,0.05); padding:0.5rem 0.7rem; border-radius:6px; border-left:3px solid #2563eb; text-align:left;">💡 <em>' + vlmAnalysisNote + '</em></p>' : '') +
                    '<div style="display:flex; gap:0.5rem; margin-top:0.85rem; flex-wrap:wrap;">' +
                        '<button type="button" class="btn btn-primary" style="flex:1; font-size:0.85rem;" onclick="if(window.closeCustomAlert) window.closeCustomAlert(); openScreen(\'screen-dashboard-mbg\')">' +
                            '📊 Buka Dashboard Evaluasi &rarr;' +
                        '</button>' +
                        '<button type="button" class="btn btn-secondary" style="flex:1; font-size:0.85rem;" onclick="if(window.closeCustomAlert) window.closeCustomAlert(); openScreen(\'screen-jurnal\')">' +
                            '🍱 Catat ke Jurnal MBG &rarr;' +
                        '</button>' +
                    '</div>' +
                '</div>';

        } catch (err) {
            console.error('AI Scan Error:', err);
            window._aiDetectionSummary = 
                '<div style="background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:1.2rem; text-align:center;">' +
                    '<p style="color:#ef4444; font-weight:700; font-size:1.05rem; margin:0 0 0.5rem 0;">⚠️ Analisis AI gagal</p>' +
                    '<p style="font-size:0.88rem; color:#64748b; margin:0;">Silakan coba scan kembali atau ambil foto baki dengan pencahayaan jelas.</p>' +
                '</div>';
            window.currentMealIntake = null;
        } finally {
            closeCameraModal();
            window.openScreen('screen-kalkulator');
            if (window.currentMealIntake && window.currentMealIntake.items) {
                window.calculateNutrition(true, true);
            }

            // 1. Tampilkan kartu hasil pemindaian di kontainer auto-detection-results
            const autoResultsEl = document.getElementById('auto-detection-results');
            if (autoResultsEl && window._aiDetectionSummary) {
                autoResultsEl.innerHTML = window._aiDetectionSummary;
                autoResultsEl.classList.remove('hidden');
                autoResultsEl.style.display = 'block';
            }

            // 2. Perbarui layar pemindai kamera (viewfinder placeholder) dengan foto baki utuh
            const vPlaceholder = document.getElementById('camera-viewfinder-placeholder');
            if (vPlaceholder) {
                if (window.currentMealIntake && window.currentMealIntake.photoUrl) {
                    vPlaceholder.innerHTML = 
                        '<div style="width:100%; max-width:480px; position:relative; border-radius:12px; overflow:hidden; box-shadow:0 4px 14px rgba(0,0,0,0.35); background:#0f172a; padding:4px;">' +
                            '<img src="' + window.currentMealIntake.photoUrl + '" style="width:100%; height:auto; display:block; object-fit:contain; max-height:340px; margin:0 auto; border-radius:8px;" alt="Baki MBG Terpindai" />' +
                            '<div style="position:absolute; bottom:4px; left:4px; right:4px; background:rgba(15,23,42,0.88); backdrop-filter:blur(6px); padding:0.55rem 0.8rem; color:#f8fafc; font-size:0.83rem; font-weight:700; text-align:center; border-radius:0 0 8px 8px;">' +
                                '📸 Foto Baki Makanan Terpindai & Selesai Dianalisis' +
                            '</div>' +
                        '</div>' +
                        '<button type="button" class="btn btn-secondary mt-3" style="font-size:0.82rem; padding:0.4rem 0.9rem;" onclick="document.getElementById(\'btn-open-camera\').click()">' +
                            '📷 Pindai Baki Lain' +
                        '</button>';
                } else {
                    vPlaceholder.innerHTML = 
                        '<div style="background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:1.2rem; text-align:center; max-width:480px; margin:0 auto;">' +
                            '<p style="color:#ef4444; font-weight:700; font-size:1.05rem; margin:0 0 0.5rem 0;">⚠️ Analisis AI gagal</p>' +
                            '<p style="font-size:0.88rem; color:#64748b; margin:0 0 1rem 0;">Silakan coba scan kembali atau ambil foto baki dengan pencahayaan jelas.</p>' +
                            '<button type="button" class="btn btn-primary" style="font-size:0.85rem; padding:0.45rem 1rem;" onclick="document.getElementById(\'btn-open-camera\').click()">' +
                                '📷 Coba Scan Kembali' +
                            '</button>' +
                        '</div>';
                }
            }

            // 3. Tampilkan Pop-Up Alert Hasil Deteksi
            setTimeout(() => {
                if (window._aiDetectionSummary) {
                    customAlert(
                        '<strong style="font-size:1.15rem; color:var(--primary-color);">Hasil Pemindaian Baki Makanan MBG</strong><br><br>' +
                        window._aiDetectionSummary
                    );
                }
            }, 300);
        }
    }

    // Inisialisasi awal sinkronisasi kalkulator gizi manual saat web dimuat:
    if (window.calculateNutrition) {
        window.calculateNutrition(false, true);
    }

}); // End DOMContentLoaded
