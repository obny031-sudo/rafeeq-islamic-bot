// Rafeeq Telegram Mini App - Main JavaScript

// Custom debug console
function debugLog(message) {
    const debugConsole = document.getElementById('debug-console');
    if (debugConsole) {
        debugConsole.style.display = 'block';
        const logEntry = document.createElement('div');
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        debugConsole.appendChild(logEntry);
        debugConsole.scrollTop = debugConsole.scrollHeight;
    }
    console.log(message);
}

// Initialize Telegram WebApp with fallback for browser testing
let tg = window.Telegram?.WebApp || {
    expand: () => {},
    ready: () => {},
    themeParams: {},
    BackButton: {
        show: () => {},
        hide: () => {},
        onClick: () => {},
        offClick: () => {}
    },
    MainButton: {
        setText: () => {},
        show: () => {},
        hide: () => {},
        onClick: () => {},
        offClick: () => {}
    },
    HapticFeedback: {
        impactOccurred: () => {},
        notificationOccurred: () => {}
    },
    showAlert: (msg) => alert(msg),
    showConfirm: (msg, callback) => {
        if (confirm(msg)) callback(true);
    },
    sendData: () => {},
    close: () => {},
    initDataUnsafe: { user: null }
};

// Safe Telegram API calls
function safeHapticFeedback(type = 'light') {
    try {
        if (tg && tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred(type);
        }
    } catch (error) {
        // Silently ignore haptic feedback errors
    }
}

function safeShowAlert(message) {
    try {
        if (tg && tg.showAlert) {
            tg.showAlert(message);
        } else {
            alert(message);
        }
    } catch (error) {
        alert(message);
    }
}

function safeShowConfirm(message, callback) {
    try {
        if (tg && tg.showConfirm) {
            tg.showConfirm(message, callback);
        } else {
            if (confirm(message)) callback(true);
        }
    } catch (error) {
        if (confirm(message)) callback(true);
    }
}

// Initialize app when ready
document.addEventListener('DOMContentLoaded', function() {
    try {
        debugLog('App starting...');
        
        // Initialize Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
            debugLog('Telegram WebApp initialized');
        }
        
        // GLOBAL DELEGATED EVENT LISTENER FOR NAVIGATION
        document.addEventListener('click', (e) => {
            // Find closest clickable target with data-screen attribute
            const targetBtn = e.target.closest('[data-screen]');
            if (targetBtn) {
                e.preventDefault();
                e.stopPropagation();
                const screenId = targetBtn.getAttribute('data-screen');
                debugLog('Delegated click to screen: ' + screenId);
                try {
                    navigateToScreen(screenId);
                } catch (err) {
                    debugLog('ERROR navigating to screen: ' + err.message);
                    console.error(`[Navigation Error] Failed to open ${screenId}:`, err);
                }
                return;
            }
            
            // Find closest clickable target with data-module attribute
            const targetModule = e.target.closest('[data-module]');
            if (targetModule) {
                e.preventDefault();
                e.stopPropagation();
                const moduleId = targetModule.getAttribute('data-module');
                debugLog('Delegated click to module: ' + moduleId);
                try {
                    navigateToModule(moduleId);
                } catch (err) {
                    debugLog('ERROR navigating to module: ' + err.message);
                    console.error(`[Navigation Error] Failed to open module ${moduleId}:`, err);
                }
                return;
            }
        });
        
        debugLog('Global delegated event listener installed');
        
        // Initialize all modules
        initDailyHub();
        initDashboard();
        initQuranReader();
        initKhatmaDashboard();
        initPrayerDashboard();
        initAICompanion();
        initMoodCheck();
        initAchievements();
        initProfile();
        initAdhkarCenter();
        initHadithCenter();
        initTasbeehCounter();
        initWorshipTracker();
        initDailyChallenges();
        initFavorites();
        initReadingHistory();
        initActivityTimeline();
        initAnalytics();
        initSettings();
        initSearchCenter();
        initNotifications();
        initHelp();
        initAbout();
        initAudioPlayer();
        initAdminDashboard();
        
        debugLog('All modules initialized');
    } catch (error) {
        debugLog('ERROR initializing app: ' + error.message);
        console.error('Initialization error:', error);
    } finally {
        // GUARANTEED: Hide loading screen regardless of errors
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.remove('active');
            loadingScreen.style.display = 'none';
        }
        
        // Show daily hub as default screen
        const dailyHub = document.getElementById('daily-hub');
        if (dailyHub) {
            dailyHub.classList.add('active');
        }
        
        debugLog('App initialization complete');
    }
});

// Telegram WebApp Initialization
function initTelegramWebApp() {
    try {
        // Expand the webapp to full height
        tg.expand();
        
        // Set theme colors based on Telegram theme
        if (tg.themeParams) {
            syncTelegramTheme();
            
            // Listen for theme changes
            tg.onEvent('themeChanged', syncTelegramTheme);
        }
        
        // Setup back button
        tg.BackButton.onClick(() => {
            navigateToScreen('dashboard');
        });
        
        // Setup main button with context
        updateMainButtonContext('dashboard');
        
        // Enable haptic feedback
        tg.HapticFeedback.impactOccurred('light');
    } catch (error) {
        console.error('Error initializing Telegram WebApp:', error);
    }
}

function updateMainButtonContext(screen) {
    try {
        const buttonActions = {
            'quran-reader': { text: 'حفظ الآية', action: 'bookmark_ayah' },
            'adhkar-center': { text: 'إكمال الأذكار', action: 'complete_adhkar' },
            'tasbeeh-counter': { text: 'حفظ التسبيح', action: 'save_tasbeeh' },
            'hadith-center': { text: 'نسخ الحديث', action: 'copy_hadith' },
            'ai-companion': { text: 'إرسال السؤال', action: 'send_question' },
            'worship-tracker': { text: 'حفظ التقدم', action: 'save_progress' },
            'daily-challenges': { text: 'إكمال التحدي', action: 'complete_challenge' },
            'favorites': { text: 'إزالة المفضلة', action: 'remove_favorite' },
            'analytics': { text: 'تصدير التقرير', action: 'export_report' },
            'settings': { text: 'حفظ الإعدادات', action: 'save_settings' }
        };
        
        const action = buttonActions[screen];
        
        if (action) {
            tg.MainButton.setText(action.text);
            tg.MainButton.show();
            
            // Remove previous click handler
            tg.MainButton.offClick();
            
            // Add new click handler
            tg.MainButton.onClick(() => {
                handleMainButtonAction(action.action);
            });
        } else {
            tg.MainButton.hide();
        }
    } catch (error) {
        console.error('Error updating main button context:', error);
    }
}

function handleMainButtonAction(action) {
    try {
        switch (action) {
            case 'bookmark_ayah':
                tg.showAlert('تم حفظ الآية');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'complete_adhkar':
                tg.showAlert('تم إكمال الأذكار');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'save_tasbeeh':
                tg.showAlert('تم حفظ التسبيح');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'copy_hadith':
                tg.showAlert('تم نسخ الحديث');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'send_question':
                tg.showAlert('تم إرسال السؤال');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'save_progress':
                tg.showAlert('تم حفظ التقدم');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'complete_challenge':
                tg.showAlert('تم إكمال التحدي');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'remove_favorite':
                tg.showAlert('تم إزالة المفضلة');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'export_report':
                tg.showAlert('تم تصدير التقرير');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'save_settings':
                tg.showAlert('تم حفظ الإعدادات');
                tg.HapticFeedback.notificationOccurred('success');
                break;
            default:
                tg.sendData(action);
        }
    } catch (error) {
        console.error('Error handling main button action:', error);
    }
}

function syncTelegramTheme() {
    try {
        const themeParams = tg.themeParams;
        
        if (themeParams) {
            // Sync background color
            if (themeParams.bg_color) {
                document.documentElement.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
                document.documentElement.style.setProperty('--bg-color', themeParams.bg_color);
            }
            
            // Sync text color
            if (themeParams.text_color) {
                document.documentElement.style.setProperty('--tg-theme-text-color', themeParams.text_color);
                document.documentElement.style.setProperty('--text-color', themeParams.text_color);
            }
            
            // Sync hint color
            if (themeParams.hint_color) {
                document.documentElement.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
                document.documentElement.style.setProperty('--text-light', themeParams.hint_color);
            }
            
            // Sync link color
            if (themeParams.link_color) {
                document.documentElement.style.setProperty('--tg-theme-link-color', themeParams.link_color);
                document.documentElement.style.setProperty('--primary-color', themeParams.link_color);
            }
            
            // Sync button color
            if (themeParams.button_color) {
                document.documentElement.style.setProperty('--tg-theme-button-color', themeParams.button_color);
            }
            
            // Sync button text color
            if (themeParams.button_text_color) {
                document.documentElement.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
            }
            
            // Check for dark mode
            const isDark = themeParams.bg_color && isColorDark(themeParams.bg_color);
            if (isDark) {
                document.documentElement.classList.add('dark-theme');
            } else {
                document.documentElement.classList.remove('dark-theme');
            }
            
            // Cache theme settings
            cacheData('theme', {
                bg_color: themeParams.bg_color,
                text_color: themeParams.text_color,
                hint_color: themeParams.hint_color,
                link_color: themeParams.link_color,
                is_dark: isDark
            });
        }
    } catch (error) {
        console.error('Error syncing Telegram theme:', error);
    }
}

function isColorDark(color) {
    try {
        // Convert hex to RGB
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        // Calculate luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        
        return luminance < 0.5;
    } catch (error) {
        console.error('Error checking if color is dark:', error);
        return false;
    }
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
    if (screenId === 'dashboard' || screenId === 'daily-hub') {
        tg.BackButton.hide();
    } else {
        tg.BackButton.show();
    }
    
    // Update main button context
    updateMainButtonContext(screenId);
}

