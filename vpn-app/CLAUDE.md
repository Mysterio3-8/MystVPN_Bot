# CLAUDE.md — MystVPN App (iOS / Android клиент)

## Статус
🟡 **Не начато.** Папка-заготовка для будущего нативного клиента.

## Зачем своё приложение
- Контроль UX без зависимости от Hiddify / v2rayTUN / Streisand
- Свой бренд в App Store / Google Play
- Push-уведомления о подписке прямо в приложении
- Sign-in через Telegram → автоподтягивание ключа
- Одна кнопка «Подключить» — без копирования ссылок

## Технический выбор (черновой)
| Платформа | Подход | Причина |
|---|---|---|
| iOS | Swift + NetworkExtension | NEPacketTunnelProvider обязателен для VPN в App Store |
| Android | Kotlin + VpnService | Нативный VpnService без зависимостей |
| Кроссплатформа | ❌ Не Flutter / RN | NetworkExtension и VpnService требуют нативного кода |

## Архитектура (черновая)
```
app
 ├─ ui/                ← экраны (логин через TG, статус, тарифы)
 ├─ vpn-engine/        ← обёртка над xray-core / wireguard-go
 ├─ api-client/        ← HTTPS к backend боту (тот же бот, новый /api эндпоинт)
 └─ keychain/          ← хранение ключа подписки в защищённом хранилище
```

## OPSEC правила (читай ПЕРЕД написанием UI)
- В UI никогда не упоминаем «VLESS», «Reality», «xray», «WireGuard», «прокси»
- Тексты для юзера: «Подключение», «Защищённый канал», «Готово к работе»
- В описании в App Store / Google Play: «безопасный доступ», «обход блокировок» — без техники
- Логи на устройстве не пишем PII / реальные адреса серверов

## Связи с другими модулями
- `bot/` — backend API, шлёт ключ при логине
- `vpn-protocol/` — engine для туннеля (libxray.so / libwg.so)
- `site/` — landing с deep-link на установку приложения

## Когда начинать
**Не раньше, чем у бота будет 100+ платящих юзеров.** До этого — фокус на воронку и виралку через Telegram.

## Команды (когда стартанём)
```bash
# iOS
xcodebuild -scheme MystVPN -configuration Release
# Android
./gradlew assembleRelease
```
