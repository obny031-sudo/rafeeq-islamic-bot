// Rafeeq Telegram Mini App - Main JavaScript

// Initialize Telegram WebApp
let tg = window.Telegram.WebApp;

// Initialize app when ready
document.addEventListener('DOMContentLoaded', function() {
    initTelegramWebApp();
    initNavigation();
    initDailyHub();
    initDashboard();
    initQuranReader();
    initKhatmaDashboard();
    initPrayerDashboard();
    initAICompanion();
    initMoodCheck();
    initAchievements();
    initProfile();
    
    // Hide loading screen after initialization
    setTimeout(() => {
        document.getElementById('loading-screen').classList.remove('active');
        document.getElementById('daily-hub').classList.add('active');
    }, 1000);
});

// Telegram WebApp Initialization
function initTelegramWebApp() {
    // Expand the webapp to full height
    tg.expand();
    
    // Set theme colors based on Telegram theme
    if (tg.themeParams) {
        document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
        document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
        document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color);
        document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color);
        document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color);
        document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color);
    }
    
    // Setup back button
    tg.BackButton.show();
    tg.BackButton.onClick(() => {
        navigateToScreen('dashboard');
    });
    
    // Setup main button
    tg.MainButton.setText('فتح التطبيق');
    tg.MainButton.show();
    tg.MainButton.onClick(() => {
        tg.sendData('opened_webapp');
    });
    
    // Enable haptic feedback
    tg.HapticFeedback.impactOccurred('light');
}

// Navigation System
function initNavigation() {
    // Bottom navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const screen = this.dataset.screen;
            navigateToScreen(screen);
            
            // Update active state
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Haptic feedback
            tg.HapticFeedback.impactOccurred('light');
        });
    });
    
    // Back buttons
    document.querySelectorAll('.back-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const screen = this.dataset.screen;
            navigateToScreen(screen);
        });
    });
    
    // Smart cards navigation
    document.querySelectorAll('.smart-card').forEach(card => {
        card.addEventListener('click', function() {
            const module = this.dataset.module;
            navigateToModule(module);
        });
    });
}

function navigateToScreen(screenId) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Show target screen
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
    }
    
    // Update Telegram back button
    if (screenId === 'dashboard') {
        tg.BackButton.hide();
    } else {
        tg.BackButton.show();
    }
}

function navigateToModule(module) {
    const moduleScreens = {
        'quran': 'quran-reader',
        'prayer': 'prayer-dashboard',
        'adhkar': 'daily-hub',
        'hadith': 'daily-hub',
        'ai': 'ai-companion',
        'favorites': 'profile'
    };
    
    const screenId = moduleScreens[module];
    if (screenId) {
        navigateToScreen(screenId);
    }
}

// Daily Hub Module
function initDailyHub() {
    updateDateDisplay();
    loadDailyContent();
    startPrayerCountdown();
}

function updateDateDisplay() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const arabicDate = now.toLocaleDateString('ar-SA', options);
    document.getElementById('date-display').textContent = arabicDate;
}

function loadDailyContent() {
    // In production, this would fetch from API
    const dailyContent = {
        morningMessage: 'ابدأ يومك بذكر الله واستعن به على أمورك',
        ayah: '﴿وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا﴾',
        ayahReference: 'سورة الطلاق: 2-3',
        wisdom: 'الصبر مفتاح الفرج، ومن يصبر يظفر',
        challenge: 'اقرأ 5 صفحات من القرآن اليوم',
        duaa: 'اللهم إني أسألك العفو والعافية في ديني ودنياي وأهلي ومالي',
        hadith: 'من سلك طريقاً يلتمس فيه علماً سهل الله له به طريقاً إلى الجنة'
    };
    
    document.getElementById('morning-message').textContent = dailyContent.morningMessage;
    document.getElementById('ayah-day').textContent = dailyContent.ayah;
    document.querySelector('.ayah-day .reference').textContent = dailyContent.ayahReference;
    document.getElementById('wisdom').textContent = dailyContent.wisdom;
    document.getElementById('daily-challenge').textContent = dailyContent.challenge;
    document.getElementById('duaa').textContent = dailyContent.duaa;
    document.getElementById('hadith').textContent = dailyContent.hadith;
}

function startPrayerCountdown() {
    // Simulate prayer countdown
    let countdown = 9000; // 2:30:00 in seconds
    
    setInterval(() => {
        countdown--;
        const hours =(Math.floor(countdown / 3600)).toString().padStart(2, '0');
        const minutes = (Math.floor((countdown % 3600) / 60)).toString().padStart(2, '0');
        const seconds = (countdown % 60).toString().padStart(2, '0');
        
        document.getElementById('prayer-countdown').textContent = `${hours}:${minutes}:${seconds}`;
    }, 1000);
}

// Dashboard Module
function initDashboard() {
    loadDashboardStats();
}