function navigateToModule(module) {
    const moduleScreens = {
        'quran': 'quran-reader',
        'prayer': 'prayer-dashboard',
        'adhkar': 'adhkar-center',
        'hadith': 'hadith-center',
        'ai': 'ai-companion',
        'favorites': 'favorites',
        'tasbeeh': 'tasbeeh-counter',
        'worship': 'worship-tracker',
        'challenges': 'daily-challenges',
        'analytics': 'analytics',
        'search': 'search-center'
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
    initMoodSelector();
    updateStreakTracker();
    updatePrayerProgressRing();
}

function updateDateDisplay() {
    try {
        const now = new Date();
        
        // Gregorian date
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const arabicDate = now.toLocaleDateString('ar-SA', options);
        const dateDisplay = document.getElementById('date-display');
        if (dateDisplay) dateDisplay.textContent = arabicDate;
        
        // Hijri date calculation
        const hijriDate = calculateHijriDate(now);
        const hijriDisplay = document.getElementById('hijri-date');
        if (hijriDisplay) hijriDisplay.textContent = hijriDate;
        
        const gregorianDisplay = document.getElementById('gregorian-date');
        if (gregorianDisplay) gregorianDisplay.textContent = arabicDate;
        
        // Check for special Islamic events
        checkIslamicEvents(hijriDate);
    } catch (error) {
        console.error('Error updating date display:', error);
    }
}

function calculateHijriDate(date) {
    // Simplified Hijri date calculation
    // In production, use a proper library like hijri-date
    const gregorianDate = new Date(date);
    const islamicEpoch = new Date(622, 6, 16); // July 16, 622 CE
    const diffTime = gregorianDate.getTime() - islamicEpoch.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const hijriYear = Math.floor(diffDays / 354.36667) + 1;
    const remainingDays = diffDays % 354.36667;
    const hijriMonth = Math.floor(remainingDays / 29.5) + 1;
    const hijriDay = Math.floor(remainingDays % 29.5) + 1;
    
    const hijriMonths = [
        'محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 'جمادى الآخرة',
        'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'
    ];
    
    return `${hijriDay} ${hijriMonths[hijriMonth - 1]} ${hijriYear}`;
}

function checkIslamicEvents(hijriDate) {
    // Check for special Islamic events
    const events = {
        'رمضان': 'شهر الصيام',
        'شوال': 'عيد الفطر',
        'ذو الحجة': 'عيد الأضحى',
        'محرم': 'رأس السنة الهجرية'
    };
    
    for (const [month, event] of Object.entries(events)) {
        if (hijriDate.includes(month)) {
            // Show event notification
            showEventNotification(event);
            break;
        }
    }
}

function showEventNotification(event) {
    try {
        // Check if notification already shown today
        const today = new Date().toDateString();
        const lastNotification = localStorage.getItem('lastEventNotification');
        
        if (lastNotification !== today) {
            tg.showAlert(`🎉 ${event}`);
            localStorage.setItem('lastEventNotification', today);
        }
    } catch (error) {
        console.error('Error showing event notification:', error);
    }
}

function loadDailyContent() {
    try {
        // In production, this would fetch from API
        // For now, use inline fallback data for local testing
        const dailyContent = {
            morningMessage: 'ابدأ يومك بذكر الله واستعن به على أمورك',
            ayah: '﴿وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا﴾',
            ayahReference: 'سورة الطلاق: 2-3',
            wisdom: 'الصبر مفتاح الفرج، ومن يصبر يظفر',
            challenge: 'اقرأ 5 صفحات من القرآن اليوم',
            duaa: 'اللهم إني أسألك العفو والعافية في ديني ودنياي وأهلي ومالي',
            hadith: 'من سلك طريقاً يلتمس فيه علماً سهل الله له به طريقاً إلى الجنة'
        };
        
        const morningMsg = document.getElementById('morning-message');
        const ayahDay = document.getElementById('ayah-day');
        const ayahRef = document.querySelector('.ayah-day .reference');
        const wisdom = document.getElementById('wisdom');
        const challenge = document.getElementById('daily-challenge');
        const duaa = document.getElementById('duaa');
        const hadith = document.getElementById('hadith');
        
        if (morningMsg) morningMsg.textContent = dailyContent.morningMessage;
        if (ayahDay) ayahDay.textContent = dailyContent.ayah;
        if (ayahRef) ayahRef.textContent = dailyContent.ayahReference;
        if (wisdom) wisdom.textContent = dailyContent.wisdom;
        if (challenge) challenge.textContent = dailyContent.challenge;
        if (duaa) duaa.textContent = dailyContent.duaa;
        if (hadith) hadith.textContent = dailyContent.hadith;
    } catch (error) {
        console.error('Error loading daily content:', error);
        // Fallback to empty state if elements don't exist
    }
}

function startPrayerCountdown() {
    try {
        // Calculate prayer times based on current time
        const now = new Date();
        const currentHours = now.getHours();
        const currentMinutes = now.getMinutes();
        const currentTimeInMinutes = currentHours * 60 + currentMinutes;
        
        // Prayer times (in minutes from midnight) - example times for Cairo
        // In production, these should be calculated based on location and date
        const prayerTimes = {
            fajr: 4 * 60 + 30,      // 4:30 AM
            dhuhr: 12 * 60 + 30,    // 12:30 PM
            asr: 15 * 60 + 30,      // 3:30 PM
            maghrib: 18 * 60 + 45,  // 6:45 PM
            isha: 20 * 60 + 0       // 8:00 PM
        };
        
        const prayerNames = {
            fajr: 'الفجر',
            dhuhr: 'الظهر',
            asr: 'العصر',
            maghrib: 'المغرب',
            isha: 'العشاء'
        };
        
        // Find next prayer
        let nextPrayer = null;
        let nextPrayerTime = null;
        
        for (const [prayer, time] of Object.entries(prayerTimes)) {
            if (time > currentTimeInMinutes) {
                nextPrayer = prayer;
                nextPrayerTime = time;
                break;
            }
        }
        
        // If no prayer found today, next prayer is Fajr tomorrow
        if (!nextPrayer) {
            nextPrayer = 'fajr';
            nextPrayerTime = prayerTimes.fajr + 24 * 60; // Add 24 hours for tomorrow
        }
        
        // Calculate countdown
        let countdownSeconds = (nextPrayerTime - currentTimeInMinutes) * 60;
        
        // Update UI
        const nextPrayerEl = document.getElementById('next-prayer-name');
        const nextPrayerTimeEl = document.getElementById('next-prayer-time');
        const dashboardPrayerEl = document.getElementById('dashboard-prayer');
        
        if (nextPrayerEl) nextPrayerEl.textContent = prayerNames[nextPrayer];
        if (nextPrayerTimeEl) {
            const prayerHour = Math.floor(nextPrayerTime / 60);
            const prayerMinute = nextPrayerTime % 60;
            nextPrayerTimeEl.textContent = `${prayerHour.toString().padStart(2, '0')}:${prayerMinute.toString().padStart(2, '0')}`;
        }
        if (dashboardPrayerEl) {
            const prayerHour = Math.floor(nextPrayerTime / 60);
            const prayerMinute = nextPrayerTime % 60;
            dashboardPrayerEl.textContent = `${prayerNames[nextPrayer]} - ${prayerHour.toString().padStart(2, '0')}:${prayerMinute.toString().padStart(2, '0')}`;
        }
        
        // Update countdown every second
        setInterval(() => {
            if (countdownSeconds > 0) {
                countdownSeconds--;
                const hours = Math.floor(countdownSeconds / 3600);
                const minutes = Math.floor((countdownSeconds % 3600) / 60);
                const seconds = countdownSeconds % 60;
                
                const countdownEl = document.getElementById('prayer-countdown');
                if (countdownEl) {
                    countdownEl.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }
                
                // Update progress ring
                updatePrayerProgressRing(countdownSeconds);
            } else {
                // Prayer time reached, recalculate
                startPrayerCountdown();
            }
        }, 1000);
    } catch (error) {
        console.error('Error starting prayer countdown:', error);
    }
}

function initMoodSelector() {
    try {
        document.querySelectorAll('.mood-chip').forEach(chip => {
            chip.addEventListener('click', function() {
                const mood = this.dataset.mood;
                
                // Update active state
                document.querySelectorAll('.mood-chip').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                
                // Show mood-based guidance
                showMoodGuidance(mood);
                
                tg.HapticFeedback.impactOccurred('light');
            });
        });
    } catch (error) {
        console.error('Error initializing mood selector:', error);
    }
}

function showMoodGuidance(mood) {
    const guidance = {
        grateful: {
            ayah: '﴿وَإِن تَعُدُّوا نِعْمَتَ اللَّهِ لَا تُحْصُوهَا﴾',
            reference: 'إبراهيم: 34',
            dua: 'اللهم لك الحمد كما ينبغي لجلال وجهك وعظيم سلطانك'
        },
        anxious: {
            ayah: '﴿أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ﴾',
            reference: 'الرعد: 28',
            dua: 'اللهم إني أعوذ بك من الهم والحزن'
        },
        sad: {
            ayah: '﴿فَإِنَّ مَعَ الْعُسْرِ يُسْرًا﴾',
            reference: 'الشرح: 5',
            dua: 'اللهم اجعل ما أصابني تكفيراً لسيئاتي'
        },
        seeking: {
            ayah: '﴿وَيَهْدِيَكَ إِلَى صِرَاطٍ مُّسْتَقِيمٍ﴾',
            reference: 'الفاتحة: 6',
            dua: 'اللهم علمني ما ينفعني وانفعني بما علمتني'
        }
    };
    
    const moodGuidance = guidance[mood];
    if (moodGuidance) {
        tg.showAlert(`${moodGuidance.ayah}\n\n${moodGuidance.reference}\n\n${moodGuidance.dua}`);
    }
}

function updateStreakTracker() {
    try {
        // In production, this would fetch from API
        const streakDays = 7;
        const streakEl = document.getElementById('streak-days');
        if (streakEl) streakEl.textContent = streakDays;
    } catch (error) {
        console.error('Error updating streak tracker:', error);
    }
}

function updatePrayerProgressRing(countdownSeconds) {
    try {
        const progressRing = document.querySelector('.progress-ring-fill');
        if (progressRing) {
            // Calculate progress based on countdown
            // Assume average interval between prayers is about 4 hours (14400 seconds)
            const circumference = 2 * Math.PI * 35; // r=35
            const maxInterval = 14400; // 4 hours in seconds
            const progress = Math.max(0, Math.min(1, countdownSeconds / maxInterval));
            const offset = circumference * (1 - progress);
            progressRing.style.strokeDashoffset = offset;
        }
    } catch (error) {
        console.error('Error updating prayer progress ring:', error);
    }
}

// Dashboard Module
function initDashboard() {
    loadDashboardStats();
}

function loadDashboardStats() {
    try {
        // In production, this would fetch from API
        const stats = {
            quranPages: 156,
            khatmaProgress: 65,
            streak: 7,
            badges: 2
        };
        
        const quranPagesEl = document.getElementById('quran-pages');
        const khatmaProgressEl = document.getElementById('khatma-progress');
        const streakEl = document.getElementById('streak-count');
        const badgesEl = document.getElementById('badge-count');
        
        if (quranPagesEl) quranPagesEl.textContent = stats.quranPages;
        if (khatmaProgressEl) khatmaProgressEl.textContent = `${stats.khatmaProgress}%`;
        if (streakEl) streakEl.textContent = stats.streak;
        if (badgesEl) badgesEl.textContent = stats.badges;
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Quran Reader Module
function initQuranReader() {
    try {
        initThemeToggle();
        initFontSizeControl();
        initPageNavigation();
        initReaderActions();
        initReaderModeToggle();
        initSurahMode();
        loadQuranPage(2);
    } catch (error) {
        console.error('Error initializing Quran reader:', error);
    }
}

function initReaderModeToggle() {
    try {
        const modeBtns = document.querySelectorAll('.mode-btn');
        modeBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const mode = this.dataset.mode;
                
                // Update active state
                modeBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Toggle modes
                const pageMode = document.getElementById('page-mode');
                const surahMode = document.getElementById('surah-mode');
                const pageNavigation = document.getElementById('page-navigation');
                
                if (mode === 'page') {
                    pageMode.classList.remove('hidden');
                    surahMode.classList.remove('active');
                    pageNavigation.style.display = 'flex';
                } else {
                    pageMode.classList.add('hidden');
                    surahMode.classList.add('active');
                    pageNavigation.style.display = 'none';
                }
                
                tg.HapticFeedback.impactOccurred('light');
            });
        });
    } catch (error) {
        console.error('Error initializing reader mode toggle:', error);
    }
}

