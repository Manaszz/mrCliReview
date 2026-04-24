# Инструкция для тупого агента: как развернуть Hermes MR review

Эта инструкция нужна, чтобы **без импровизации, без ручного шаманства и без творческого переосмысления реальности** поднять поток:

**GitLab MR webhook → Hermes → OpenCode → комментарий в Merge Request**

Предусловие: **Hermes-agent уже развернут из коробки**.

---

## 1. Что должно уже существовать

До начала работ проверь, что у тебя есть:

1. Сервер или VM, где уже установлен и запускается Hermes.
2. Доступ в shell под пользователем, который может:
   - читать рабочий каталог Hermes
   - читать и писать в каталог проекта
   - перезапускать Hermes
3. Доступ к корпоративному GitLab по сети.
4. GitLab token с правами:
   - читать проект и MR
   - публиковать комментарии в MR
5. Установленный OpenCode, который уже умеет запускаться в non-interactive режиме.
6. Копия этого репозитория на сервере.

Если чего-то из этого нет, **не продолжай**. Сломанное окружение само себя не починит, хотя люди в это почему-то верят.

---

## 2. Какая ветка нужна

Нужная ветка в репозитории:

```bash
git fetch origin
git checkout feat/hermes-gitlab-mr-review
git pull --ff-only origin feat/hermes-gitlab-mr-review
```

Проверь, что в репозитории появились файлы:

- `deployment/hermes/config.hermes.example.yaml`
- `.hermes/skills/gitlab-mr-opencode-review/SKILL.md`
- `.hermes/skills/gitlab-mr-opencode-review/templates/opencode-review-prompt.md`
- `.hermes/skills/gitlab-mr-opencode-review/scripts/post_gitlab_note.sh`
- `docs/HERMES_MR_REVIEW_REDESIGN_RU.md`
- `docs/HERMES_SETUP_STUPID_AGENT_RU.md`

---

## 3. Рекомендуемая структура каталогов

Ниже пример. Можно использовать другой путь, но тогда **везде** поменяй его последовательно.

```text
/opt/mrCliReview
├── .hermes/
│   └── skills/
│       └── gitlab-mr-opencode-review/
├── deployment/
├── docs/
└── runtime/
    └── mr-review-workspaces/
```

Создай runtime-каталоги:

```bash
mkdir -p /opt/mrCliReview/runtime/mr-review-workspaces
```

---

## 4. Подготовь переменные окружения

Создай env-файл или экспортируй переменные вручную.

Пример:

```bash
export GITLAB_URL="https://gitlab.company.local"
export GITLAB_TOKEN="REPLACE_ME"
export GITLAB_WEBHOOK_SECRET="REPLACE_ME"
export HERMES_MR_ROOT="/opt/mrCliReview/runtime/mr-review-workspaces"
export OPENCODE_MODEL="gpt-5"
```

### Обязательные переменные

- `GITLAB_URL`
- `GITLAB_TOKEN`
- `GITLAB_WEBHOOK_SECRET`
- `HERMES_MR_ROOT`

### Необязательная

- `OPENCODE_MODEL`

Если у тебя есть отдельный env-файл Hermes, внеси значения туда.

---

## 5. Подключи skill из репозитория в Hermes

Открой Hermes config и внеси туда значения по образцу из файла:

`deployment/hermes/config.hermes.example.yaml`

### Ключевые параметры, которые должны быть в конфиге

#### Рабочая директория

```yaml
terminal:
  backend: local
  cwd: /opt/mrCliReview/runtime
```

#### Подключение skills из репозитория

```yaml
skills:
  external_dirs:
    - /opt/mrCliReview/.hermes/skills
```

#### Включение webhook платформы

```yaml
platforms:
  webhook:
    enabled: true
    host: 0.0.0.0
    port: 8644
    path_prefix: /webhooks
```

#### Route для GitLab MR

В конфиге должен быть route:

- `gitlab-mr-review`

Он должен:

- принимать `merge_request` events
- использовать `secret: ${GITLAB_WEBHOOK_SECRET}`
- прокидывать данные MR в prompt

Не придумывай своё имя route без причины. Иначе потом будешь удивляться, почему GitLab стучится не туда.

---

## 6. Проверь, что OpenCode вообще работает

Перед запуском webhook-потока убедись, что OpenCode запускается руками.

Простой smoke test:

```bash
opencode run "Reply with OK only" --format text
```

Ожидаемый результат: корректный текстовый ответ.

Если команда не работает, сначала почини OpenCode:

- бинарник должен быть в `PATH`
- auth должен быть настроен
- модель должна быть доступна

Пока OpenCode не работает, **не тестируй webhook**. Иначе это будет не интеграция, а коллекция ложных симптомов.

---

## 7. Проверь, что Hermes видит skill

Минимальная проверка: убедись, что путь из `skills.external_dirs` существует и содержит:

```bash
ls -R /opt/mrCliReview/.hermes/skills/gitlab-mr-opencode-review
```

Должны быть:

- `SKILL.md`
- `templates/opencode-review-prompt.md`
- `scripts/post_gitlab_note.sh`

Если у тебя есть привычный способ запускать одноразовые запросы через Hermes, выполни smoke test с подключённым skill. Например, через non-interactive команду Hermes. Проверка должна подтвердить, что профиль поднимается и external skill directory не ломает загрузку.

Если Hermes стартует, но skill не подхватывается, обычно виновато одно из трёх:

1. неверный путь в `skills.external_dirs`
2. не тот профиль Hermes
3. старый кэш / конфиг / не сделан restart

---

## 8. Перезапусти Hermes

После изменения конфига обязательно перезапусти Hermes тем способом, которым он у вас развёрнут.

Примеры:

- systemd service
- docker compose restart
- kubernetes rollout restart
- supervisor

Смысл действия один:

- Hermes должен перечитать конфиг
- webhook platform должна подняться
- route `gitlab-mr-review` должен стать доступным

После перезапуска проверь порт:

```bash
ss -ltnp | grep 8644
```

Если порт не слушается, значит webhook platform не поднялась.

---

## 9. Настрой webhook в GitLab

Открой настройки проекта в GitLab.

Путь обычно такой:

- **Project → Settings → Webhooks**

### Укажи URL webhook

Если Hermes доступен по hostname `hermes.company.local`, то URL будет таким:

```text
http://hermes.company.local:8644/webhooks/gitlab-mr-review
```

Если используется HTTPS и reverse proxy, укажи внешний HTTPS URL.

### Укажи secret token

В GitLab webhook secret должен **в точности** совпадать со значением:

- `GITLAB_WEBHOOK_SECRET`

### Включи события

Нужно включить:

- **Merge request events**

Остальные события для этой версии не нужны.

Сохрани webhook.

---

## 10. Выполни end-to-end тест

### Тестовый сценарий

1. Создай тестовую ветку.
2. Внеси маленькое изменение в код.
3. Открой Merge Request в GitLab.
4. Или обнови существующий MR новым push.

### Что должно произойти

1. GitLab отправит webhook в Hermes.
2. Hermes примет событие `merge_request`.
3. Hermes вызовет skill `gitlab-mr-opencode-review`.
4. Skill создаст рабочую папку:

```text
$HERMES_MR_ROOT/<project_id>/mr-<mr_iid>/
```

5. Внутри появятся артефакты:

- `repo/`
- `artifacts/diff.patch`
- `artifacts/opencode-prompt.md`
- `artifacts/opencode-output.md`
- `artifacts/final-comment.md`

6. В Merge Request появится комментарий с AI review.

---

## 11. Что проверять на диске

Пример команды:

```bash
find /opt/mrCliReview/runtime/mr-review-workspaces -maxdepth 4 -type f | sort
```

У успешного прогона должны быть минимум такие файлы:

```text
.../artifacts/diff.patch
.../artifacts/opencode-prompt.md
.../artifacts/opencode-output.md
.../artifacts/final-comment.md
```

