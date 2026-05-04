# CLAUDE.md — VPN-Site (keybest.cc)

## Что это
Лендинг MystVPN на домене keybest.cc. Статический сайт без бэкенда.

## Структура
- `index.html` — главная страница
- `css/styles.css` — все стили
- `js/app.js` — i18n (RU/EN), анимации, переключатель языка
- `pages/` — подстраницы: features, pricing, setup, faq

## Деплой
Файлы копируются в `/var/www/guide/` при каждом git push → GitHub Actions.
nginx раздаёт их напрямую с домена keybest.cc.

## Правила
- Пути к CSS/JS всегда абсолютные: `/css/styles.css`, `/js/app.js`
- Переводы через `data-i18n="ключ"` + ключи в `js/app.js` в объекте `translations`
- Поддерживаемые языки: только RU и EN
- OPSEC: никогда не упоминать VLESS, Reality, xray, прокси — только «обход блокировок»