function initSurahMode() {
    try {
        debugLog('Initializing surah mode...');
        
        // Load surah list from quran.json
        loadSurahList();
        
        // Initialize search functionality
        const surahSearch = document.getElementById('surah-search');
        if (surahSearch) {
            surahSearch.addEventListener('input', function() {
                filterSurahs(this.value);
            });
        }
        
        const surahSelect = document.getElementById('surah-select');
        if (surahSelect) {
            surahSelect.addEventListener('change', function() {
                loadSurah(this.value);
            });
        }
        
        const prevAyah = document.getElementById('prev-ayah');
        const nextAyah = document.getElementById('next-ayah');
        
        if (prevAyah) {
            prevAyah.addEventListener('click', navigateToPreviousAyah);
        }
        
        if (nextAyah) {
            nextAyah.addEventListener('click', navigateToNextAyah);
        }
        
        // Load initial surah
        loadSurah(1);
        
        debugLog('Surah mode initialized successfully');
    } catch (error) {
        debugLog('ERROR in initSurahMode: ' + error.message);
        console.error('Error initializing surah mode:', error);
    }
}

let quranData = null;

async function loadSurahList() {
    try {
        debugLog('Loading surah list...');
        
        const response = await fetch('assets/data/quran.json');
        quranData = await response.json();
        
        const surahSelect = document.getElementById('surah-select');
        if (surahSelect && quranData) {
            surahSelect.innerHTML = '';
            
            quranData.forEach(surah => {
                const option = document.createElement('option');
                option.value = surah.id;
                option.textContent = `${surah.id}. ${surah.name}`;
                surahSelect.appendChild(option);
            });
            
            debugLog('Surah list loaded successfully: ' + quranData.length + ' surahs');
        }
    } catch (error) {
        debugLog('ERROR loading surah list: ' + error.message);
        console.error('Error loading surah list:', error);
        
        // Fallback to hardcoded list
        loadFallbackSurahList();
    }
}

function loadFallbackSurahList() {
    debugLog('Loading fallback surah list...');
    
    const surahNames = {
        1: 'سورة الفاتحة',
        2: 'سورة البقرة',
        3: 'سورة آل عمران',
        4: 'سورة النساء',
        5: 'سورة المائدة',
        6: 'سورة الأنعام',
        7: 'سورة الأعراف',
        8: 'سورة الأنفال',
        9: 'سورة التوبة',
        10: 'سورة يونس',
        11: 'سورة هود',
        12: 'سورة يوسف',
        13: 'سورة الرعد',
        14: 'سورة إبراهيم',
        15: 'سورة الحجر',
        16: 'سورة النحل',
        17: 'سورة الإسراء',
        18: 'سورة الكهف',
        19: 'سورة مريم',
        20: 'سورة طه',
        36: 'سورة يس',
        55: 'سورة الرحمن',
        67: 'سورة الملك',
        112: 'سورة الإخلاص',
        113: 'سورة الفلق',
        114: 'سورة الناس'
    };
    
    const surahSelect = document.getElementById('surah-select');
    if (surahSelect) {
        surahSelect.innerHTML = '';
        
        Object.keys(surahNames).sort((a, b) => a - b).forEach(id => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = surahNames[id];
            surahSelect.appendChild(option);
        });
        
        debugLog('Fallback surah list loaded');
    }
}

function filterSurahs(searchTerm) {
    try {
        const surahSelect = document.getElementById('surah-select');
        if (!surahSelect) return;
        
        const options = surahSelect.querySelectorAll('option');
        const term = searchTerm.toLowerCase();
        
        options.forEach(option => {
            const text = option.textContent.toLowerCase();
            option.style.display = text.includes(term) ? 'block' : 'none';
        });
    } catch (error) {
        debugLog('ERROR filtering surahs: ' + error.message);
        console.error('Error filtering surahs:', error);
    }
}

let currentAyah = 1;
let totalAyahs = 7;
let currentSurahId = 1;

function loadSurah(surahId) {
    try {
        debugLog('Loading surah: ' + surahId);
        currentSurahId = parseInt(surahId);
        
        let surahData = null;
        
        // Try to load from quranData first
        if (quranData) {
            surahData = quranData.find(s => s.id === currentSurahId);
        }
        
        // Fallback to hardcoded data
        if (!surahData) {
            const surahNames = {
                1: 'الفاتحة',
                2: 'البقرة',
                3: 'آل عمران',
                4: 'النساء',
                5: 'المائدة',
                18: 'الكهف',
                36: 'يس',
                55: 'الرحمن',
                67: 'الملك',
                112: 'الإخلاص',
                113: 'الفلق',
                114: 'الناس'
            };
            
            const surahAyahs = {
                1: 7,
                2: 286,
                3: 200,
                4: 176,
                5: 120,
                18: 110,
                36: 83,
                55: 78,
                67: 30,
                112: 4,
                113: 5,
                114: 6
            };
            
            surahData = {
                id: currentSurahId,
                name: surahNames[currentSurahId] || 'سورة ' + currentSurahId,
                total_verses: surahAyahs[currentSurahId] || 100,
                verses: []
            };
        }
        
        // Update surah info
        const surahInfo = document.querySelector('.surah-info h2');
        if (surahInfo) {
            surahInfo.textContent = surahData.name;
        }
        
        // Reset ayah navigation
        currentAyah = 1;
        totalAyahs = surahData.total_verses;
        
        // Display surah content
        const surahContent = document.getElementById('surah-content');
        if (surahContent && surahData.verses && surahData.verses.length > 0) {
            surahContent.innerHTML = '';
            
            surahData.verses.forEach((ayah, index) => {
                const ayahDiv = document.createElement('div');
                ayahDiv.className = 'ayah-text';
                ayahDiv.innerHTML = `
                    <span class="ayah-number">${ayah.id}</span>
                    <span class="ayah-content">${ayah.text}</span>
                `;
                surahContent.appendChild(ayahDiv);
            });
            
            debugLog('Surah loaded successfully: ' + surahData.name + ' (' + surahData.verses.length + ' verses)');
        } else {
            surahContent.innerHTML = '<p class="placeholder">جاري تحميل السورة...</p>';
            debugLog('Surah verses not available, showing placeholder');
        }
        
        // Update ayah indicator
        updateAyahIndicator();
        
        safeHapticFeedback('light');
    } catch (error) {
        debugLog('ERROR loading surah: ' + error.message);
        console.error('Error loading surah:', error);
    }
}

function updateAyahIndicator() {
    try {
        const indicator = document.getElementById('ayah-indicator');
        if (indicator) {
            indicator.textContent = `آية ${currentAyah} / ${totalAyahs}`;
        }
    } catch (error) {
        debugLog('ERROR updating ayah indicator: ' + error.message);
        console.error('Error updating ayah indicator:', error);
    }
}

function navigateToPreviousAyah() {
    if (currentAyah > 1) {
        currentAyah--;
        updateAyahIndicator();
        scrollToAyah(currentAyah);
        safeHapticFeedback('light');
    }
}

function navigateToNextAyah() {
    if (currentAyah < totalAyahs) {
        currentAyah++;
        updateAyahIndicator();
        scrollToAyah(currentAyah);
        safeHapticFeedback('light');
    }
}

function scrollToAyah(ayahNumber) {
    const ayahElements = document.querySelectorAll('.ayah-text');
    if (ayahElements[ayahNumber - 1]) {
        ayahElements[ayahNumber - 1].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function initThemeToggle() {
    try {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', newTheme);
                this.textContent = newTheme === 'dark' ? '☀️' : '🌙';
                safeHapticFeedback('light');
            });
        }
    } catch (error) {
        debugLog('ERROR in initThemeToggle: ' + error.message);
        console.error('Error initializing theme toggle:', error);
    }
}

function initFontSizeControl() {
    try {
        const fontSizeBtn = document.getElementById('font-size');
        if (fontSizeBtn) {
            let currentSize = 1.3;
            
            fontSizeBtn.addEventListener('click', function() {
                currentSize = currentSize >= 1.8 ? 1.1 : currentSize + 0.1;
                const quranText = document.getElementById('quran-text');
                if (quranText) {
                    quranText.style.fontSize = `${currentSize}rem`;
                }
                safeHapticFeedback('light');
            });
        }
    } catch (error) {
        debugLog('ERROR in initFontSizeControl: ' + error.message);
        console.error('Error initializing font size control:', error);
    }
}

// Page Navigation
let currentPage = 1;
const totalPages = 604;

function initPageNavigation() {
    try {
        const prevPageBtn = document.getElementById('prev-page');
        const nextPageBtn = document.getElementById('next-page');
        
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', function() {
                if (currentPage > 1) {
                    currentPage--;
                    loadQuranPage(currentPage);
                    safeHapticFeedback('light');
                }
            });
        }
        
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', function() {
                if (currentPage < totalPages) {
                    currentPage++;
                    loadQuranPage(currentPage);
                    safeHapticFeedback('light');
                }
            });
        }
        
        debugLog('Page navigation initialized successfully');
    } catch (error) {
        debugLog('ERROR in initPageNavigation: ' + error.message);
        console.error('Error initializing page navigation:', error);
    }
}

function initReaderActions() {
    try {
        const bookmarkBtn = document.getElementById('bookmark-btn');
        const tafseerBtn = document.getElementById('tafseer-btn');
        const audioBtn = document.getElementById('audio-btn');
        const wordByWordBtn = document.getElementById('word-by-word-btn');
        
        if (bookmarkBtn) {
            bookmarkBtn.addEventListener('click', bookmarkAyah);
        }
        
        if (tafseerBtn) {
            tafseerBtn.addEventListener('click', showTafseerOverlay);
        }
        
        if (audioBtn) {
            audioBtn.addEventListener('click', toggleAudio);
        }
        
        if (wordByWordBtn) {
            wordByWordBtn.addEventListener('click', showWordByWordOverlay);
        }
        
        // Close buttons
        const closeTafseer = document.getElementById('close-tafseer');
        if (closeTafseer) {
            closeTafseer.addEventListener('click', hideTafseerOverlay);
        }
        
        const closeWordByWord = document.getElementById('close-word-by-word');
        if (closeWordByWord) {
            closeWordByWord.addEventListener('click', hideWordByWordOverlay);
        }
    } catch (error) {
        console.error('Error initializing reader actions:', error);
    }
}

function bookmarkAyah() {
    try {
        // Show share options
        showShareOptions();
        tg.HapticFeedback.notificationOccurred('success');
    } catch (error) {
        console.error('Error bookmarking ayah:', error);
    }
}

function showShareOptions() {
    try {
        const shareOptions = [
            'مشاركة كصورة جميلة',
            'نسخ النص',
            'مشاركة على Telegram'
        ];
        
        tg.showAlert(`خيارات المشاركة:\n\n${shareOptions.map((o, i) => `${i + 1}. ${o}`).join('\n')}`);
    } catch (error) {
        console.error('Error showing share options:', error);
    }
}

function toggleAudio() {
    try {
        // Show reciter selection
        showReciterSelection();
        tg.HapticFeedback.impactOccurred('light');
    } catch (error) {
        console.error('Error toggling audio:', error);
    }
}