Если `final-comment.md` есть, а комментария в GitLab нет, проблема почти наверняка в GitLab API token или URL.

---

## 12. Частые проблемы и что делать

### Проблема 1. GitLab webhook получает 401/403

Причины:

- не совпадает `GITLAB_WEBHOOK_SECRET`
- webhook route указан не тот
- reverse proxy режет headers

Что делать:

- перепроверь secret
- перепроверь URL `/webhooks/gitlab-mr-review`
- убедись, что `X-Gitlab-Token` доходит до Hermes

### Проблема 2. Hermes поднялся, но skill не исполняется

Причины:

- неверный путь в `skills.external_dirs`
- не тот профиль Hermes
- не был сделан restart

Что делать:

- проверь реальный путь
- проверь активный профиль
- перезапусти Hermes

### Проблема 3. Репозиторий не клонируется

Причины:

- Hermes сервер не имеет сетевого доступа до GitLab
- clone URL требует другой способ аутентификации
- GitLab token не годится для чтения repo

Что делать:

- проверь network connectivity до GitLab
- проверь, какой clone URL возвращает GitLab API
- при необходимости используй сервисный доступ, подходящий для clone/fetch

### Проблема 4. `diff.patch` пустой

Причины:

- source/target branches fetched неверно
- MR уже не содержит отличий
- checkout/reset выполнен не на ту ветку

Что делать:

- проверь руками:

```bash
cd <workspace>/repo
git fetch --all --prune
git checkout <source_branch>
git reset --hard origin/<source_branch>
git diff --binary origin/<target_branch>...HEAD
```

### Проблема 5. OpenCode не возвращает результат

Причины:

- не настроен auth
- модель недоступна
- команда `opencode run` не работает из shell-пользователя Hermes

Что делать:

- проверь `which opencode`
- выполни manual smoke test от того же пользователя
- проверь модель и права

### Проблема 6. Комментарий в MR не публикуется

Причины:

- плохой `GITLAB_TOKEN`
- неверный `GITLAB_URL`
- GitLab API недоступен

Что делать:

- проверь вручную curl-запросом:

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" "${GITLAB_URL%/}/api/v4/projects/<project_id>/merge_requests/<mr_iid>"
```

- затем проверь POST note через API

---

## 13. Минимальный definition of done

Считать настройку успешной можно только если выполнено всё ниже:

1. Hermes слушает webhook endpoint.
2. GitLab успешно отправляет `merge_request` webhook.
3. Skill `gitlab-mr-opencode-review` запускается.
4. Создаются рабочие артефакты в `HERMES_MR_ROOT`.
5. OpenCode возвращает review.
6. В исходном Merge Request появляется комментарий.

Если нет последнего пункта, внедрение **не закончено**.

---

## 14. Что не делать в этой версии

Не надо сразу пытаться прикручивать:

- автофиксы
- отдельный fix MR
- автокоммиты
- автолейблы
- мультиагентный fan-out на 12 типов review

Сначала добейся стабильной цепочки:

**GitLab MR → Hermes → OpenCode → GitLab comment**

Потом уже можно усложнять систему, как это любят делать люди, которым скучно на работающем проде.

---

## 15. Быстрый чек-лист

```text
[ ] Ветка feat/hermes-gitlab-mr-review выкачана
[ ] Hermes config обновлён
[ ] skills.external_dirs указывает на /opt/mrCliReview/.hermes/skills
[ ] GITLAB_URL задан
[ ] GITLAB_TOKEN задан
[ ] GITLAB_WEBHOOK_SECRET задан
[ ] HERMES_MR_ROOT создан
[ ] OpenCode smoke test проходит
[ ] Hermes перезапущен
[ ] GitLab webhook создан
[ ] Merge request test выполнен
[ ] Комментарий в MR появился
```

Если хотя бы один пункт не выполнен, не рассказывай, что «почти всё готово». Почти готово не ревьюит merge request.