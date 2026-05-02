/**
 * MystVPN - JavaScript приложение
 * Многоязычность и интерактивность
 */

// Переводы для всех языков
const base = {
  ru: {
    nav_features: "Возможности",
    nav_pricing: "Тарифы",
    nav_setup: "Подключение",
    nav_faq: "FAQ",
    nav_channel: "Канал",
    nav_bot: "Открыть бота",
    hero_badge: "3 дня бесплатно · без карты · в Telegram",
    hero_title: "VPN, который подключается быстрее, чем открывается приложение.",
    hero_text: "MystVPN выдает ключ прямо в официальном боте @MysterioVPN_bot. Работает на телефоне, ноутбуке и ПК, помогает держать доступ к нужным сервисам и не требует сложной настройки.",
    cta_trial: "Попробовать 3 дня",
    cta_guide: "Смотреть инструкцию",
    hero_note: "Оплата картой и СБП. Подписка не продлевается без вашего действия.",
    mock_setup: "ключ за 60 секунд",
    mock_traffic: "безлимитный",
    mock_trial: "3 дня бесплатно",
    chat_1: "Выберите тариф или активируйте пробный период.",
    chat_2: "🎁 3 дня бесплатно",
    chat_3: "Пробный период активирован.",
    chat_btn_1: "Открыть ключ",
    chat_btn_2: "Инструкция",
    chat_btn_3: "Личный кабинет",
    features_kicker: "Возможности",
    features_title: "Сервис без лишнего шума.",
    features_text: "Вместо кабинетов, форм и ручной выдачи ключей — понятный Telegram-бот, стабильные протоколы и короткая инструкция для каждого устройства.",
    f1_title: "Ключ сразу после оплаты",
    f1_text: "Бот создает VPN-доступ автоматически: пробник, покупка, подарок и продление работают без ожидания менеджера.",
    f2_title: "Reality и XHTTP",
    f2_text: "Два профиля в одной подписке. Если один маршрут работает хуже, клиент может переключиться на резервный.",
    f3_title: "Все популярные клиенты",
    f3_text: "Hiddify, v2rayTUN, V2RayNG, FoXray и Streisand. Подходит для Android, iPhone, Windows и Mac.",
    f4_title: "Честный срок доступа",
    f4_text: "Ключ отключается по окончании подписки. В кабинете всегда видно, сколько дней осталось.",
    f5_title: "Реферальные бонусы",
    f5_text: "Приглашайте друзей: они получают 3 дня, вы получаете бонусные дни к своей подписке.",
    f6_title: "Поддержка рядом",
    f6_text: "Канал @MysterioVPN, поддержка @Myst_support и инструкция на сайте помогают быстро решить проблемы подключения.",
    setup_kicker: "Подключение",
    setup_title: "От Telegram до VPN за 4 шага.",
    setup_text: "Пользователь не разбирается в протоколах. Он нажимает кнопку, копирует подписку или открывает ее в приложении и подключается.",
    s1_title: "Откройте бота",
    s1_text: "Перейдите в @MysterioVPN_bot и запустите пробник или выберите тариф.",
    s2_title: "Получите подписку",
    s2_text: "Бот отправит ссылку подписки и готовый ключ для VPN-клиента.",
    s3_title: "Добавьте в приложение",
    s3_text: "Откройте ссылку в Hiddify, v2rayTUN или другом рекомендованном клиенте.",
    s4_title: "Включите VPN",
    s4_text: "Проверьте доступ, сохраните кабинет и продлевайте подписку в один клик.",
    pricing_kicker: "Тарифы",
    pricing_title: "Прозрачные цены.",
    pricing_text: "Можно начать с бесплатного пробника. Чем дольше срок, тем ниже цена за месяц.",
    p1_period: "1 месяц",
    p2_period: "3 месяца",
    p3_period: "6 месяцев",
    p4_period: "1 год",
    p2_save: "183 ₽/мес · экономия 16%",
    p3_save: "167 ₽/мес · экономия 24%",
    p4_save: "150 ₽/мес · экономия 32%",
    popular: "Популярный",
    pf1: "Безлимитный трафик",
    pf2: "Все устройства",
    pf3: "Поддержка",
    pf4: "Лучший старт",
    pf5: "Меньше продлений",
    pf6: "Максимальная выгода",
    buy: "Купить в боте",
    tech_title: "Технологии под нестабильные сети.",
    tech_text: "MystVPN использует VLESS Reality и резервный XHTTP-профиль. Это помогает сохранить подключение в ситуациях, где обычные VPN-профили часто ломаются.",
    tech_l1: "Subscription URL для быстрой настройки.",
    tech_l2: "Автоматическая выдача и продление ключа.",
    tech_l3: "Удаление ключа после окончания подписки.",
    devices_title: "Один сервис для всех устройств.",
    devices_text: "Настройте телефон, ноутбук и домашний компьютер. Бот хранит кабинет, срок подписки, инструкцию и ссылку для обновления профиля.",
    faq_title: "Ответы до покупки.",
    faq_text: "Если останутся вопросы, напишите в поддержку. Ссылка всегда есть в боте и внизу сайта.",
    q1: "Что будет после окончания пробника?",
    a1: "Ключ перестанет работать. Чтобы продолжить, выберите тариф в боте и оплатите подписку.",
    q2: "Можно ли пользоваться на нескольких устройствах?",
    a2: "Да. Один профиль можно добавить на телефон, планшет, ноутбук и ПК.",
    q3: "Какие способы оплаты доступны?",
    a3: "В боте доступны оплата картой и СБП через YooKassa. Также поддерживаются подарки и промокоды.",
    q4: "Российские банки будут работать?",
    a4: "Для банков и госуслуг лучше включить bypass в VPN-клиенте. В кабинете есть отдельная подсказка с правилами маршрутизации.",
    q5: "Где получить помощь?",
    a5: "Поддержка: @Myst_support. Новости и статусы сервиса: @MysterioVPN.",
    q6: "Как быстро выдается ключ?",
    a6: "Обычно сразу после пробника или оплаты. Если панель временно недоступна, в кабинете появится кнопка повторной выдачи.",
    final_title: "Попробуйте MystVPN до оплаты.",
    final_text: "Откройте официальный бот, активируйте 3 дня и подключите первое устройство по инструкции.",
    final_btn: "Запустить бота",
    foot_bot: "Бот",
    foot_channel: "Канал",
    foot_support: "Поддержка",
    foot_guide: "Инструкция",
    foot_terms: "Оферта"
  },
  en: {
    nav_features: "Features",
    nav_pricing: "Pricing",
    nav_setup: "Setup",
    nav_faq: "FAQ",
    nav_channel: "Channel",
    nav_bot: "Open bot",
    hero_badge: "3 days free · no card · in Telegram",
    hero_title: "A VPN that connects faster than an app opens.",
    hero_text: "MystVPN gives you a key directly in the official @MysterioVPN_bot. It works on phones, laptops and desktops, keeps access to the services you need, and does not require complex setup.",
    cta_trial: "Try 3 days",
    cta_guide: "View guide",
    hero_note: "Card and SBP payments. Subscription does not renew without your action.",
    mock_setup: "key in 60 seconds",
    mock_traffic: "unlimited",
    mock_trial: "3 days free",
    chat_1: "Choose a plan or activate a trial.",
    chat_2: "🎁 3 days free",
    chat_3: "Trial activated.",
    chat_btn_1: "Open key",
    chat_btn_2: "Guide",
    chat_btn_3: "Cabinet",
    features_kicker: "Features",
    features_title: "A service without noise.",
    features_text: "Instead of forms and manual key delivery: a clear Telegram bot, stable protocols and a short guide for every device.",
    f1_title: "Key right after payment",
    f1_text: "The bot creates VPN access automatically: trial, purchase, gift and renewal work without waiting for a manager.",
    f2_title: "Reality and XHTTP",
    f2_text: "Two profiles in one subscription. If one route is worse, the client can switch to backup.",
    f3_title: "Popular clients",
    f3_text: "Hiddify, v2rayTUN, V2RayNG, FoXray and Streisand. Works for Android, iPhone, Windows and Mac.",
    f4_title: "Honest access time",
    f4_text: "The key stops when the subscription ends. The cabinet always shows days left.",
    f5_title: "Referral bonuses",
    f5_text: "Invite friends: they get 3 days, you get bonus days for your subscription.",
    f6_title: "Support nearby",
    f6_text: "The @MysterioVPN channel, @Myst_support and the site guide help solve setup issues quickly.",
    setup_kicker: "Setup",
    setup_title: "From Telegram to VPN in 4 steps.",
    setup_text: "Users do not need to understand protocols. They press a button, copy a subscription or open it in an app, and connect.",
    s1_title: "Open the bot",
    s1_text: "Go to @MysterioVPN_bot and start a trial or choose a plan.",
    s2_title: "Get subscription",
    s2_text: "The bot sends a subscription link and a ready key for a VPN client.",
    s3_title: "Add to app",
    s3_text: "Open the link in Hiddify, v2rayTUN or another recommended client.",
    s4_title: "Turn VPN on",
    s4_text: "Check access, keep your cabinet and renew in one click.",
    pricing_kicker: "Pricing",
    pricing_title: "Transparent prices.",
    pricing_text: "Start with a free trial. Longer periods make the monthly price lower.",
    p1_period: "1 month",
    p2_period: "3 months",
    p3_period: "6 months",
    p4_period: "1 year",
    p2_save: "183 ₽/mo · save 16%",
    p3_save: "167 ₽/mo · save 24%",
    p4_save: "150 ₽/mo · save 32%",
    popular: "Popular",
    pf1: "Unlimited traffic",
    pf2: "All devices",
    pf3: "Support",
    pf4: "Best start",
    pf5: "Fewer renewals",
    pf6: "Best value",
    buy: "Buy in bot",
    tech_title: "Technology for unstable networks.",
    tech_text: "MystVPN uses VLESS Reality and backup XHTTP. This helps keep connection where regular VPN profiles often fail.",
    tech_l1: "Subscription URL for fast setup.",
    tech_l2: "Automatic key issue and renewal.",
    tech_l3: "Key removal after subscription ends.",
    devices_title: "One service for all devices.",
    devices_text: "Set up your phone, laptop and desktop. The bot stores your cabinet, subscription end date, guide and update link.",
    faq_title: "Answers before purchase.",
    faq_text: "If questions remain, contact support. The link is always in the bot and site footer.",
    q1: "What happens after trial ends?",
    a1: "The key stops working. To continue, choose a plan in the bot and pay.",
    q2: "Can I use multiple devices?",
    a2: "Yes. One profile can be added to phone, tablet, laptop and PC.",
    q3: "What payment methods are available?",
    a3: "Card and SBP payments via YooKassa are available in the bot. Gifts and promo codes are also supported.",
    q4: "Will local banks work?",
    a4: "For banks and government services, enable bypass in the VPN client. The cabinet has a routing guide.",
    q5: "Where can I get help?",
    a5: "Support: @Myst_support. News and status: @MysterioVPN.",
    q6: "How fast is key delivery?",
    a6: "Usually immediately after trial or payment. If the panel is temporarily unavailable, the cabinet has a retry button.",
    final_title: "Try MystVPN before paying.",
    final_text: "Open the official bot, activate 3 days and connect your first device using the guide.",
    final_btn: "Launch bot",
    foot_bot: "Bot",
    foot_channel: "Channel",
    foot_support: "Support",
    foot_guide: "Guide",
    foot_terms: "Terms"
  }
};