function showReciterSelection() {
    try {
        const reciters = [
            { id: 'mishary', name: 'مشاري العفاسي' },
            { id: 'abdulbasit', name: 'عبد الباسط عبد الصمد' },
            { id: 'minshawi', name: 'محمد صديق المنشاوي' },
            { id: 'husary', name: 'محمود خليل الحصري' },
            { id: 'sudais', name: 'عبد الرحمن السديس' }
        ];
        
        let reciterOptions = reciters.map((r, i) => `${i + 1}. ${r.name}`).join('\n');
        tg.showAlert(`اختر القارئ:\n\n${reciterOptions}`);
    } catch (error) {
        console.error('Error showing reciter selection:', error);
    }
}

function showTafseerOverlay() {
    try {
        const tafseerOverlay = document.getElementById('tafseer-overlay');
        const tafseerText = document.getElementById('tafseer-text');
        
        if (tafseerOverlay) {
            tafseerOverlay.classList.add('active');
            
            // Load tafseer content
            if (tafseerText) {
                tafseerText.innerHTML = `
                    <p>تفسير الآية من تفسير ابن كثير:</p>
                    <p>هذه الآية تتحدث عن التقوى والخوف من الله، وتشير إلى أن من يتق الله يجعل له مخرجاً من كل ضيق وصعوبة.</p>
                    <p>والمخرج هنا يشمل المخرج من كل كرب وهم، والمخرج من كل ما يضيق على العبد من أمور دنياه وأخراه.</p>
                `;
            }
            
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch (error) {
        console.error('Error showing tafseer overlay:', error);
    }
}

function hideTafseerOverlay() {
    try {
        const tafseerOverlay = document.getElementById('tafseer-overlay');
        if (tafseerOverlay) {
            tafseerOverlay.classList.remove('active');
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch (error) {
        console.error('Error hiding tafseer overlay:', error);
    }
}

function showWordByWordOverlay() {
    try {
        const wordByWordOverlay = document.getElementById('word-by-word-overlay');
        const wordByWordContent = document.getElementById('word-by-word-content');
        
        if (wordByWordOverlay) {
            wordByWordOverlay.classList.add('active');
            
            // Load word-by-word content
            if (wordByWordContent) {
                wordByWordContent.innerHTML = `
                    <div class="word-breakdown">
                        <div class="word-item">
                            <span class="word-arabic">وَمَن</span>
                            <span class="word-translation">And whoever</span>
                            <span class="word-meaning">من + ومن</span>
                        </div>
                        <div class="word-item">
                            <span class="word-arabic">يَتَّقِ</span>
                            <span class="word-translation">is conscious of</span>
                            <span class="word-meaning">يخاف ويحترم</span>
                        </div>
                        <div class="word-item">
                            <span class="word-arabic">اللَّهَ</span>
                            <span class="word-translation">Allah</span>
                            <span class="word-meaning">الله سبحانه</span>
                        </div>
                        <div class="word-item">
                            <span class="word-arabic">يَجْعَل</span>
                            <span class="word-translation">He makes</span>
                            <span class="word-meaning">يخلق وييسر</span>
                        </div>
                        <div class="word-item">
                            <span class="word-arabic">لَّهُ</span>
                            <span class="word-translation">for him</span>
                            <span class="word-meaning">له وحده</span>
                        </div>
                        <div class="word-item">
                            <span class="word-arabic">مَخْرَجًا</span>
                            <span class="word-translation">a way out</span>
                            <span class="word-meaning">مخرجاً من الضيق</span>
                        </div>
                    </div>
                `;
            }
            
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch (error) {
        console.error('Error showing word-by-word overlay:', error);
    }
}

function hideWordByWordOverlay() {
    try {
        const wordByWordOverlay = document.getElementById('word-by-word-overlay');
        if (wordByWordOverlay) {
            wordByWordOverlay.classList.remove('active');
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch (error) {
        console.error('Error hiding word-by-word overlay:', error);
    }
}

function loadQuranPage(pageNumber) {
    try {
        debugLog('Loading page: ' + pageNumber);
        
        // Update page indicator
        const pageIndicatorEl = document.getElementById('page-indicator');
        if (pageIndicatorEl) pageIndicatorEl.textContent = `صفحة ${pageNumber} / ${totalPages}`;
        
        const currentPageEl = document.getElementById('current-page');
        if (currentPageEl) currentPageEl.textContent = `صفحة ${pageNumber}`;
        
        // Get quran text container
        const quranTextEl = document.getElementById('quran-text');
        if (!quranTextEl) {
            debugLog('ERROR: quran-text element not found');
            return;
        }
        
        // Clear existing content
        quranTextEl.innerHTML = '';
        
        // Try to load from quranData
        if (quranData && quranData.length > 0) {
            // Calculate which surah to show based on page number
            // This is a simplified mapping - in production, you'd use proper page-to-surah mapping
            const surahIndex = Math.min(Math.floor((pageNumber - 1) / 5), quranData.length - 1);
            const surah = quranData[surahIndex];
            
            if (surah && surah.verses && surah.verses.length > 0) {
                // Update surah name header
                const surahInfo = document.querySelector('.surah-info h2');
                if (surahInfo) surahInfo.textContent = surah.name;
                
                // Display verses
                surah.verses.forEach((ayah, index) => {
                    const ayahDiv = document.createElement('div');
                    ayahDiv.className = 'ayah-text';
                    ayahDiv.innerHTML = `
                        <span class="ayah-number">${ayah.id}</span>
                        <span class="ayah-content">${ayah.text}</span>
                    `;
                    quranTextEl.appendChild(ayahDiv);
                });
                
                debugLog('Loaded surah: ' + surah.name + ' for page ' + pageNumber);
            } else {
                quranTextEl.innerHTML = '<p class="placeholder">جاري تحميل الصفحة...</p>';
                debugLog('No verses found for page ' + pageNumber);
            }
        } else {
            // Fallback to placeholder
            quranTextEl.innerHTML = `
                <div class="page-placeholder">
                    <p>صفحة ${pageNumber}</p>
                    <p>جاري تحميل محتوى الصفحة...</p>
                </div>
            `;
            debugLog('quranData not available, showing placeholder');
        }
        
        safeHapticFeedback('light');
    } catch (error) {
        debugLog('ERROR loading page: ' + error.message);
        console.error('Error loading page:', error);
    }
}

// Khatma Dashboard Module
function initKhatmaDashboard() {
    try {
        loadKhatmaProgress();
        calculateDailyQuota();
        initKhatmaSettings();
    } catch (error) {
        console.error('Error initializing Khatma dashboard:', error);
    }
}

function calculateDailyQuota() {
    try {
        const currentPage = 393; // Example: page 393 out of 604
        const totalPages = 604;
        const pagesRemaining = totalPages - currentPage;
        
        // Calculate based on different completion goals
        const goals = {
            '30_days': Math.ceil(pagesRemaining / 30),
            '60_days': Math.ceil(pagesRemaining / 60),
            '90_days': Math.ceil(pagesRemaining / 90),
            'ramadan': Math.ceil(pagesRemaining / 30) // For Ramadan
        };
        
        const dailyQuotaEl = document.getElementById('daily-quota');
        if (dailyQuotaEl) {
            dailyQuotaEl.innerHTML = `
                <div class="quota-options">
                    <div class="quota-option">
                        <span class="quota-label">30 يوم:</span>
                        <span class="quota-value">${goals['30_days']} صفحة</span>
                    </div>
                    <div class="quota-option">
                        <span class="quota-label">60 يوم:</span>
                        <span class="quota-value">${goals['60_days']} صفحة</span>
                    </div>
                    <div class="quota-option">
                        <span class="quota-label">90 يوم:</span>
                        <span class="quota-value">${goals['90_days']} صفحة</span>
                    </div>
                </div>
            `;
        }
        
        // Cache the calculation
        cacheData('khatmaQuota', goals);
    } catch (error) {
        console.error('Error calculating daily quota:', error);
    }
}

function initKhatmaSettings() {
    try {
        // Add goal selector to Khatma dashboard
        const khatmaContent = document.querySelector('.khatma-content');
        if (khatmaContent) {
            const settingsSection = document.createElement('div');
            settingsSection.className = 'khatma-settings';
            settingsSection.innerHTML = `
                <h3>إعدادات الختمة</h3>
                <div class="setting-item">
                    <label>الهدف الزمني:</label>
                    <select id="khatma-goal">
                        <option value="30">30 يوم</option>
                        <option value="60" selected>60 يوم</option>
                        <option value="90">90 يوم</option>
                        <option value="ramadan">رمضان</option>
                    </select>
                </div>
                <button class="action-btn" id="update-quota">تحديث الحصة</button>
            `;
            
            khatmaContent.appendChild(settingsSection);
            
            // Add event listener
            const updateBtn = document.getElementById('update-quota');
            if (updateBtn) {
                updateBtn.addEventListener('click', function() {
                    const goal = document.getElementById('khatma-goal').value;
                    updateQuotaBasedOnGoal(goal);
                });
            }
        }
    } catch (error) {
        console.error('Error initializing Khatma settings:', error);
    }
}

function updateQuotaBasedOnGoal(goal) {
    try {
        const quota = getCachedData('khatmaQuota');
        if (quota && quota[goal]) {
            tg.showAlert(`الحصة اليومية: ${quota[goal]} صفحة`);
            tg.HapticFeedback.notificationOccurred('success');
        }
    } catch (error) {
        console.error('Error updating quota based on goal:', error);
    }
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
    try {
        loadAchievements();
        initBadgeSystem();
        loadXPProgress();
    } catch (error) {
        console.error('Error initializing achievements:', error);
    }
}

function loadAchievements() {
    // In production, this would fetch from API
    const achievements = {
        totalPages: 156,
        streak: 7,
        tasbeeh: 234,
        challenges: 12
    };
    
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        if (badge.classList.contains('unlocked')) {
            badge.addEventListener('click', function() {
                showBadgeDetails(this);
            });
        }
    });
}

function initBadgeSystem() {
    try {
        const badges = [
            { id: 'first_khatma', name: 'أول ختمة', icon: '🥉', description: 'أكملت أول ختمة للقرآن', unlocked: true },
            { id: 'streak_7', name: 'أسبوع متواصل', icon: '🔥', description: 'أكملت 7 أيام متتالية', unlocked: true },
            { id: 'streak_30', name: 'شهر متواصل', icon: '💎', description: 'أكملت 30 يوماً متتالية', unlocked: false },
            { id: 'tasbeeh_1000', name: 'ألف تسبيحة', icon: '📿', description: 'سبحت 1000 مرة', unlocked: false },
            { id: 'quran_100', name: '100 صفحة', icon: '📖', description: 'قرأت 100 صفحة', unlocked: true },
            { id: 'prayer_master', name: 'إمام الصلاة', icon: '🕌', description: 'أديت الصلوات الخمس 30 يوماً', unlocked: false },
            { id: 'hadith_collector', name: 'جامع الأحاديث', icon: '📚', description: 'قرأت 50 حديثاً', unlocked: false },
            { id: 'community_hero', name: 'بطل المجتمع', icon: '🌟', description: 'أكملت 10 تحديات مجتمعية', unlocked: false }
        ];
        
        const badgesGrid = document.querySelector('.badges-grid');
        if (badgesGrid) {
            badgesGrid.innerHTML = badges.map(badge => `
                <div class="badge ${badge.unlocked ? 'unlocked' : 'locked'}" data-id="${badge.id}">
                    <div class="badge-icon">${badge.icon}</div>
                    <div class="badge-name">${badge.name}</div>
                    <div class="badge-description">${badge.description}</div>
                    ${!badge.unlocked ? '<div class="badge-lock">🔒</div>' : ''}
                </div>
            `).join('');
            
            // Add click events for unlocked badges
            document.querySelectorAll('.badge.unlocked').forEach(badge => {
                badge.addEventListener('click', function() {
                    const badgeId = this.dataset.id;
                    const badgeData = badges.find(b => b.id === badgeId);
                    showBadgeDetails(badgeData);
                });
            });
        }
        
        // Cache badges
        cacheData('badges', badges);
    } catch (error) {
        console.error('Error initializing badge system:', error);
    }
}

function showBadgeDetails(badge) {
    try {
        tg.showAlert(`${badge.icon} ${badge.name}\n\n${badge.description}`);
        tg.HapticFeedback.impactOccurred('light');
    } catch (error) {
        console.error('Error showing badge details:', error);
    }
}

function loadXPProgress() {
    try {
        const xpData = getCachedData('xpData') || {
            currentXP: 1250,
            level: 5,
            xpToNextLevel: 500,
            totalXP: 1250
        };
        
        const xpProgress = document.querySelector('.xp-progress');
        if (xpProgress) {
            xpProgress.innerHTML = `
                <div class="xp-header">
                    <span class="level-badge">المستوى ${xpData.level}</span>
                    <span class="xp-display">${xpData.currentXP} XP</span>
                </div>
                <div class="xp-bar">
                    <div class="xp-fill" style="width: ${(xpData.currentXP % 500) / 500 * 100}%"></div>
                </div>
                <div class="xp-info">
                    <span>${xpData.currentXP % 500} / ${xpData.xpToNextLevel} XP للمستوى التالي</span>
                </div>
                <div class="xp-rewards">
                    <h4>مكافآت المستوى ${xpData.level + 1}:</h4>
                    <ul>
                        <li>🎖️ شارة جديدة</li>
                        <li>⭐ 50 XP إضافية</li>
                        <li>🎨 سمة خاصة</li>
                    </ul>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading XP progress:', error);
    }
}

function awardXP(amount) {
    try {
        const xpData = getCachedData('xpData') || {
            currentXP: 0,
            level: 1,
            xpToNextLevel: 500,
            totalXP: 0
        };
        
        xpData.currentXP += amount;
        xpData.totalXP += amount;
        
        // Check for level up
        while (xpData.currentXP >= xpData.xpToNextLevel) {
            xpData.currentXP -= xpData.xpToNextLevel;
            xpData.level++;
            xpData.xpToNextLevel = Math.floor(xpData.xpToNextLevel * 1.5);
            
            tg.showAlert(`🎉 مبروك! وصلت للمستوى ${xpData.level}!`);
            tg.HapticFeedback.notificationOccurred('success');
        }
        
        cacheData('xpData', xpData);
        loadXPProgress();
    } catch (error) {
        console.error('Error awarding XP:', error);
    }
}

// Profile Module
function initProfile() {
    loadProfileData();
    initProfileActions();
}

function loadProfileData() {
    try {
        debugLog('Loading profile data...');
        
        // Get user data from Telegram WebApp SDK
        const telegramUser = tg.initDataUnsafe?.user;
        
        // Admin user IDs (in production, fetch from backend API)
        const adminUserIds = [6326713765]; // Replace with actual admin IDs
        
        // Check if user is admin
        const isAdmin = telegramUser && adminUserIds.includes(telegramUser.id);
        
        debugLog('User is admin: ' + isAdmin);
        
        // Show/hide admin section
        const adminSection = document.getElementById('admin-section');
        if (adminSection) {
            adminSection.style.display = isAdmin ? 'block' : 'none';
            debugLog('Admin section visibility set to: ' + (isAdmin ? 'visible' : 'hidden'));
        }
        
        // Show/hide admin nav button
        const adminNavBtn = document.querySelector('.nav-btn.admin-only');
        if (adminNavBtn) {
            adminNavBtn.style.display = isAdmin ? 'flex' : 'none';
            debugLog('Admin nav button visibility set to: ' + (isAdmin ? 'visible' : 'hidden'));
        }
        
        // Load profile data
        const profileData = {
            name: telegramUser?.first_name || 'المستخدم',
            username: telegramUser?.username ? '@' + telegramUser.username : '',
            userId: telegramUser?.id ? 'ID: ' + telegramUser.id : 'ID: 123456789',
            lastSurah: 'البقرة',
            lastDhikr: 'سبحان الله',
            streak: '7 أيام',
            khatmas: '2 ختمات',
            tasbeeh: '1,234',
            badges: '2 شارات'
        };
        
        // Set user avatar from Telegram photo if available
        if (telegramUser?.photo_url) {
            const userAvatar = document.getElementById('user-avatar');
            if (userAvatar) {
                userAvatar.style.backgroundImage = `url(${telegramUser.photo_url})`;
                userAvatar.style.backgroundSize = 'cover';
                userAvatar.style.backgroundPosition = 'center';
                userAvatar.textContent = '';
            }
        }
        
        // Update profile UI with null checks
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) userNameEl.textContent = profileData.name;
        
        const userUsernameEl = document.getElementById('user-username');
        if (userUsernameEl) userUsernameEl.textContent = profileData.username;
        
        const userIdEl = document.getElementById('user-id');
        if (userIdEl) userIdEl.textContent = profileData.userId;
        
        const profileStreakEl = document.getElementById('profile-streak');
        if (profileStreakEl) profileStreakEl.textContent = profileData.streak;
        
        const profileKhatmasEl = document.getElementById('profile-khatmas');
        if (profileKhatmasEl) profileKhatmasEl.textContent = profileData.khatmas;
        
        const profileTasbeehEl = document.getElementById('profile-tasbeeh');
        if (profileTasbeehEl) profileTasbeehEl.textContent = profileData.tasbeeh;
        
        const profileBadgesEl = document.getElementById('profile-badges');
        if (profileBadgesEl) profileBadgesEl.textContent = profileData.badges;
        
        debugLog('Profile data loaded successfully');
    } catch (error) {
        debugLog('ERROR loading profile data: ' + error.message);
        console.error('Error loading profile data:', error);
    }
}

function initProfileActions() {
    try {
        document.querySelectorAll('.profile-actions .action-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const screen = this.dataset.screen;
                const action = this.textContent;
                
                if (screen) {
                    navigateToScreen(screen);
                } else if (action === 'تسجيل الخروج') {
                    safeShowConfirm('هل أنت متأكد من تسجيل الخروج؟', (confirmed) => {
                        if (confirmed) {
                            tg.close();
                        }
                    });
                }
                
                safeHapticFeedback('light');
            });
        });
    } catch (error) {
        debugLog('ERROR in initProfileActions: ' + error.message);
        console.error('Error initializing profile actions:', error);
    }
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

// Adhkar Center Module
function initAdhkarCenter() {
    initAdhkarCategories();
    loadAdhkar('morning');
}

function initAdhkarCategories() {
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const category = this.dataset.category;
            
            // Update active state
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Load adhkar for category
            loadAdhkar(category);
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function loadAdhkar(category) {
    const adhkarData = {
        morning: [
            { text: 'أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ', count: 'مرة واحدة' },
            { text: 'اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا', count: 'مرة واحدة' },
            { text: 'سُبْحَانَ اللهِ وَبِحَمْدِهِ', count: '100 مرة' }
        ],
        evening: [
            { text: 'أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ', count: 'مرة واحدة' },
            { text: 'اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا', count: 'مرة واحدة' },
            { text: 'أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ', count: '3 مرات' }
        ],
        sleep: [
            { text: 'بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا', count: 'مرة واحدة' },
            { text: 'اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ', count: 'مرة واحدة' }
        ],
        travel: [
            { text: 'اللَّهُمَّ إِنَّا نَسْأَلُكَ فِي سَفَرِنَا', count: 'مرة واحدة' },
            { text: 'سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا', count: 'مرة واحدة' }
        ],
        prayer: [
            { text: 'سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ', count: 'مرة واحدة' },
            { text: 'اللَّهُمَّ اغْفِرْ لِي ذُنُوبِي', count: 'مرة واحدة' }
        ],
        general: [
            { text: 'سُبْحَانَ اللهِ', count: '33 مرة' },
            { text: 'الْحَمْدُ لِلَّهِ', count: '33 مرة' },
            { text: 'اللَّهُ أَكْبَرُ', count: '34 مرة' }
        ]
    };
    
    const adhkarList = document.getElementById('adhkar-list');
    const items = adhkarData[category] || [];
    
    adhkarList.innerHTML = items.map(item => `
        <div class="adhkar-item">
            <p class="adhkar-text">${item.text}</p>
            <span class="adhkar-count">${item.count}</span>
            <button class="copy-btn" onclick="copyToClipboard('${item.text}')">📋 نسخ</button>
        </div>
    `).join('');
}

// Hadith Center Module
function initHadithCenter() {
    initHadithCollections();
    initHadithSearch();
    loadHadiths('bukhari');
}

function initHadithCollections() {
    document.querySelectorAll('.collection-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const collection = this.dataset.collection;
            
            // Update active state
            document.querySelectorAll('.collection-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Load hadiths for collection
            loadHadiths(collection);
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function initHadithSearch() {
    const searchInput = document.getElementById('hadith-search');
    const searchBtn = document.querySelector('.search-bar .search-btn');
    
    searchBtn.addEventListener('click', () => searchHadith(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchHadith(searchInput.value);
    });
}

function searchHadith(query) {
    // In production, this would search in API
    tg.showAlert(`البحث عن: ${query}`);
}

function loadHadiths(collection) {
    const hadithData = {
        bukhari: [
            {
                text: 'إنما الأعمال بالنيات',
                narrator: 'عمر بن الخطاب',
                reference: 'صحيح البخاري 1',
                explanation: 'هذا الحديث يبين أن نية الإنسان هي المعيار في قبول الأعمال.'
            },
            {
                text: 'الدين النصيحة',
                narrator: 'تميم الداري',
                reference: 'صحيح البخاري 57',
                explanation: 'النصيحة هي أساس الدين، وتشمل نصيحة الله ورسوله والمسلمين.'
            }
        ],
        muslim: [
            {
                text: 'المسلم من سلم المسلمون من لسانه ويده',
                narrator: 'عبد الله بن عمرو',
                reference: 'صحيح مسلم 41',
                explanation: 'المسلم الحقيقي هو الذي لا يؤذي المسلمين بقول أو فعل.'
            }
        ]
    };

    const hadiths = hadithData[collection] || [];
    const hadithList = document.getElementById('hadith-list');

    hadithList.innerHTML = hadiths.map(hadith => `
        <div class="hadith-item">
            <p class="hadith-text">${hadith.text}</p>
            <p class="hadith-narrator">الراوي: ${hadith.narrator}</p>
            <p class="hadith-reference">${hadith.reference}</p>
            <p class="hadith-explanation">${hadith.explanation}</p>
            <div class="hadith-actions">
                <button class="action-btn copy-hadith" data-text="${hadith.text}">📋 نسخ</button>
                <button class="action-btn share-hadith" data-text="${hadith.text}">📤 مشاركة</button>
            </div>
        </div>
    `).join('');

    // Add event listeners for copy and share buttons
    document.querySelectorAll('.copy-hadith').forEach(btn => {
        btn.addEventListener('click', function() {
            copyHadith(this.dataset.text);
        });
    });

    document.querySelectorAll('.share-hadith').forEach(btn => {
        btn.addEventListener('click', function() {
            shareHadith(this.dataset.text);
        });
    });
}

function copyHadith(text) {
    try {
        navigator.clipboard.writeText(text).then(() => {
            tg.showAlert('تم نسخ الحديث');
            tg.HapticFeedback.notificationOccurred('success');
        });
    } catch (error) {
        console.error('Error copying hadith:', error);
    }
}

function shareHadith(text) {
    try {
        // In production, this would use Telegram's share API
        tg.showAlert(`سيتم مشاركة الحديث:\n\n${text}`);
        tg.HapticFeedback.impactOccurred('light');
    } catch (error) {
        console.error('Error sharing hadith:', error);
    }
}

// Tasbeeh Counter Module
function initTasbeehCounter() {
    initTasbeehOptions();
    initTasbeehButton();
    initTasbeehActions();
}

function initTasbeehOptions() {
    document.querySelectorAll('.tasbeeh-option').forEach(btn => {
        btn.addEventListener('click', function() {
            const dhikr = this.dataset.dhikr;
            
            // Update active state
            document.querySelectorAll('.tasbeeh-option').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update tasbeeh text
            document.querySelector('.tasbeeh-text').textContent = dhikr;
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function initTasbeehButton() {
    const tasbeehBtn = document.getElementById('tasbeeh-btn');
    let count = 0;
    const target = 33;
    
    tasbeehBtn.addEventListener('click', function() {
        count++;
        document.getElementById('tasbeeh-count').textContent = count;
        
        if (count === target) {
            tg.HapticFeedback.notificationOccurred('success');
            tg.showAlert('أكملت الهدف!');
        } else {
            tg.HapticFeedback.impactOccurred('light');
        }
    });
}

function initTasbeehActions() {
    document.getElementById('reset-tasbeeh').addEventListener('click', function() {
        document.getElementById('tasbeeh-count').textContent = '0';
        tg.HapticFeedback.impactOccurred('medium');
    });
    
    document.getElementById('save-tasbeeh').addEventListener('click', function() {
        tg.showAlert('تم حفظ التسبيح');
        tg.HapticFeedback.notificationOccurred('success');
    });
}

// Worship Tracker Module
function initWorshipTracker() {
    initDateNavigation();
    initWorshipCheckboxes();
    initWorshipSave();
}

function initDateNavigation() {
    document.getElementById('prev-day').addEventListener('click', function() {
        // Navigate to previous day
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('next-day').addEventListener('click', function() {
        // Navigate to next day
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initWorshipCheckboxes() {
    document.querySelectorAll('.worship-checkboxes input').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                tg.HapticFeedback.notificationOccurred('success');
            }
        });
    });
}

function initWorshipSave() {
    document.getElementById('save-worship').addEventListener('click', function() {
        tg.showAlert('تم حفظ التقدم');
        tg.HapticFeedback.notificationOccurred('success');
    });
}

// Daily Challenges Module
function initDailyChallenges() {
    try {
        loadDailyChallenge();
        initChallengeActions();
        loadCommunityProgress();
    } catch (error) {
        console.error('Error initializing daily challenges:', error);
    }
}

function loadDailyChallenge() {
    try {
        const challenges = [
            {
                id: 1,
                title: 'قراءة 5 صفحات من القرآن',
                description: 'اقرأ 5 صفحات من القرآن الكريم اليوم',
                xp: 50,
                icon: '📖',
                completed: false
            },
            {
                id: 2,
                title: 'أداء الصلوات الخمس',
                description: 'أدِ الصلوات الخمس في وقتها',
                xp: 100,
                icon: '🕌',
                completed: false
            },
            {
                id: 3,
                title: 'أذكار الصباح والمساء',
                description: 'اقرأ أذكار الصباح والمساء',
                xp: 30,
                icon: '🤲',
                completed: false
            },
            {
                id: 4,
                title: 'التسبيح 100 مرة',
                description: 'سبح الله 100 مرة',
                xp: 25,
                icon: '📿',
                completed: false
            },
            {
                id: 5,
                title: 'قراءة حديث نبوي',
                description: 'اقرأ حديثاً واحداً على الأقل',
                xp: 20,
                icon: '📚',
                completed: false
            }
        ];
        
        const challengeContainer = document.querySelector('.challenges-content');
        if (challengeContainer) {
            challengeContainer.innerHTML = `
                <div class="daily-challenge-card">
                    <div class="challenge-header">
                        <span class="challenge-icon">🎯</span>
                        <h3>تحدي اليوم</h3>
                    </div>
                    <div class="challenge-info">
                        <h4>${challenges[0].title}</h4>
                        <p>${challenges[0].description}</p>
                        <div class="challenge-reward">
                            <span class="reward-icon">⭐</span>
                            <span class="reward-xp">+${challenges[0].xp} XP</span>
                        </div>
                    </div>
                    <button class="action-btn complete-challenge" data-id="${challenges[0].id}">إكمال التحدي</button>
                </div>
                
                <div class="community-progress">
                    <h3>تقدم المجتمع</h3>
                    <div class="progress-stats">
                        <div class="stat-item">
                            <span class="stat-label">المشاركون:</span>
                            <span class="stat-value">1,234</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">المكتملون:</span>
                            <span class="stat-value">856</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">نسبة الإنجاز:</span>
                            <span class="stat-value">69%</span>
                        </div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 69%"></div>
                    </div>
                </div>
            `;
            
            // Add event listener for complete button
            const completeBtn = document.querySelector('.complete-challenge');
            if (completeBtn) {
                completeBtn.addEventListener('click', function() {
                    completeChallenge(this.dataset.id);
                });
            }
        }
        
        // Cache challenges
        cacheData('dailyChallenges', challenges);
    } catch (error) {
        console.error('Error loading daily challenge:', error);
    }
}

function initChallengeActions() {
    // Additional challenge actions can be added here
}

function loadCommunityProgress() {
    // In production, this would fetch from API
    const progress = {
        participants: 1234,
        completed: 856,
        percentage: 69
    };
    
    cacheData('communityProgress', progress);
}

function completeChallenge(challengeId) {
    try {
        tg.showConfirm('هل أكملت هذا التحدي؟', (confirmed) => {
            if (confirmed) {
                // Award XP
                awardXP(50);
                
                // Update UI
                const completeBtn = document.querySelector('.complete-challenge');
                if (completeBtn) {
                    completeBtn.textContent = '✅ تم الإكمال';
                    completeBtn.disabled = true;
                    completeBtn.style.background = '#4CAF50';
                }
                
                tg.HapticFeedback.notificationOccurred('success');
                tg.showAlert('تم إكمال التحدي! +50 XP');
            }
        });
    } catch (error) {
        console.error('Error completing challenge:', error);
    }
}

// Favorites Module
function initFavorites() {
    initFavoritesTabs();
    loadFavorites('quran');
}

function initFavoritesTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            // Update active state
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Load favorites for tab
            loadFavorites(tab);
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function loadFavorites(tab) {
    const favoritesList = document.getElementById('favorites-list');
    
    // In production, this would fetch from API
    const favorites = {
        quran: [
            { title: 'سورة الفاتحة', reference: 'صفحة 1' },
            { title: 'آية الكرسي', reference: 'البقرة 255' }
        ],
        hadith: [
            { title: 'إنما الأعمال بالنيات', reference: 'البخاري 1' }
        ],
        adhkar: [
            { title: 'أذكار الصباح', reference: 'يومي' }
        ]
    };
    
    const items = favorites[tab] || [];
    
    if (items.length === 0) {
        favoritesList.innerHTML = '<div class="empty-state">لا توجد مفضلات</div>';
    } else {
        favoritesList.innerHTML = items.map(item => `
            <div class="favorite-item">
                <h4>${item.title}</h4>
                <span class="favorite-reference">${item.reference}</span>
                <button class="remove-favorite">🗑️</button>
            </div>
        `).join('');
    }
}

// Reading History Module
function initReadingHistory() {
    // Load history data
    // In production, this would fetch from API
}

// Activity Timeline Module
function initActivityTimeline() {
    initTimelineFilter();
}

function initTimelineFilter() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update active state
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Filter timeline
            filterTimeline(filter);
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function filterTimeline(filter) {
    // In production, this would filter the timeline
}

// Analytics Module
function initAnalytics() {
    initAnalyticsPeriod();
}

function initAnalyticsPeriod() {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.dataset.period;
            
            // Update active state
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Load analytics for period
            loadAnalytics(period);
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function loadAnalytics(period) {
    // In production, this would fetch analytics for the period
}

// Settings Module
function initSettings() {
    try {
        // Dark mode toggle
        const darkModeToggle = document.getElementById('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('change', function() {
                toggleDarkMode(this.checked);
            });
        }
        
        // Font size select
        const fontSizeSelect = document.getElementById('font-size-select');
        if (fontSizeSelect) {
            fontSizeSelect.addEventListener('change', function() {
                changeFontSize(this.value);
            });
        }
        
        // Language select
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.addEventListener('change', function() {
                changeLanguage(this.value);
            });
        }
        
        // Notification toggles
        initNotificationSettings();
        
        // Prayer settings
        const prayerMethod = document.getElementById('prayer-method');
        if (prayerMethod) {
            prayerMethod.addEventListener('change', function() {
                changePrayerMethod(this.value);
            });
        }
        
        const locationBtn = document.getElementById('location-btn');
        if (locationBtn) {
            locationBtn.addEventListener('click', function() {
                if (typeof requestLocation === 'function') {
                    requestLocation();
                } else {
                    debugLog('requestLocation function not defined');
                }
            });
        }
        
        // Data export/import
        const exportBtn = document.getElementById('export-data');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportUserData);
        }
        
        const importBtn = document.getElementById('import-data');
        if (importBtn) {
            importBtn.addEventListener('click', importUserData);
        }
    } catch (error) {
        console.error('Error initializing settings:', error);
    }
}

function initNotificationSettings() {
    try {
        // Prayer notifications
        const prayerNotif = document.querySelector('.settings-section:nth-child(3) .setting-item:nth-child(1) input');
        if (prayerNotif) {
            prayerNotif.addEventListener('change', function() {
                togglePrayerNotifications(this.checked);
            });
        }
        
        // Adhkar notifications
        const adhkarNotif = document.querySelector('.settings-section:nth-child(3) .setting-item:nth-child(2) input');
        if (adhkarNotif) {
            adhkarNotif.addEventListener('change', function() {
                toggleAdhkarNotifications(this.checked);
            });
        }
        
        // Challenge notifications
        const challengeNotif = document.querySelector('.settings-section:nth-child(3) .setting-item:nth-child(3) input');
        if (challengeNotif) {
            challengeNotif.addEventListener('change', function() {
                toggleChallengeNotifications(this.checked);
            });
        }
    } catch (error) {
        console.error('Error initializing notification settings:', error);
    }
}

function togglePrayerNotifications(enabled) {
    try {
        // In production, this would send to backend to enable/disable Telegram bot notifications
        const notificationSettings = getCachedData('notificationSettings') || {};
        notificationSettings.prayer = enabled;
        cacheData('notificationSettings', notificationSettings);
        
        tg.HapticFeedback.impactOccurred('light');
        
        if (enabled) {
            tg.showAlert('تم تفعيل إشعارات الصلاة');
        } else {
            tg.showAlert('تم تعطيل إشعارات الصلاة');
        }
    } catch (error) {
        console.error('Error toggling prayer notifications:', error);
    }
}

function toggleAdhkarNotifications(enabled) {
    try {
        const notificationSettings = getCachedData('notificationSettings') || {};
        notificationSettings.adhkar = enabled;
        cacheData('notificationSettings', notificationSettings);
        
        tg.HapticFeedback.impactOccurred('light');
        
        if (enabled) {
            tg.showAlert('تم تفعيل إشعارات الأذكار');
        } else {
            tg.showAlert('تم تعطيل إشعارات الأذكار');
        }
    } catch (error) {
        console.error('Error toggling adhkar notifications:', error);
    }
}

function toggleChallengeNotifications(enabled) {
    try {
        const notificationSettings = getCachedData('notificationSettings') || {};
        notificationSettings.challenges = enabled;
        cacheData('notificationSettings', notificationSettings);
        
        tg.HapticFeedback.impactOccurred('light');
        
        if (enabled) {
            tg.showAlert('تم تفعيل إشعارات التحديات');
        } else {
            tg.showAlert('تم تعطيل إشعارات التحديات');
        }
    } catch (error) {
        console.error('Error toggling challenge notifications:', error);
    }
}

function initDarkModeToggle() {
    const darkModeToggle = document.getElementById('dark-mode');
    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initFontSizeSelect() {
    const fontSizeSelect = document.getElementById('font-size-select');
    fontSizeSelect.addEventListener('change', function() {
        const size = this.value;
        document.body.style.fontSize = size === 'small' ? '14px' : size === 'large' ? '18px' : '16px';
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initLanguageSelect() {
    const languageSelect = document.getElementById('language-select');
    languageSelect.addEventListener('change', function() {
        tg.showAlert('سيتم تغيير اللغة');
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initPrayerMethod() {
    const prayerMethod = document.getElementById('prayer-method');
    prayerMethod.addEventListener('change', function() {
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initLocationBtn() {
    document.getElementById('location-btn').addEventListener('click', function() {
        tg.showAlert('سيتم تحديد الموقع');
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initDataActions() {
    document.getElementById('export-data').addEventListener('click', function() {
        tg.showAlert('سيتم تصدير البيانات');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('import-data').addEventListener('click', function() {
        tg.showAlert('سيتم استيراد البيانات');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('clear-data').addEventListener('click', function() {
        tg.showConfirm('هل أنت متأكد من مسح البيانات؟', (confirmed) => {
            if (confirmed) {
                tg.showAlert('تم مسح البيانات');
            }
        });
    });
}

// Search Center Module
function initSearchCenter() {
    initGlobalSearch();
    initSearchFilters();
}

function initGlobalSearch() {
    const searchInput = document.getElementById('global-search');
    const searchBtn = document.querySelector('.search-bar-large .search-btn-large');
    
    searchBtn.addEventListener('click', () => performGlobalSearch(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performGlobalSearch(searchInput.value);
    });
}

function initSearchFilters() {
    document.querySelectorAll('.filter-chip').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update active state
            document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            tg.HapticFeedback.impactOccurred('light');
        });
    });
}

function performGlobalSearch(query) {
    const searchResults = document.getElementById('search-results');
    
    if (!query) {
        searchResults.innerHTML = `
            <div class="search-empty">
                <div class="empty-icon">🔍</div>
                <p>ابحث عن أي شيء في التطبيق</p>
            </div>
        `;
        return;
    }
    
    // In production, this would search in API
    searchResults.innerHTML = `
        <div class="search-results-list">
            <div class="search-result-item">
                <span class="result-type">📖 قرآن</span>
                <p>نتيجة البحث: ${query}</p>
            </div>
            <div class="search-result-item">
                <span class="result-type">📚 حديث</span>
                <p>نتيجة البحث: ${query}</p>
            </div>
        </div>
    `;
}

// Notifications Module
function initNotifications() {
    initNotificationActions();
}

function initNotificationActions() {
    document.getElementById('mark-all-read').addEventListener('click', function() {
        document.querySelectorAll('.notification-item').forEach(item => {
            item.classList.remove('unread');
        });
        tg.HapticFeedback.notificationOccurred('success');
    });
    
    document.getElementById('clear-notifications').addEventListener('click', function() {
        document.getElementById('notifications-list').innerHTML = '<div class="empty-state">لا توجد إشعارات</div>';
        tg.HapticFeedback.impactOccurred('medium');
    });
}

// Help Module
function initHelp() {
    initContactActions();
}

function initContactActions() {
    document.getElementById('contact-support').addEventListener('click', function() {
        tg.showAlert('سيتم فتح نموذج الدعم');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('report-bug').addEventListener('click', function() {
        tg.showAlert('سيتم فتح نموذج الإبلاغ');
        tg.HapticFeedback.impactOccurred('light');
    });
}

// About Module
function initAbout() {
    initAppActions();
}

function initAppActions() {
    document.getElementById('rate-app').addEventListener('click', function() {
        tg.showAlert('شكراً لتقييمك!');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('share-app').addEventListener('click', function() {
        tg.showAlert('سيتم مشاركة التطبيق');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('privacy-policy').addEventListener('click', function() {
        tg.showAlert('سياسة الخصوصية: نحترم خصوصيتك');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('terms').addEventListener('click', function() {
        tg.showAlert('الشروط والأحكام: استخدام التطبيق يعني الموافقة على الشروط');
        tg.HapticFeedback.impactOccurred('light');
    });
}

// Points System Module
function initPointsSystem() {
    initPointsNavigation();
    initPointsActions();
    initMarketplace();
    loadUserPoints();
}

function initPointsNavigation() {
    document.getElementById('back-from-points').addEventListener('click', function() {
        navigateToScreen('dashboard');
        tg.HapticFeedback.impactOccurred('light');
    });
    
    document.getElementById('back-from-admin').addEventListener('click', function() {
        navigateToScreen('dashboard');
        tg.HapticFeedback.impactOccurred('light');
    });
}

function initPointsActions() {
    // Add points for various actions
    const actions = {
        'quran-reading': 10,
        'prayer-completed': 5,
        'adhkar-completed': 15,
        'tasbeeh-100': 3,
        'challenge-completed': 20
    };
    
    // Simulate earning points
    Object.keys(actions).forEach(action => {
        const element = document.querySelector(`[data-action="${action}"]`);
        if (element) {
            element.addEventListener('click', function() {
                addPoints(actions[action]);
                tg.HapticFeedback.notificationOccurred('success');
            });
        }
    });
}

function addPoints(amount) {
    try {
        let currentPoints = parseInt(localStorage.getItem('userPoints') || '0');
        currentPoints += amount;
        localStorage.setItem('userPoints', currentPoints);
        updatePointsDisplay(currentPoints);
        
        // Show notification
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.showAlert(`+${amount} نقاط! رصيدك الجديد: ${currentPoints}`);
        }
    } catch (error) {
        console.error('Error adding points:', error);
    }
}

function removePoints(amount) {
    try {
        let currentPoints = parseInt(localStorage.getItem('userPoints') || '0');
        if (currentPoints >= amount) {
            currentPoints -= amount;
            localStorage.setItem('userPoints', currentPoints);
            updatePointsDisplay(currentPoints);
            return true;
        } else {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('رصيد النقاط غير كافٍ');
            }
            return false;
        }
    } catch (error) {
        console.error('Error removing points:', error);
        return false;
    }
}

function loadUserPoints() {
    try {
        const points = localStorage.getItem('userPoints') || '0';
        updatePointsDisplay(parseInt(points));
    } catch (error) {
        console.error('Error loading points:', error);
    }
}

function updatePointsDisplay(points) {
    const pointsElement = document.getElementById('user-points');
    if (pointsElement) {
        pointsElement.textContent = points;
    }
}

function initMarketplace() {
    const serviceButtons = document.querySelectorAll('.service-btn');
    serviceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const cost = parseInt(this.getAttribute('data-cost'));
            const service = this.closest('.service-item').getAttribute('data-service');
            
            if (removePoints(cost)) {
                purchaseService(service);
                tg.HapticFeedback.notificationOccurred('success');
            } else {
                tg.HapticFeedback.notificationOccurred('error');
            }
        });
    });
}

function purchaseService(service) {
    try {
        // Get purchased services
        let purchasedServices = JSON.parse(localStorage.getItem('purchasedServices') || '[]');
        
        if (!purchasedServices.includes(service)) {
            purchasedServices.push(service);
            localStorage.setItem('purchasedServices', JSON.stringify(purchasedServices));
            
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('تم شراء الخدمة بنجاح!');
            }
        } else {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('لقد اشتريت هذه الخدمة بالفعل');
            }
        }
    } catch (error) {
        console.error('Error purchasing service:', error);
    }
}

// Admin Dashboard Module
function initAdminDashboard() {
    initAdminNavigation();
    initAdminStats();
    initAdminUserManagement();
    initAdminPointsManagement();
    initAdminServiceManagement();
}

function initAdminNavigation() {
    try {
        // Check if user is admin using Telegram user ID
        const telegramUser = tg.initDataUnsafe?.user;
        const adminUserIds = [6326713765];
        const isAdmin = telegramUser && adminUserIds.includes(telegramUser.id);
        
        if (!isAdmin) {
            // Hide admin dashboard for non-admin users
            const adminScreen = document.getElementById('admin-dashboard');
            if (adminScreen) {
                adminScreen.style.display = 'none';
            }
        } else {
            // Initialize admin subpage navigation
            initAdminSubpageNavigation();
        }
    } catch (error) {
        console.error('Error initializing admin navigation:', error);
    }
}

function initAdminSubpageNavigation() {
    try {
        // Back button to return to admin dashboard
        document.querySelectorAll('.back-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const targetScreen = this.dataset.screen;
                if (targetScreen) {
                    navigateToScreen(targetScreen);
                } else {
                    // Default to admin dashboard
                    navigateToScreen('admin-dashboard');
                }
                safeHapticFeedback('light');
            });
        });
        
        // Admin dashboard navigation buttons (using data-action)
        const adminNavButtons = document.querySelectorAll('.mission-btn');
        adminNavButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const action = this.dataset.action;
                if (action) {
                    handleAdminAction(action);
                }
                safeHapticFeedback('light');
            });
        });
    } catch (error) {
        console.error('Error initializing admin subpage navigation:', error);
    }
}

function handleAdminAction(action) {
    try {
        // Map actions to subpage IDs
        const actionToSubpage = {
            'broadcast': 'broadcast-center',
            'analytics': 'live-dashboard',
            'users': 'user-management',
            'ai': 'ai-chat',
            'notifications': 'notification-center',
            'settings': 'feature-flags',
            'content': 'content-manager',
            'media': 'media-manager',
            'reports': 'analytics-dashboard',
            'system': 'system-monitor'
        };
        
        const subpageId = actionToSubpage[action];
        if (subpageId) {
            showAdminSubpage(subpageId);
        } else {
            safeShowAlert(`Action: ${action}`);
        }
    } catch (error) {
        console.error('Error handling admin action:', error);
    }
}

function showAdminSubpage(subpageId) {
    try {
        // Hide all admin subpages
        document.querySelectorAll('.admin-subpage').forEach(subpage => {
            subpage.classList.remove('active');
            subpage.style.display = 'none';
        });
        
        // Show target subpage
        const targetSubpage = document.getElementById(subpageId);
        if (targetSubpage) {
            targetSubpage.classList.add('active');
            targetSubpage.style.display = 'block';
        }
    } catch (error) {
        console.error('Error showing admin subpage:', error);
    }
}

function initAdminStats() {
    // Simulated stats for demo
    document.getElementById('total-users').textContent = '1,234';
    document.getElementById('total-points').textContent = '45,678';
    document.getElementById('total-services').textContent = '89';
}

function initAdminUserManagement() {
    const searchButton = document.getElementById('search-user');
    const searchInput = document.getElementById('user-search');
    
    if (searchButton && searchInput) {
        searchButton.addEventListener('click', function() {
            const searchTerm = searchInput.value;
            searchUsers(searchTerm);
        });
    }
}

function searchUsers(searchTerm) {
    try {
        // Simulated user search for demo
        const mockUsers = [
            { id: 123456789, name: 'أحمد محمد', points: 150 },
            { id: 987654321, name: 'فاطمة علي', points: 320 },
            { id: 456789123, name: 'محمد أحمد', points: 85 }
        ];
        
        const results = mockUsers.filter(user => 
            user.name.includes(searchTerm) || user.id.toString().includes(searchTerm)
        );
        
        displayUserResults(results);
    } catch (error) {
        console.error('Error searching users:', error);
    }
}

function displayUserResults(users) {
    const resultsContainer = document.getElementById('user-results');
    if (!resultsContainer) return;
    
    if (users.length === 0) {
        resultsContainer.innerHTML = '<p>لم يتم العثور على مستخدمين</p>';
        return;
    }
    
    let html = '';
    users.forEach(user => {
        html += `
            <div class="user-result-item">
                <span class="user-result-name">${user.name} (ID: ${user.id})</span>
                <span class="user-result-points">${user.points} نقطة</span>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

function initAdminPointsManagement() {
    const addPointsBtn = document.getElementById('add-points-btn');
    const removePointsBtn = document.getElementById('remove-points-btn');
    
    if (addPointsBtn) {
        addPointsBtn.addEventListener('click', function() {
            const userId = document.getElementById('user-id-input').value;
            const points = parseInt(document.getElementById('points-amount').value);
            
            if (userId && points) {
                manageUserPoints(userId, points, 'add');
            }
        });
    }
    
    if (removePointsBtn) {
        removePointsBtn.addEventListener('click', function() {
            const userId = document.getElementById('user-id-input').value;
            const points = parseInt(document.getElementById('points-amount').value);
            
            if (userId && points) {
                manageUserPoints(userId, points, 'remove');
            }
        });
    }
}

function manageUserPoints(userId, points, action) {
    try {
        // Simulated API call for demo
        const message = action === 'add' 
            ? `تم إضافة ${points} نقطة للمستخدم ${userId}`
            : `تم خصم ${points} نقطة من المستخدم ${userId}`;
        
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.showAlert(message);
            window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
        }
        
        // Clear inputs
        document.getElementById('user-id-input').value = '';
        document.getElementById('points-amount').value = '';
    } catch (error) {
        console.error('Error managing user points:', error);
    }
}

function initAdminServiceManagement() {
    const updateCostBtn = document.getElementById('update-service-cost');
    
    if (updateCostBtn) {
        updateCostBtn.addEventListener('click', function() {
            const service = document.getElementById('service-select').value;
            const cost = document.getElementById('service-cost').value;
            
            if (service && cost) {
                updateServiceCost(service, parseInt(cost));
            }
        });
    }
}

function updateServiceCost(service, cost) {
    try {
        // Simulated API call for demo
        const message = `تم تحديث سعر ${service} إلى ${cost} نقطة`;
        
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.showAlert(message);
            window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
        }
        
        // Clear input
        document.getElementById('service-cost').value = '';
    } catch (error) {
        console.error('Error updating service cost:', error);
    }
}

// Add navigation to points system and admin dashboard
function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const screenId = this.getAttribute('data-screen');
            navigateToScreen(screenId);
            
            // Update active state
            navButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
            }
        });
    });
    
    // Add special navigation for points and admin
    const profileScreen = document.getElementById('profile');
    if (profileScreen) {
        // Add points button to profile
        const pointsButton = document.createElement('button');
        pointsButton.className = 'action-btn';
        pointsButton.textContent = 'نظام النقاط';
        pointsButton.addEventListener('click', function() {
            navigateToScreen('points-system');
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
            }
        });
        
        const appActions = profileScreen.querySelector('.app-actions');
        if (appActions) {
            appActions.insertBefore(pointsButton, appActions.firstChild);
        }
        
        // Add admin button for admin users
        const isAdmin = localStorage.getItem('isAdmin') === 'true';
        if (isAdmin) {
            const adminButton = document.createElement('button');
            adminButton.className = 'action-btn';
            adminButton.textContent = 'لوحة التحكم';
            adminButton.addEventListener('click', function() {
                navigateToScreen('admin-dashboard');
                if (window.Telegram && window.Telegram.WebApp) {
                    window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
                }
            });
            
            appActions.insertBefore(adminButton, appActions.firstChild);
        }
    }
}