function loadDashboardStats() {
    // In production, this would fetch from API
    const stats = {
        nextPrayer: 'العصر - 15:30',
        lastAyah: 'البقرة 255',
        khatmaPercent: '65%',
        hijriDate: '1 محرم 1446',
        gregorianDate: '31 يوليو 2026',
        streak: 7,
        dailyWird: 5
    };
    
    document.getElementById('dashboard-prayer').textContent = stats.nextPrayer;
    document.getElementById('last-ayah').textContent = stats.lastAyah;
    document.getElementById('khatma-percent').textContent = stats.khatmaPercent;
    document.getElementById('hijri-date').textContent = stats.hijriDate;
    document.getElementById('gregorian-date').textContent = stats.gregorianDate;
    document.getElementById('streak-count').textContent = stats.streak;
    document.getElementById('daily-wird').textContent = stats.dailyWird;
}

// Quran Reader Module
function initQuranReader() {
    initThemeToggle();
    initFontSizeControl();
    initPageNavigation();
    initReaderActions();
    loadQuranPage(2);
}

function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        this.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initFontSizeControl() {
    const fontSizeBtn = document.getElementById('font-size');
    let currentSize = 1.3;
    
    fontSizeBtn.addEventListener('click', function() {
        currentSize = currentSize >= 1.8 ? 1.1 : currentSize + 0.1;
        document.getElementById('quran-text').style.fontSize = `${currentSize}rem`;
        
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initPageNavigation() {
    document.getElementById('prev-page').addEventListener('click', function() {
        // Navigate to previous page
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('next-page').addEventListener('click', function() {
        // Navigate to next page
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initReaderActions() {
    document.getElementById('bookmark-btn').addEventListener('click', function() {
        // Save bookmark
        tg.showAlert('تم حفظ العلامة');
        tg.HapticFeedback.notificationOccurred('success');
    });
    
    document.getElementById('tafseer-btn').addEventListener('click', function() {
        // Show tafseer
        tg.showAlert('سيتم عرض التفسير');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('audio-btn').addEventListener('click', function() {
        // Play audio
        tg.showAlert('سيتم تشغيل التلاوة');
        tg.HapticFeedback.impactOccurred('light');
    });
}

function loadQuranPage(pageNumber) {
    // In production, this would fetch from API
    const quranText = `
        بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
        
        الم
        ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ
        الَّذِينَ يُؤْمِنُونَ بِالْغَيْبِ وَيُقِيمُونَ الصَّلَاةَ وَمِمَّا رَزَقْنَاهُمْ يُنفِقُونَ
        وَالَّذِينَ يُؤْمِنُونَ بِمَا أُنزِلَ إِلَيْكَ وَمَا أُنزِلَ مِن قَبْلِكَ وَبِالْآخِرَةِ هُمْ يُوقِنُونَ
    `;
    
    document.getElementById('quran-text').textContent = quranText;
    document.getElementById('current-page').textContent = `صفحة ${pageNumber}`;
    document.getElementById('page-indicator').textContent = `${pageNumber} / 604`;
}

// Khatma Dashboard Module
function initKhatmaDashboard() {
    loadKhatmaProgress();
}

function loadKhatmaProgress() {
    // In production, this would fetch from API
    const progress = {
        percent: 65,
        pagesRemaining: 211,
        completionDate: '15 سبتمبر 2026',
        dailyQuota: 5,
        remainingJuz: 6
    };
    
    document.getElementById('khatma-progress').style.width = `${progress.percent}%`;
    document.getElementById('khatma-percent-display').textContent = `${progress.percent}%`;
    document.getElementById('pages-remaining').textContent = `${progress.pagesRemaining} صفحة متبقية`;
    document.getElementById('completion-date').textContent = progress.completionDate;
    document.getElementById('daily-quota').textContent = `${progress.dailyQuota} صفحات`;
    document.getElementById('remaining-juz').textContent = `${progress.remainingJuz} أجزاء`;
}

// Prayer Dashboard Module
function initPrayerDashboard() {
    initQiblaCompass();
    startPrayerTimers();
}

function initQiblaCompass() {
    // In production, this would use device orientation
    const qiblaArrow = document.getElementById('qibla-arrow');
    qiblaArrow.style.transform = 'rotate(135deg)';
}

function startPrayerTimers() {
    // Simulate prayer countdowns
    let asrCountdown = 9000;
    
    setInterval(() => {
        asrCountdown--;
        const hours = (Math.floor(asrCountdown / 3600)).toString().padStart(2, '0');
        const minutes = (Math.floor((asrCountdown % 3600) / 60)).toString().padStart(2, '0');
        const seconds = (asrCountdown % 60).toString().padStart(2, '0');
        
        document.getElementById('asr-countdown').textContent = `${hours}:${minutes}:${seconds}`;
    }, 1000);
}

// AI Companion Module
function initAICompanion() {
    initChatInput();
    initQuickPrompts();
}

function initChatInput() {
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Add user message
    addChatMessage(message, 'user');
    userInput.value = '';
    
    // Simulate AI response
    setTimeout(() => {
        const response = generateAIResponse(message);
        addChatMessage(response, 'bot');
    }, 1000);
    
    tg.HapticFeedback.impactOccurred('light');
}

function addChatMessage(text, type) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.innerHTML = `<div class="message-content"><p>${text}</p></div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateAIResponse(message) {
    // Simple AI response simulation
    const responses = {
        'قلق': 'لا تقلق، فالله مع الذين اتقوا والذين هم محسنون. توكل على الله واجعل همك هم واحداً.',
        'دعاء': 'اللهم إني أسألك الجنة وما قرب إليها من قول أو عمل، وأعوذ بك من النار وما قرب إليها من قول أو عمل.',
        'تفسير': 'سأقوم بمساعدتك في فهم الآية. ما هي الآية التي تريد تفسيرها؟',
        'تحفيز': 'قال رسول الله صلى الله عليه وسلم: "إن الله يحب إذا عمل أحدكم عملاً أن يتقنه". استمر في جهودك!'
    };
    
    for (const key in responses) {
        if (message.includes(key)) {
            return responses[key];
        }
    }
    
    return 'أنا هنا لمساعدتك. يمكنك سؤالي عن أي شيء يتعلق بالقرآن، الأحاديث، أو الدعاء.';
}

function initQuickPrompts() {
    document.querySelectorAll('.prompt-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const prompt = this.dataset.prompt;
            document.getElementById('user-input').value = prompt;
            sendMessage();
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

// Mood Check Module
function initMoodCheck() {
    initMoodSelection();
    initDailyTracking();
}

function initMoodSelection() {
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const mood = this.dataset.mood;
            const emoji = this.dataset.emoji;
            showMoodResponse(mood, emoji);
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function showMoodResponse(mood, emoji) {
    const responses = {
        happy: 'أحسنت! ابق على هذا الشعور الإيجابي واشكر الله على نعمه.',
        sad: 'لا بأس، فالله مع الصابرين. تذكر أن بعد الضيق يأتي الفرج.',
        anxious: 'توكل على الله وقل "حسبني الله وثيقة"، فنعم الوكيل هو.',
        tired: 'خذ قسطاً من الراحة واجعل نيتك في الراحة التقوي على العبادة.'
    };
    
    const responseDiv = document.getElementById('mood-response');
    responseDiv.innerHTML = `
        <div class="mood-emoji-large">${emoji}</div>
        <p>${responses[mood]}</p>
        <p class="mood-ayah">﴿إِنَّ مَعَ الْعُسْرِ يُسْرًا﴾</p>
    `;
}

function initDailyTracking() {
    document.querySelectorAll('.tracking-item input').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                tg.HapticFeedback.notificationOccurred('success');
                tg.sendData(JSON.stringify({
                    action: 'tracking_complete',
                    item: this.id
                }));
            }
        });
    });
}

// Achievements Module
function initAchievements() {
    loadAchievements();
}

function loadAchievements() {
    // In production, this would fetch from API
    const achievements = {
        totalPages: 156,
        streak: 7,
        tasbeeh: 234,
        khatmaCount: 2
    };
    
    // Update stats
    const statBoxes = document.querySelectorAll('.stat-box .stat-value');
    statBoxes[0].textContent = achievements.totalPages;
    statBoxes[1].textContent = achievements.streak;
    statBoxes[2].textContent = achievements.tasbeeh;
    statBoxes[3].textContent = achievements.khatmaCount;
}

// Profile Module
function initProfile() {
    loadProfileData();
    initProfileActions();
}

function loadProfileData() {
    // In production, this would fetch from API
    const profileData = {
        name: tg.initDataUnsafe?.user?.first_name || 'المستخدم',
        lastSurah: 'البقرة',
        lastDhikr: 'سبحان الله',
        streak: '7 أيام',
        badges: '2 شارات'
    };
    
    document.getElementById('user-name').textContent = profileData.name;
    document.getElementById('profile-last-surah').textContent = profileData.lastSurah;
    document.getElementById('profile-last-dhikr').textContent = profileData.lastDhikr;
    document.getElementById('profile-streak').textContent = profileData.streak;
    document.getElementById('profile-badges').textContent = profileData.badges;
    
    // Set avatar
    if (tg.initDataUnsafe?.user?.photo_url) {
        document.getElementById('user-avatar').style.backgroundImage = `url(${tg.initDataUnsafe.user.photo_url})`;
        document.getElementById('user-avatar').style.backgroundSize = 'cover';
        document.getElementById('user-avatar').textContent = '';
    }
}

function initProfileActions() {
    document.querySelectorAll('.profile-actions .action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.textContent;
            
            if (action === 'الإعدادات') {
                tg.showAlert('سيتم فتح الإعدادات');
            } else if (action === 'المساعدة') {
                tg.showAlert('سيتم فتح المساعدة');
            } else if (action === 'تسجيل الخروج') {
                tg.showConfirm('هل أنت متأكد من تسجيل الخروج؟', (confirmed) => {
                    if (confirmed) {
                        tg.close();
                    }
                });
            }
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

// Utility Functions
function showNotification(message) {
    tg.showAlert(message);
}

function sendDataToBot(data) {
    tg.sendData(JSON.stringify(data));
}

// Handle theme changes from Telegram
Telegram.WebApp.onEvent('themeChanged', function() {
    if (tg.themeParams) {
        document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
        document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
    }
});

// Handle viewport changes
Telegram.WebApp.onEvent('viewportChanged', function() {
    // Adjust layout if needed
});
