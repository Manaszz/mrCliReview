# 📋 Кто что делает: CLI vs FastAPI (Краткая версия)

## ⚡ Главный принцип

**CLI = Анализ кода**  
**FastAPI = Git + GitLab + Оркестрация**

---

## 🎯 Что CLI отдаёт в ответ?

### JSON структура:

```json
{
  "issues": [
    {
      "file": "UserService.java",
      "line": 45,
      "severity": "HIGH",
      "message": "Potential NullPointerException",
      "suggestion": "Add null check",
      "auto_fixable": true
    }
  ],
  
  "refactoring_suggestions": [
    {
      "file": "UserService.java",
      "message": "Method too long (150 lines)",
      "suggestion": "Extract validation logic",
      "impact": "SIGNIFICANT"
    }
  ],
  
  "documentation_additions": [
    {
      "file": "UserService.java",
      "line": 25,
      "type": "JAVADOC",
      "generated_doc": "/** ... */"
    }
  ],
  
  "files_modified": [
    {
      "file": "UserService.java",
      "changes": [...]
    }
  ],
  
  "summary": {
    "total_issues": 15,
    "critical": 2,
    "auto_fixable_count": 8
  }
}
```

---

## 📊 Таблица ответственности

| Операция | CLI | FastAPI | Кто делает |
|----------|:---:|:-------:|------------|
| **Анализ кода** | ✅ | ❌ | CLI читает и анализирует |
| **Обнаружение багов** | ✅ | ❌ | CLI находит проблемы |
| **Генерация Javadoc** | ✅ | ❌ | CLI генерирует текст |
| **Запись в файлы** | ✅ | ❌ | CLI пишет Javadoc/fixes |
| **git diff** | ✅ | ✅ | Оба используют |
| | | | |
| **git clone** | ❌ | ✅ | FastAPI с credentials |
| **git commit** | ❌ | ✅ | FastAPI контролирует |
| **git push** | ❌ | ✅ | FastAPI с credentials |
| **git branch create** | ❌ | ✅ | FastAPI для MR |
| **GitLab API** | ❌ | ✅ | FastAPI все операции |
| **Создать MR** | ❌ | ✅ | FastAPI через API |
| **Добавить комментарий** | ❌ | ✅ | FastAPI публикует |
| **Классификация refactoring** | ❌ | ✅ | FastAPI бизнес-логика |

---

## 🔄 Flow: Кто что делает

### 1️⃣ Только ремарки (comments only)

```
FastAPI:
├─ Clone repo + Fetch target branch
├─ Запустить CLI
└─ Опубликовать комментарии в MR

CLI:
├─ git diff origin/main (получить изменённые файлы)
├─ Прочитать и проанализировать код
├─ Найти проблемы
└─ Вернуть JSON с issues
```

**Результат:** Комментарии в GitLab MR

---

### 2️⃣ Review + Auto-documentation

```
FastAPI:
├─ Clone repo + Fetch target branch
├─ Запустить CLI с enable_auto_documentation=true
├─ [CLI вернул JSON + изменил файлы]
├─ Обнаружить изменённые файлы
├─ git commit -m "docs: Add Javadoc"
├─ git push origin feature-branch
└─ Добавить note в MR "✅ Added Javadoc (commit abc123)"

CLI:
├─ git diff origin/main
├─ Анализировать код
├─ Сгенерировать Javadoc
├─ ЗАПИСАТЬ Javadoc в файлы ⬅️ CLI пишет!
└─ Вернуть JSON с files_modified
```

**Результат:** Javadoc в исходной MR + note

---

### 3️⃣ Significant refactoring → отдельный MR

```
FastAPI:
├─ Clone repo + Fetch target branch
├─ Запустить CLI
├─ [CLI вернул refactoring suggestions]
├─ Классифицировать: SIGNIFICANT → отдельный MR
├─ git checkout origin/main
├─ git checkout -b refactor/extract-methods
├─ [Опционально: запустить CLI apply refactoring]
├─ git commit -m "refactor: Extract validation"
├─ git push origin refactor/extract-methods
├─ GitLab API: создать MR
│   source: refactor/extract-methods
│   target: main
│   title: "🤖 [AI] Refactor: Extract methods"
└─ Добавить ссылку в исходный MR "✨ Created MR !789"

CLI:
├─ Анализировать код
├─ Найти сложные методы
├─ Предложить refactoring (impact=SIGNIFICANT)
└─ [Опционально: применить refactoring если включено]
```

**Результат:** 
- Новый MR для refactoring
- Ссылка в исходном MR

---

## 🔧 Конфигурация

```python
class ReviewRequest:
    # Что CLI должен делать
    enable_auto_documentation: bool = False  # CLI генерирует Javadoc
    enable_auto_fixes: bool = False          # CLI применяет фиксы
    
    # Что FastAPI должен делать
    commit_documentation: bool = False       # FastAPI коммитит
    commit_auto_fixes: bool = False          # FastAPI коммитит
    create_refactoring_mr: bool = True       # FastAPI создаёт MR
    post_mr_comments: bool = True            # FastAPI публикует
```

### Примеры:

**Только review (ничего не меняем):**
```json
{
  "enable_auto_documentation": false,
  "enable_auto_fixes": false,
  "create_refactoring_mr": false,
  "post_mr_comments": true
}
```
→ CLI анализирует, FastAPI публикует комментарии

**Review + Javadoc:**
```json
{
  "enable_auto_documentation": true,
  "commit_documentation": true,
  "post_mr_comments": true
}
```
→ CLI генерирует + пишет Javadoc, FastAPI коммитит + пушит

**Full automation:**
```json
{
  "enable_auto_documentation": true,
  "commit_documentation": true,
  "enable_auto_fixes": true,
  "commit_auto_fixes": true,
  "create_refactoring_mr": true,
  "post_mr_comments": true
}
```
→ CLI делает всё что может, FastAPI коммитит + создаёт MR

---

## 💡 Итого

### CLI делает:
- ✅ Анализирует код (главная задача)
- ✅ Генерирует Javadoc
- ✅ Применяет автоматические фиксы
- ✅ **Пишет в файлы** (если разрешено)
- ❌ НЕ коммитит
- ❌ НЕ пушит
- ❌ НЕ создаёт MR/ветки

### FastAPI делает:
- ✅ Клонирует репозиторий
- ✅ Запускает CLI
- ✅ Обнаруживает изменения от CLI
- ✅ **Коммитит изменения** (если CLI изменил файлы)
- ✅ **Пушит в GitLab**
- ✅ **Создаёт ветки** для refactoring
- ✅ **Создаёт MR** через API
- ✅ **Публикует комментарии** в GitLab
- ❌ НЕ анализирует код

---

## 🎯 Ключевое различие

**CLI работает с локальными файлами:**
- Читает
- Анализирует  
- Пишет (если разрешено)

**FastAPI работает с Git/GitLab:**
- Клонирует
- Коммитит
- Пушит
- Создаёт MR
- Публикует результаты

---

## 📚 Полная версия

См. [docs/CLI_RESPONSIBILITY_SEPARATION.md](docs/CLI_RESPONSIBILITY_SEPARATION.md) для:
- Детальных диаграмм flow
- Примеров JSON ответов
- Полного кода сценариев
- Всех опций конфигурации

---

**TL;DR:** CLI = анализ + генерация + запись в файлы. FastAPI = Git + GitLab + оркестрация.