// Initialize all modules
document.addEventListener('DOMContentLoaded', function() {
    try {
        initApp();
        initNavigation();
        initPointsSystem();
        initAdminDashboard();
    } catch (error) {
        console.error('Error initializing app:', error);
    }
});

// Offline Data Caching Module
function initOfflineCache() {
    try {
        // Initialize cache if not exists
        if (!localStorage.getItem('rafeeq_cache')) {
            const initialCache = {
                quranPages: {},
                adhkar: {},
                hadith: {},
                settings: {},
                lastSync: null
            };
            localStorage.setItem('rafeeq_cache', JSON.stringify(initialCache));
        }
        
        // Check online status
        window.addEventListener('online', syncOfflineData);
        window.addEventListener('offline', showOfflineNotification);
        
        // Auto-sync every 5 minutes if online
        setInterval(() => {
            if (navigator.onLine) {
                syncOfflineData();
            }
        }, 5 * 60 * 1000);
    } catch (error) {
        console.error('Error initializing offline cache:', error);
    }
}

function cacheData(key, data) {
    try {
        const cache = JSON.parse(localStorage.getItem('rafeeq_cache') || '{}');
        cache[key] = data;
        cache.lastSync = new Date().toISOString();
        localStorage.setItem('rafeeq_cache', JSON.stringify(cache));
    } catch (error) {
        console.error('Error caching data:', error);
    }
}

