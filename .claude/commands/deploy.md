---
description: Задеплоить изменения на сервер (git add → commit → push → GitHub Actions)
---

Выполни деплой текущих изменений:

1. Проверь `git status` и `git diff --stat` — убедись что изменения корректны
2. `git add -A`
3. Составь осмысленный commit message по изменениям (feat/fix/refactor/docs)
4. `git commit -m "..."`
5. `git push origin master`
6. Сообщи что GitHub Actions запустился и деплой начался

Если есть ошибки при push — разберись и исправь без вопросов.
