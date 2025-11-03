# Offline NPM Packages

Эта папка используется для офлайн установки CLI инструментов в Docker.

## Подготовка пакетов (в среде с интернетом)

```bash
# Перейти в эту папку
cd offline-packages

# Скачать пакеты в формате .tgz
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Проверить
ls -lh *.tgz
```

Результат:
```
cline-cli-2.1.0.tgz
qwen-code-1.5.0.tgz
```

## Использование

После того как пакеты скачаны, просто запустите сборку:

```bash
# В корне проекта
docker-compose build
```

Docker автоматически найдёт и установит пакеты из этой папки.

## Проверка установки

```bash
# Запустить контейнер
docker-compose up -d

# Проверить CLI внутри контейнера
docker exec code-review-api cline --version
docker exec code-review-api qwen-code --version
```

## Структура

```
offline-packages/
├── .gitignore              # Игнорирует .tgz файлы
├── README.md               # Эта инструкция
├── cline-cli-2.1.0.tgz    # Пакет Cline CLI (не в git)
└── qwen-code-1.5.0.tgz    # Пакет Qwen Code (не в git)
```

## Примечание

Файлы *.tgz НЕ коммитятся в Git (слишком большие). Каждый разработчик должен скачать их самостоятельно в среде с интернетом.