function getCachedData(key) {
    try {
        const cache = JSON.parse(localStorage.getItem('rafeeq_cache') || '{}');
        return cache[key] || null;
    } catch (error) {
        console.error('Error getting cached data:', error);
        return null;
    }
}

function syncOfflineData() {
    try {
        // In production, this would sync with backend API
        console.log('Syncing offline data...');
        const cache = JSON.parse(localStorage.getItem('rafeeq_cache') || '{}');
        cache.lastSync = new Date().toISOString();
        localStorage.setItem('rafeeq_cache', JSON.stringify(cache));
    } catch (error) {
        console.error('Error syncing offline data:', error);
    }
}

function showOfflineNotification() {
    try {
        tg.showAlert('أنت متصل بدون إنترنت. سيتم مزامنة البيانات عند الاتصال.');
    } catch (error) {
        console.error('Error showing offline notification:', error);
    }
}

// Utility Functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        tg.showAlert('تم النسخ');
        tg.HapticFeedback.notificationOccurred('success');
    });
}

// Audio Player Module
function initAudioPlayer() {
    try {
        const playPauseBtn = document.getElementById('play-pause-btn');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const closeBtn = document.getElementById('close-audio');
        
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', togglePlayPause);
        }
        if (prevBtn) {
            prevBtn.addEventListener('click', playPrevious);
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', playNext);
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', closeAudioPlayer);
        }
    } catch (error) {
        console.error('Error initializing audio player:', error);
    }
}