// Дополнительные языки (частичные переводы)
const packs = {
  fr: { hero_title: "Un VPN qui se connecte en quelques secondes.", nav_features: "Fonctions", nav_pricing: "Tarifs", nav_setup: "Installation", nav_faq: "FAQ", nav_channel: "Canal", nav_bot: "Ouvrir le bot", cta_trial: "Essayer 3 jours", cta_guide: "Voir le guide", pricing_title: "Des prix transparents.", buy: "Acheter dans le bot", final_btn: "Lancer le bot" },
  es: { hero_title: "Un VPN que se conecta en segundos.", nav_features: "Funciones", nav_pricing: "Precios", nav_setup: "Conexión", nav_faq: "FAQ", nav_channel: "Canal", nav_bot: "Abrir bot", cta_trial: "Probar 3 días", cta_guide: "Ver guía", pricing_title: "Precios claros.", buy: "Comprar en el bot", final_btn: "Abrir bot" },
  pt: { hero_title: "Uma VPN que conecta em segundos.", nav_features: "Recursos", nav_pricing: "Preços", nav_setup: "Configuração", nav_faq: "FAQ", nav_channel: "Canal", nav_bot: "Abrir bot", cta_trial: "Teste 3 dias", cta_guide: "Ver guia", pricing_title: "Preços transparentes.", buy: "Comprar no bot", final_btn: "Abrir bot" },
  tr: { hero_title: "Saniyeler içinde bağlanan VPN.", nav_features: "Özellikler", nav_pricing: "Fiyatlar", nav_setup: "Kurulum", nav_faq: "SSS", nav_channel: "Kanal", nav_bot: "Botu aç", cta_trial: "3 gün dene", cta_guide: "Kılavuz", pricing_title: "Şeffaf fiyatlar.", buy: "Botta satın al", final_btn: "Botu başlat" },
  ar: { hero_title: "VPN يتصل خلال ثوان.", nav_features: "المزايا", nav_pricing: "الأسعار", nav_setup: "الإعداد", nav_faq: "الأسئلة", nav_channel: "القناة", nav_bot: "افتح البوت", cta_trial: "جرّب 3 أيام", cta_guide: "الدليل", pricing_title: "أسعار واضحة.", buy: "اشترِ من البوت", final_btn: "تشغيل البوت" },
  fa: { hero_title: "VPN که در چند ثانیه وصل می‌شود.", nav_features: "قابلیت‌ها", nav_pricing: "قیمت‌ها", nav_setup: "راه‌اندازی", nav_faq: "سوالات", nav_channel: "کانال", nav_bot: "باز کردن ربات", cta_trial: "۳ روز امتحان کن", cta_guide: "راهنما", pricing_title: "قیمت‌گذاری شفاف.", buy: "خرید در ربات", final_btn: "شروع ربات" },
  uk: { hero_title: "VPN, який підключається за секунди.", nav_features: "Можливості", nav_pricing: "Тарифи", nav_setup: "Підключення", nav_faq: "FAQ", nav_channel: "Канал", nav_bot: "Відкрити бота", cta_trial: "Спробувати 3 дні", cta_guide: "Інструкція", pricing_title: "Прозорі ціни.", buy: "Купити в боті", final_btn: "Запустити бота" },
  id: { hero_title: "VPN yang tersambung dalam hitungan detik.", nav_features: "Fitur", nav_pricing: "Harga", nav_setup: "Setup", nav_faq: "FAQ", nav_channel: "Kanal", nav_bot: "Buka bot", cta_trial: "Coba 3 hari", cta_guide: "Lihat panduan", pricing_title: "Harga transparan.", buy: "Beli di bot", final_btn: "Mulai bot" },
  zh: { hero_title: "几秒即可连接的 VPN。", nav_features: "功能", nav_pricing: "价格", nav_setup: "设置", nav_faq: "FAQ", nav_channel: "频道", nav_bot: "打开机器人", cta_trial: "免费试用3天", cta_guide: "查看教程", pricing_title: "透明价格。", buy: "在机器人中购买", final_btn: "启动机器人" },
  ja: { hero_title: "数秒で接続できるVPN。", nav_features: "機能", nav_pricing: "料金", nav_setup: "設定", nav_faq: "FAQ", nav_channel: "チャンネル", nav_bot: "Botを開く", cta_trial: "3日間試す", cta_guide: "ガイドを見る", pricing_title: "わかりやすい料金。", buy: "Botで購入", final_btn: "Botを起動" },
  ko: { hero_title: "몇 초 만에 연결되는 VPN.", nav_features: "기능", nav_pricing: "요금", nav_setup: "설정", nav_faq: "FAQ", nav_channel: "채널", nav_bot: "봇 열기", cta_trial: "3일 체험", cta_guide: "가이드 보기", pricing_title: "투명한 가격.", buy: "봇에서 구매", final_btn: "봇 시작" },
  de: { hero_title: "Ein VPN, das in Sekunden verbindet.", nav_features: "Funktionen", nav_pricing: "Preise", nav_setup: "Einrichtung", nav_faq: "FAQ", nav_channel: "Kanal", nav_bot: "Bot öffnen", cta_trial: "3 Tage testen", cta_guide: "Anleitung", pricing_title: "Klare Preise.", buy: "Im Bot kaufen", final_btn: "Bot starten" },
  vi: { hero_title: "VPN kết nối trong vài giây.", nav_features: "Tính năng", nav_pricing: "Giá", nav_setup: "Cài đặt", nav_faq: "FAQ", nav_channel: "Kênh", nav_bot: "Mở bot", cta_trial: "Thử 3 ngày", cta_guide: "Xem hướng dẫn", pricing_title: "Giá minh bạch.", buy: "Mua trong bot", final_btn: "Khởi chạy bot" },
  ms: { hero_title: "VPN yang bersambung dalam beberapa saat.", nav_features: "Ciri", nav_pricing: "Harga", nav_setup: "Tetapan", nav_faq: "FAQ", nav_channel: "Saluran", nav_bot: "Buka bot", cta_trial: "Cuba 3 hari", cta_guide: "Lihat panduan", pricing_title: "Harga jelas.", buy: "Beli dalam bot", final_btn: "Mulakan bot" },
  hi: { hero_title: "VPN जो कुछ सेकंड में कनेक्ट होता है.", nav_features: "फीचर", nav_pricing: "कीमत", nav_setup: "सेटअप", nav_faq: "FAQ", nav_channel: "चैनल", nav_bot: "बॉट खोलें", cta_trial: "3 दिन आज़माएं", cta_guide: "गाइड देखें", pricing_title: "स्पष्ट कीमतें.", buy: "बॉट में खरीदें", final_btn: "बॉट शुरू करें" }
};

// Текущий язык
let currentLang = 'ru';

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  init();
});

function init() {
  // Определяем язык браузера
  const browserLang = navigator.language.split('-')[0];
  const supportedLangs = Object.keys(base);
  
  if (supportedLangs.includes(browserLang)) {
    currentLang = browserLang;
  }
  
  // Устанавливаем язык в select
  const langSelect = document.getElementById('langSelect');
  if (langSelect) {
    langSelect.value = currentLang;
    langSelect.addEventListener('change', (e) => {
      setLang(e.target.value);
    });
  }
  
  // Применяем переводы
  setLang(currentLang);
}

// Смена языка
function setLang(lang) {
  currentLang = lang;
  
  // Объединяем базовые переводы с пакетами
  const translations = { ...base[lang] || base.ru, ...packs[lang] };
  
  // Обновляем все элементы с data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (translations[key]) {
      el.textContent = translations[key];
    }
  });
  
  // Сохраняем язык в localStorage
  localStorage.setItem('lang', lang);
}

// Перевод по ключу
function t(key) {
  const translations = { ...base[currentLang] || base.ru, ...packs[currentLang] };
  return translations[key] || key;
}