let isPlaying = false;
let currentAudio = null;

function togglePlayPause() {
    try {
        isPlaying = !isPlaying;
        const playPauseBtn = document.getElementById('play-pause-btn');
        
        if (isPlaying) {
            playPauseBtn.textContent = '⏸️';
            // In production, this would play actual audio
            tg.HapticFeedback.impactOccurred('light');
        } else {
            playPauseBtn.textContent = '▶️';
            // In production, this would pause audio
            tg.HapticFeedback.impactOccurred('light');
        }
        
        updateAudioProgress();
    } catch (error) {
        console.error('Error toggling play/pause:', error);
    }
}

function playPrevious() {
    try {
        // In production, this would play previous track
        tg.HapticFeedback.impactOccurred('light');
        tg.showAlert('تشغيل السورة السابقة');
    } catch (error) {
        console.error('Error playing previous:', error);
    }
}

function playNext() {
    try {
        // In production, this would play next track
        tg.HapticFeedback.impactOccurred('light');
        tg.showAlert('تشغيل السورة التالية');
    } catch (error) {
        console.error('Error playing next:', error);
    }
}

function closeAudioPlayer() {
    try {
        const audioDock = document.getElementById('audio-dock');
        if (audioDock) {
            audioDock.style.display = 'none';
        }
        tg.HapticFeedback.impactOccurred('medium');
    } catch (error) {
        console.error('Error closing audio player:', error);
    }
}

function updateAudioProgress() {
    try {
        if (isPlaying) {
            // Simulate audio progress
            let progress = 0;
            const progressFill = document.getElementById('audio-progress');
            const currentTimeEl = document.getElementById('audio-current');
            
            const interval = setInterval(() => {
                if (!isPlaying) {
                    clearInterval(interval);
                    return;
                }
                
                progress += 1;
                if (progress > 100) {
                    progress = 0;
                    isPlaying = false;
                    const playPauseBtn = document.getElementById('play-pause-btn');
                    if (playPauseBtn) playPauseBtn.textContent = '▶️';
                    clearInterval(interval);
                }
                
                if (progressFill) progressFill.style.width = `${progress}%`;
                
                // Update time display
                const seconds = Math.floor((progress / 100) * 38);
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = seconds % 60;
                if (currentTimeEl) {
                    currentTimeEl.textContent = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
                }
            }, 380); // Update every 380ms for 38 second duration
        }
    } catch (error) {
        console.error('Error updating audio progress:', error);
    }
}
