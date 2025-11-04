# Документ требований к продукту: Мультиагентная система Code Review

**Версия:** 2.0.0  
**Дата:** Ноябрь 2025  
**Статус:** Активная разработка  
**Целевая аудитория:** Java Spring Boot приложения (расширяемо на другие языки)

---

## Краткое резюме

### Видение

Создать интеллектуальную, автоматизированную систему code review, которая использует современные CLI-based AI агенты (Cline и Qwen Code) для предоставления всестороннего, многомерного анализа Java Spring Boot merge requests. Система направлена на снижение нагрузки ручного ревью, выявление критических проблем до продакшена и последовательное применение стандартов кодирования в командах разработчиков.

### Цели

1. **Всесторонний охват**: Поддержка 13 специализированных типов ревью, покрывающих ошибки, безопасность, производительность, архитектуру, лучшие практики, покрытие тестами и управление знаниями
2. **Гибкость**: Возможность выбора конкретных типов ревью на основе контекста и срочности
3. **Двухагентная архитектура**: Выбор между Cline CLI (DeepSeek V3.1 Terminus) и Qwen Code CLI (Qwen3-Coder) для различных случаев использования
4. **Умное создание MR**: Автоматическая генерация fix MR с интеллектуальным разделением критических исправлений от предложений по рефакторингу, с правильной стратегией веток (ветвление от MR source, не target)
5. **Автоматизация покрытия тестами**: Автоматическая генерация недостающих юнит-тестов по конвенциям проекта (JUnit5, Mockito, Testcontainers)
6. **Управление знаниями**: Автообновление Memory Bank проекта с каждым MR для живой документации
7. **Кастомизируемость**: Поддержка правил и конвенций, специфичных для проекта, через иерархическую систему правил
8. **Контекстно-зависимые ревью**: System prompt с интеграцией Memory Bank для рекомендаций, основанных на контексте
9. **Готовность к продакшену**: Docker Compose развёртывание с поддержкой Kubernetes и возможностью air-gap передачи

### Целевые пользователи

- **Основные**: Команды разработки Java Spring Boot, работающие с GitLab
- **Вторичные**: DevOps команды, управляющие пайплайнами качества кода
- **Третичные**: Технические лидеры и архитекторы, применяющие стандарты кодирования

---

## Обзор архитектуры

### Архитектура системы

```
GitLab MR Event
    ↓
n8n Workflow (валидация)
    ↓
Review API (FastAPI)
    ↓
Review Service (выбор агента)
    ↓
┌─────────────────┬──────────────────┐
│  Cline CLI      │  Qwen Code CLI   │
│  (DeepSeek V3.1)│  (Qwen3-Coder)   │
└─────────────────┴──────────────────┘
    ↓
Клонированный репозиторий (локальный анализ)
    ↓
Агрегация результатов
    ↓
┌──────────────────┬─────────────────┬────────────────┐
│ Javadoc Commit   │ Fixes MR        │ Refactoring MR │
│ (source branch)  │ (критические)   │ (если значимые)│
└──────────────────┴─────────────────┴────────────────┘
    ↓
GitLab комментарии & уведомления
```

### Ключевые архитектурные решения

#### 1. CLI-based агенты (не прямые вызовы моделей)

**Решение**: Использовать Cline CLI и Qwen Code CLI вместо прямых API вызовов к языковым моделям.

**Обоснование**:
- CLI агенты имеют встроенное управление контекстом и памятью
- Лучшее понимание кода через нативную индексацию репозитория
- Возможности анализа нескольких файлов и перекрёстных ссылок
- Способность работать с большими кодовыми базами через интеллектуальное разбиение
- Встроенный анализ diff и обнаружение изменений

#### 2. Выполнение одного агента (не комбинированное)

**Решение**: Всегда выполнять либо Cline, ЛИБО Qwen Code, никогда оба одновременно.

**Обоснование**:
- Предотвращает конфликтующие рекомендации
- Более простая интерпретация результатов
- Меньшее потребление ресурсов
- Более чёткая атрибуция ответственности
- Более простая отладка и отслеживание проблем

#### 3. Минимальное использование GitLab API

**Решение**: Клонировать репозиторий локально и выполнять весь анализ на клонированном коде.

**Обоснование**:
- Снижает проблемы с rate limit API
- Позволяет CLI агентам использовать нативные git операции
- Лучшая производительность для больших diff
- CLI агенты работают лучше с локальными репозиториями
- Более простая обработка ошибок

#### 4. Стратегия клонирования репозитория

**Решение**: Клонировать полную MR source branch для каждого ревью.

**Обоснование**:
- CLI агенты требуют полного контекста репозитория
- Позволяет точный анализ между файлами
- Позволяет агентам понимать структуру проекта
- Поддерживает предложения по рефакторингу, охватывающие несколько файлов
- Cleanup после ревью поддерживает изоляцию

#### 5. System Prompt с интеграцией Memory Bank

**Решение**: Использовать глобальный system prompt, который препендится ко всем запросам на ревью, со встроенной осведомлённостью о Memory Bank.

**Обоснование**:
- Обеспечивает консистентные стандарты стиля кода во всех ревью (использование Lombok, конвенции Java и т.д.)
- Загружается один раз при запуске и кэшируется для производительности
- Инструктирует агентов проверять и читать директорию `memory-bank/` для контекста проекта
- Предоставляет базовые правила без их передачи в каждом запросе
- Позволяет контекстно-зависимые рекомендации, выровненные с решениями проекта
- Уменьшает размер промпта для отдельных запросов

**Функции System Prompt**:
- Форматирование Java и конвенции Spring Boot
- Руководство по использованию Lombok
- Критерии обнаружения code smells
- Уровни серьёзности ревью
- Инструкции по интеграции Memory Bank
- Требования к формату вывода

---

## Основные функции

### 1. Система многотипного ревью (13 типов)

#### ERROR_DETECTION
**Назначение**: Идентифицировать баги, потенциальные падения и логические ошибки

**Проверки**:
- Паттерны предотвращения NullPointerException
- Правильность использования Optional
- Анти-паттерны обработки исключений (пустые catch блоки, проглатывание исключений)
- Try-with-resources для AutoCloseable ресурсов
- Нарушения типобезопасности
- Непроверенные касты и raw types
- Отсутствующие null проверки на границах

**Примеры проблем**:
```java
// ПЛОХО: Потенциальный NPE
public void process(User user) {
    String name = user.getName().toUpperCase(); // NPE если getName() возвращает null
}

// ХОРОШО: Защитное программирование
public void process(User user) {
    String name = Optional.ofNullable(user.getName())
        .map(String::toUpperCase)
        .orElse("UNKNOWN");
}
```

#### BEST_PRACTICES
**Назначение**: Применять принципы SOLID, DRY, KISS и конвенции Spring Boot

**Проверки**:
- Нарушения принципов SOLID (SRP, OCP, LSP, ISP, DIP)
- Нарушения DRY (дублирование кода)
- Чрезмерно сложные методы (высокая цикломатическая сложность)
- Правильное использование Records для неизменяемых data классов
- Sealed классы для контролируемого наследования
- Использование Pattern Matching (Java 17+)
- Правильное использование Generics (избегание raw types, правильное использование wildcard)
- Конвенции Spring Boot (использование @Service, @Repository, @Component)
- Паттерны внедрения зависимостей (предпочтительно constructor injection)
- Размещение @Transactional (service layer, не repository)

**Примеры проблем**:
```java
// ПЛОХО: Бизнес-логика в контроллере
@RestController
public class UserController {
    @Autowired
    private UserRepository repo;
    
    @PostMapping("/users")
    public User createUser(@RequestBody UserDto dto) {
        // Логика валидации в контроллере
        if (dto.getAge() < 18) throw new IllegalArgumentException("Too young");
        
        // Бизнес-логика в контроллере
        User user = new User();
        user.setName(dto.getName());
        user.setAge(dto.getAge());
        user.setCreatedAt(LocalDateTime.now());
        
        return repo.save(user);
    }
}

// ХОРОШО: Разделение ответственностей
@RestController
public class UserController {
    private final UserService userService;
    
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    @PostMapping("/users")
    public User createUser(@Valid @RequestBody UserDto dto) {
        return userService.createUser(dto);
    }
}

@Service
public class UserService {
    private final UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    @Transactional
    public User createUser(UserDto dto) {
        // Бизнес-логика здесь
    }
}
```

#### REFACTORING
**Назначение**: Предлагать улучшения кода для поддерживаемости и читаемости

**Проверки**:
- Обнаружение циклических зависимостей
- Бизнес-логика в контроллерах (должна быть в сервисах)
- Длинные методы (>50 строк)
- Длинные классы (>500 строк)
- Глубокая вложенность (>3 уровней)
- Magic numbers (должны быть константами)
- Дублирование кода
- Сложные boolean выражения
- Блокирующие вызовы в reactive коде

**Классификация**:
- **SIGNIFICANT** (отдельный MR): >3 затронутых классов, breaking changes, >200 LOC, изменения DI структуры, миграции паттернов
- **MINOR** (объединённые с fixes): переименование переменных, извлечение констант, форматирование, упрощение условий

#### SECURITY_AUDIT
**Назначение**: Идентифицировать уязвимости безопасности и риски

**Проверки**:
- SQL injection (непараметризованные запросы)
- XSS уязвимости (некодированный output)
- Конфигурация CSRF защиты
- Валидация входных данных (использование Bean Validation)
- Проверки аутентификации/авторизации
- Безопасное использование @Transactional (правильная изоляция)
- Захардкоженные credentials
- Небезопасная генерация случайных чисел
- Уязвимости path traversal
- End-of-life зависимости (EOL Spring Boot/Framework версии)

**Примеры проблем**:
```java
// ПЛОХО: Уязвимость SQL Injection
@Repository
public class UserRepository {
    @Autowired
    private JdbcTemplate jdbc;
    
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
        return jdbc.queryForObject(sql, new UserRowMapper());
    }
}

// ХОРОШО: Параметризованный запрос
@Repository
public class UserRepository {
    @Autowired
    private JdbcTemplate jdbc;
    
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = ?";
        return jdbc.queryForObject(sql, new UserRowMapper(), username);
    }
}
```

#### DOCUMENTATION
**Назначение**: Генерировать и проверять качество документации кода

**Проверки**:
- Отсутствующий Javadoc на публичных API
- Полнота Javadoc (@param, @return, @throws)
- Наличие осмысленных комментариев
- Самодокументирующийся код (чёткое именование)
- Стандарты документации API
- Обновления README для новых функций

**Автогенерация**:
- Javadoc для публичных методов
- Документация уровня класса
- Package-info.java для пакетов

**Стратегия коммита**: Улучшения документации коммитятся напрямую в MR source branch.

#### PERFORMANCE
**Назначение**: Идентифицировать проблемы производительности и возможности оптимизации

**Проверки**:
- Обнаружение N+1 запросов в JPA (@OneToMany, @ManyToOne lazy loading)
- Отсутствующие @EntityGraph или JOIN FETCH
- Блокирующие вызовы в reactive коде (Project Reactor, RxJava)
- Неэффективное использование Stream API
- Неправильное использование parallel stream
- Неправильная конфигурация connection pool (HikariCP)
- Отсутствующие возможности кэширования
- Неэффективные операции с коллекциями
- Большие аллокации объектов в циклах

**Примеры проблем**:
```java
// ПЛОХО: Проблема N+1 запроса
@Service
public class OrderService {
    public List<OrderDto> getAllOrders() {
        List<Order> orders = orderRepository.findAll(); // 1 запрос
        return orders.stream()
            .map(order -> {
                List<Item> items = order.getItems(); // N запросов (lazy loading)
                return new OrderDto(order, items);
            })
            .collect(Collectors.toList());
    }
}

// ХОРОШО: JOIN FETCH
@Service
public class OrderService {
    public List<OrderDto> getAllOrders() {
        List<Order> orders = orderRepository.findAllWithItems(); // 1 запрос
        return orders.stream()
            .map(order -> new OrderDto(order, order.getItems()))
            .collect(Collectors.toList());
    }
}

// Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    @Query("SELECT o FROM Order o LEFT JOIN FETCH o.items")
    List<Order> findAllWithItems();
}
```

#### ARCHITECTURE
**Назначение**: Проверять архитектурные паттерны и лучшие практики микросервисов

**Проверки**:
- Реализация Circuit Breaker (Resilience4j)
- Паттерны API Gateway
- Соответствие Database per Service (микросервисы)
- Паттерны коммуникации service-to-service
- Паттерны event-driven архитектуры
- Стратегия версионирования API (URL path vs content negotiation)
- Реализация пагинации REST API
- Конфигурация CORS
- Правильное использование DTO для разделения слоёв

**Примеры проблем**:
```java
// ПЛОХО: Прямой доступ к БД через сервисы
@Service
public class OrderService {
    @Autowired
    private UserRepository userRepository; // Cross-service DB доступ
    
    public Order createOrder(Long userId) {
        User user = userRepository.findById(userId).orElseThrow();
        // ...
    }
}

// ХОРОШО: Service-to-service через API
@Service
public class OrderService {
    private final UserServiceClient userClient;
    
    public OrderService(UserServiceClient userClient) {
        this.userClient = userClient;
    }
    
    @CircuitBreaker(name = "userService", fallbackMethod = "createOrderFallback")
    public Order createOrder(Long userId) {
        UserDto user = userClient.getUser(userId);
        // ...
    }
    
    public Order createOrderFallback(Long userId, Exception e) {
        // Fallback логика
    }
}
```

#### TRANSACTION_MANAGEMENT
**Назначение**: Проверять правильную конфигурацию и использование транзакций

**Проверки**:
- Размещение @Transactional (service layer, не repository)
- Правильность уровней propagation (REQUIRED, REQUIRES_NEW, NESTED)
- Соответствие уровней isolation (READ_COMMITTED, REPEATABLE_READ)
- Оптимизация read-only транзакций
- Правильность границ транзакций
- Избегание @Transactional на private методах
- Правильная обработка исключений в транзакциях

**Примеры проблем**:
```java
// ПЛОХО: Чрезмерное использование @Transactional
@Service
public class UserService {
    @Transactional // Ненужно для read-only
    public User findById(Long id) {
        return userRepository.findById(id).orElseThrow();
    }
}

// ХОРОШО: Read-only транзакция
@Service
public class UserService {
    @Transactional(readOnly = true)
    public User findById(Long id) {
        return userRepository.findById(id).orElseThrow();
    }
    
    @Transactional // Write операция
    public User createUser(UserDto dto) {
        User user = new User();
        // ... настройка user
        return userRepository.save(user);
    }
}
```

#### CONCURRENCY
**Назначение**: Идентифицировать проблемы конкурентности и оптимизировать конкурентный код

**Проверки**:
- Обнаружение race conditions
- Правильное использование синхронизации
- Использование Virtual threads (Java 21+)
- Конфигурация и паттерны @Async
- Правильное использование CompletableFuture
- Использование thread-safe коллекций
- Неизменяемость для конкурентного доступа
- Избегание разделяемого изменяемого состояния

**Примеры проблем**:
```java
// ПЛОХО: Race condition
public class Counter {
    private int count = 0;
    
    public void increment() {
        count++; // Не потокобезопасно
    }
}

// ХОРОШО: Атомарные операции
public class Counter {
    private final AtomicInteger count = new AtomicInteger(0);
    
    public void increment() {
        count.incrementAndGet();
    }
}
```

#### DATABASE_OPTIMIZATION
**Назначение**: Оптимизировать запросы к БД и паттерны доступа к данным

**Проверки**:
- Отсутствующие индексы на часто запрашиваемых колонках
- Использование @EntityGraph для оптимизации fetch
- Стратегия lazy vs eager loading
- Использование batch операций
- Query projection для больших сущностей
- Правильная реализация пагинации
- Sizing connection pool
- Кэширование результатов запросов

**Примеры проблем**:
```java
// ПЛОХО: Получение полной сущности когда нужно несколько полей
@Service
public class UserService {
    public List<String> getAllUsernames() {
        return userRepository.findAll().stream()
            .map(User::getUsername)
            .collect(Collectors.toList());
    }
}

// ХОРОШО: Projection запрос
@Service
public class UserService {
    public List<String> getAllUsernames() {
        return userRepository.findAllUsernames();
    }
}

public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT u.username FROM User u")
    List<String> findAllUsernames();
}
```

#### UNIT_TEST_COVERAGE (Обязательный)
**Назначение**: Автоматически проверять покрытие изменений кода юнит-тестами и генерировать недостающие тесты

**Проверки**:
- Обнаружение всех изменённых файлов через `git diff`
- Идентификация соответствующих файлов тестов
- Проверка наличия тестов для новых методов/классов
- Валидация качества и полноты тестов

**Автогенерация**:
- Полный, готовый к использованию код тестов
- Следует конвенциям проекта (именование, структура, базовые классы)
- Использует современные фреймворки тестирования:
  - JUnit 5
  - Mockito для моков
  - TestContainers для интеграционных тестов
- Наследуется от базовых тестовых классов проекта (если есть):
  - `JupiterBase`, `JupiterArtemisBase`, `JupiterNuxeoBase` и т.д.

**Покрываемые тестовые сценарии**:
- Happy path (нормальное выполнение)
- Граничные случаи (null значения, пустые коллекции, границы)
- Ошибочные случаи (исключения, ошибки валидации)
- Варианты бизнес-логики

**Пример вывода**:
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest extends JupiterBase {
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void shouldReturnUserWhenIdExists() {
        // Given
        Long userId = 1L;
        User expectedUser = new User(userId, "John Doe");
        when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));
        
        // When
        User actualUser = userService.getUserById(userId);
        
        // Then
        assertThat(actualUser).isNotNull();
        assertThat(actualUser.getId()).isEqualTo(userId);
        verify(userRepository).findById(userId);
    }
}
```

**Когда выполняется**: 
- **По умолчанию**: Всегда включён в процесс ревью
- **Можно отключить**: Указать `review_types` без `UNIT_TEST_COVERAGE`

---

#### MEMORY_BANK (Опциональный)
**Назначение**: Инициализировать или валидировать Memory Bank проекта - структурированную базу знаний для AI-разработки

**Что такое Memory Bank**:
Основан на методологии **Cursor's Memory Bank (v1.2 Final)**. Коллекция markdown файлов, предоставляющих полный контекст проекта:

1. **projectbrief.md** - Scope проекта, цели и требования
2. **productContext.md** - Почему проект существует, какие проблемы решает
3. **systemPatterns.md** - Архитектура, паттерны проектирования, технические решения
4. **techContext.md** - Технологический стек, зависимости, настройка
5. **activeContext.md** - Текущий фокус работы, недавние изменения, следующие шаги
6. **progress.md** - Что работает, что осталось сделать, известные проблемы

**Режимы работы**:

1. **Режим обновления (ОСНОВНОЙ)**: Когда Memory Bank существует
   - **CLI Агент**:
     - Анализирует изменения MR через `git diff`
     - Определяет какие файлы нужно обновить
     - **ЗАПИСЫВАЕТ** обновлённое содержимое в файлы Memory Bank:
       - `activeContext.md` - недавние изменения (ОБЯЗАТЕЛЬНО)
       - `systemPatterns.md` - если есть архитектурные изменения
       - `techContext.md` - если добавлены новые зависимости/технологии
       - `progress.md` - если завершены функции или изменился статус
       - `changelog.md` - запись о MR (ОБЯЗАТЕЛЬНО)
     - Возвращает `files_modified` в JSON
   - **FastAPI**:
     - Обнаруживает изменённые файлы в `memory-bank/`
     - Стейджит: `git add memory-bank/`
     - Коммитит с тегом `[skip ci]`
     - Пушит в ветку MR

2. **Режим инициализации**: Когда Memory Bank не существует
   - Анализирует весь проект (структура, build конфигурация, главные классы, пакеты)
   - Идентифицирует технологии (язык, фреймворк, БД, система сборки)
   - Создаёт полную структуру Memory Bank со всеми 6 core файлами

3. **Режим валидации (РЕДКО)**: Когда нужна валидация
   - Проверяет структуру и полноту
   - Отчитывается о проблемах

**Интеграция с System Prompt**:
- System prompt инструктирует всех агентов проверять наличие директории `memory-bank/`
- Если найдена, агенты читают ключевые файлы для контекста перед ревью
- Рекомендации выравниваются с задокументированными архитектурными решениями

**Разделение ответственности CLI/FastAPI**:
- **CLI агенты**: Анализируют и ЗАПИСЫВАЮТ в файлы (нет доступа к Git)
- **FastAPI**: Обрабатывает все Git операции (commit, push)

**Когда выполняется**:
- **По явному запросу**: Включить `MEMORY_BANK` в `review_types`
- **Опционально**: Не входит в стандартный процесс ревью
- **Рекомендуется**: Включать в каждый MR для автообновления Memory Bank

---

#### ALL (По умолчанию)
**Назначение**: Выполнить все типы ревью для всестороннего анализа

**Поведение**: Когда параметр `review_types` содержит `ALL` или не указан, все 13 специализированных типов ревью выполняются параллельно (на основе ёмкости CLI: 5 для Cline, 3 для Qwen).

---

### 2. Поддержка двух CLI агентов

#### Cline CLI (Основной)

**Модель**: DeepSeek V3.1 Terminus  
**Параллельные задачи**: 5  
**Сильные стороны**:
- Превосходное понимание контекста
- Лучше в сложных предложениях по рефакторингу
- Отличный анализ безопасности
- Сильные архитектурные инсайты
- Всесторонняя генерация документации

**Распределение задач**:
1. ERROR_DETECTION + UNIT_TEST_COVERAGE
2. BEST_PRACTICES + ARCHITECTURE
3. REFACTORING + PERFORMANCE
4. SECURITY_AUDIT + TRANSACTION_MANAGEMENT
5. DOCUMENTATION + CONCURRENCY + DATABASE_OPTIMIZATION + MEMORY_BANK

#### Qwen Code CLI (Альтернатива)

**Модель**: Qwen3-Coder-32B  
**Параллельные задачи**: 3  
**Сильные стороны**:
- Быстрое выполнение
- Сильное обнаружение ошибок
- Хорошее распознавание паттернов кода
- Эффективно для сфокусированных ревью

**Распределение задач**:
1. ERROR_DETECTION + SECURITY_AUDIT + UNIT_TEST_COVERAGE
2. BEST_PRACTICES + PERFORMANCE
3. REFACTORING + DATABASE_OPTIMIZATION + MEMORY_BANK

#### Стратегия выбора агента

**По умолчанию**: Cline (более всесторонний)

**Когда использовать Qwen**:
- Требуется быстрый оборот
- Сфокусированные ревью (1-3 типа ревью)
- Ограниченные вычислительные ресурсы
- Фокус на обнаружении ошибок + безопасности

**Конфигурация**: Задайте через переменную окружения `DEFAULT_CLI_AGENT` или параметр `agent` в API запросе.

---

### 3. Умное создание MR

#### Коммиты документации (Немедленно)

**Цель**: MR source branch  
**Содержимое**: Javadoc и комментарии кода  
**Время**: Коммитится сразу после завершения ревью  
**Обоснование**: Документация улучшает качество оригинального MR без изменения логики

#### Коммиты юнит-тестов (Немедленно)

**Цель**: MR source branch  
**Содержимое**: Сгенерированные юнит-тесты для непокрытого кода  
**Время**: Коммитится сразу после UNIT_TEST_COVERAGE ревью  
**Обоснование**: Тесты улучшают качество оригинального MR и обеспечивают покрытие кода

#### Обновления Memory Bank (Немедленно)

**Цель**: MR source branch  
**Содержимое**: Обновлённые файлы Memory Bank (activeContext.md, changelog.md и т.д.)  
**Время**: Коммитится сразу после MEMORY_BANK ревью с тегом `[skip ci]`  
**Обоснование**: Поддерживает актуальность базы знаний проекта с каждым изменением

#### Fixes MR (Критические проблемы)

**Цель**: Новая ветка от **MR source branch** (НЕ от target branch)  
**Source Branch**: `{original_mr_source_branch}`  
**Target Branch**: `{original_mr_source_branch}` (для MR)  
**Содержимое**: 
- Критические исправления багов (предотвращение NPE, обработка исключений)
- Патчи уязвимостей безопасности
- Критические проблемы производительности (исправления N+1 запросов)

**Именование ветки**: `fix/mr-{iid}-ai-review-fixes`  
**Описание**: Детальный список исправлений со ссылками на оригинальные проблемы  
**Автослияние**: Нет (требуется одобрение разработчика)

**Обоснование стратегии веток**:
Создание fix ветки от MR source branch позволяет разработчику:
1. Просмотреть и слить исправления в свою feature ветку сначала
2. Протестировать объединённые изменения
3. Затем слить улучшенную feature ветку в main target branch
4. Избегает конфликтов и поддерживает чистую историю слияний

#### Refactoring MR (Условно)

**Логика решения**:
```python
if refactoring_classifier.classify(suggestions) == "SIGNIFICANT":
    create_separate_refactoring_mr()
else:
    include_in_fixes_mr()
```

**Цель**: Новая ветка от **MR source branch** (НЕ от target branch)  
**Source Branch**: `{original_mr_source_branch}`  
**Target Branch**: `{original_mr_source_branch}` (для MR)

**Критерии SIGNIFICANT**:
- Более 3 затронутых классов
- Breaking changes публичных API
- Более 200 строк изменённого кода
- Модификации структуры внедрения зависимостей
- Миграции паттернов (например, callback hell в CompletableFuture)

**Критерии MINOR**:
- Переименования переменных/методов
- Извлечение констант
- Форматирование кода
- Упрощение условий
- Локальный рефакторинг внутри методов

**Именование ветки**: `refactor/mr-{iid}-ai-suggestions`  
**Описание**: Обоснование для каждого рефакторинга с примерами кода

**Обоснование стратегии веток**: То же что и для Fixes MR - позволяет разработчику интегрировать рефакторинг в свою feature ветку перед слиянием в main

---

### 4. Иерархическая система правил

#### Приоритет правил (от высшего к низшему)

1. **Правила конкретного проекта** (`.project-rules/` в корне репозитория)
2. **Правила Confluence** (получаемые через n8n workflow)
3. **Правила по умолчанию** (`rules/java-spring-boot/` в review service)

#### Структура правил

Каждый файл правил содержит:
- **Обзор**: Назначение и scope
- **Паттерны**: Паттерны кода для обнаружения (положительные и отрицательные примеры)
- **Уровни серьёзности**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Возможность автоисправления**: Может ли проблема быть автоисправлена
- **Примеры**: Фрагменты кода до/после
- **Ссылки**: Ссылки на документацию и лучшие практики

#### Правила конкретного проекта

**Расположение**: Директория `.project-rules/` в репозитории проекта  
**Формат**: Markdown файлы, соответствующие структуре по умолчанию  
**Использование**: Автоматически обнаруживаются и загружаются во время ревью  
**Поведение переопределения**: Правила проекта полностью переопределяют правила по умолчанию для той же проверки

**Пример**: Требование изоляции транзакций, специфичное для проекта
```markdown
# transaction_management.md

## Уровень изоляции по умолчанию

**Правило**: Все @Transactional методы ДОЛЖНЫ использовать уровень изоляции READ_COMMITTED, если явно не задокументировано иное.

**Обоснование**: Наша БД (PostgreSQL) оптимизирована для READ_COMMITTED. REPEATABLE_READ может вызвать проблемы производительности при высокой нагрузке.

**Пример**:
```java
// ТРЕБУЕТСЯ
@Transactional(isolation = Isolation.READ_COMMITTED)
public void processOrder(Order order) {
    // ...
}
```
```

#### Правила Confluence

**Интеграция**: Загружаются через n8n workflow  
**Кэш**: TTL 1 час  
**Формат**: Markdown экспортированный из Confluence  
**Случай использования**: Общие правила для нескольких проектов/команд
```
---


### 5. Настраиваемое выполнение ревью

#### Выбор типа ревью

**API параметр**: `review_types: List[ReviewType]`  
**По умолчанию**: `[ALL]`

**Примеры**:

Быстрая проверка безопасности:
```json
{
  "agent": "QWEN_CODE",
  "review_types": ["ERROR_DETECTION", "SECURITY_AUDIT"],
  "project_id": 123,
  "merge_request_iid": 456
}
```

Фокус на производительность:
```json
{
  "agent": "CLINE",
  "review_types": ["PERFORMANCE", "DATABASE_OPTIMIZATION"],
  "project_id": 123,
  "merge_request_iid": 456
}
```

Полное ревью (По умолчанию):
```json
{
  "agent": "CLINE",
  "review_types": ["ALL"],
  "project_id": 123,
  "merge_request_iid": 456
}
```

#### Стратегия выполнения

**Параллельное выполнение**: Несколько типов ревью выполняются одновременно в пределах ёмкости CLI агента  
**Управление ресурсами**: Автоматическое throttling если нагрузка системы превышает порог  
**Timeout**: 5 минут на тип ревью (настраиваемо)  
**Retry**: 1 retry при сбое с экспоненциальным backoff

---

## Точки интеграции

### Интеграция GitLab (Минимальное использование API)

**Требуемые API вызовы**:
1. `GET /projects/:id/merge_requests/:iid` - Получить метаданные MR
2. `GET /projects/:id` - Получить clone URL
3. `POST /projects/:id/merge_requests/:iid/notes` - Добавить сводный комментарий
4. `POST /projects/:id/repository/commits` - Закоммитить документацию
5. `POST /projects/:id/merge_requests` - Создать fix/refactoring MR

**Избегаемые**:
- Листинг файлов через API (использовать git локально)
- Получение diff через API (использовать git diff локально)
- Сложные merge операции через API

### Интеграция n8n Workflow

**Workflow**: GitLab Webhook → Валидация → Review API → Обработка результатов

**LangChain Code Node** (JavaScript валидация):
```javascript
// Валидация JIRA тикета и описания
const title = $json.body.object_attributes.title;
const description = $json.body.object_attributes.description || '';

const jiraPattern = /([A-Z]+-\d+)/;
const jiraMatch = title.match(jiraPattern);

const validationErrors = [];
if (!jiraMatch) {
    validationErrors.push('Отсутствует JIRA тикет в заголовке (формат: PROJECT-123)');
}
if (description.length < 50) {
    validationErrors.push('Описание слишком короткое (минимум 50 символов)');
}
if (description.includes('TODO') || description.includes('TBD')) {
    validationErrors.push('Описание содержит placeholder текст');
}

return {
    is_valid: validationErrors.length === 0,
    errors: validationErrors,
    jira_ticket: jiraMatch ? jiraMatch[1] : null,
    score: jiraMatch && description.length >= 50 ? 100 : 50
};
```

**Review API вызов**:
```javascript
const response = await $http.request({
    method: 'POST',
    url: 'http://review-api:8000/api/v1/review',
    headers: {
        'Content-Type': 'application/json'
    },
    body: {
        agent: 'CLINE',
        review_types: ['ALL'],
        project_id: $json.body.project.id,
        merge_request_iid: $json.body.object_attributes.iid,
        language: 'java'
    }
});

return response.body;
```

### MCP RAG интеграция (Будущее)

**Назначение**: Запрос внутренней базы знаний для совместимости библиотек, паттернов использования API  
**Протокол**: SSE/HTTP соединение с n8n MCP сервером  
**Backend**: Qdrant vector database  
**Случаи использования**:
- Проверка совместимости библиотек (Library Updater Agent)
- Поиск документации внутренних API
- Сопоставление паттернов исторических проблем

---

## TODO функции (Запланированные)

### JIRA Task Matcher Agent

**Назначение**: Проверять, что изменения MR полностью реализуют требования JIRA задачи

**Входные данные**:
- JIRA task ID (из заголовка MR)
- Описание задачи из JIRA API
- Изменения кода MR

**Анализ**:
- Идентифицировать требования задачи из описания
- Сопоставить требования с изменениями кода
- Обнаружить отсутствующие реализации
- Отличить работу по задаче от рефакторинга

**Выходные данные**:
- Процент завершения (0-100%)
- Список нереализованных требований
- Предложения по недостающей реализации
- Fix MR если требования неполные

**Интеграция**: Требует доступа JIRA API через n8n workflow

### Changelog Generator Agent

**Назначение**: Автоматически генерировать/обновлять записи CHANGELOG.md

**Входные данные**:
- История Git коммитов
- MR diff
- Сообщения коммитов
- Информация JIRA задачи

**Анализ**:
- Категоризировать изменения (Added/Changed/Fixed/Deprecated/Removed/Security)
- Извлекать осмысленные описания из коммитов
- Группировать связанные изменения
- Следовать формату Keep a Changelog

**Вывод**: Обновление CHANGELOG.md закоммиченное в ветку MR

### Library Updater Agent

**Назначение**: Идентифицировать и обновлять устаревшие зависимости

**Входные данные**:
- pom.xml 
- Текущие версии зависимостей
- MCP RAG база знаний (информация о совместимости)

**Анализ**:
- Идентифицировать устаревшие библиотеки
- Проверить совместимость через базу знаний
- Идентифицировать breaking changes
- Генерировать заметки по миграции

**Вывод**: MR с обновлёнными зависимостями и руководством по миграции

**Интеграция**: Требует MCP RAG соединение для проверки совместимости

---

## Технический стек

### Backend
- **Framework**: FastAPI 0.104+
- **Язык**: Python 3.11
- **Async**: asyncio с uvicorn
- **Валидация**: Pydantic 2.5+

### CLI агенты
- **Cline CLI**: Последняя стабильная версия
- **Qwen Code CLI**: Последняя стабильная версия
- **Установка**: npm глобальные пакеты

### Модели (Предразвёрнутые)
- **DeepSeek V3.1 Terminus**: через OpenAI совместимый API
- **Qwen3-Coder-32B**: через OpenAI совместимый API

### Интеграция GitLab
- **python-gitlab**: 4.4.0
- **GitPython**: 3.1.40

### Развёртывание
- **Основное**: Docker Compose
- **Продакшн**: Kubernetes (директория deployment/)
- **Container Registry**: Внутренний registry для air-gap поддержки

---

## Архитектура развёртывания

### Docker Compose (Разработка/тестирование)

```yaml
services:
  review-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_API_URL=${MODEL_API_URL}
      - DEEPSEEK_MODEL_NAME=${DEEPSEEK_MODEL_NAME}
      - QWEN3_MODEL_NAME=${QWEN3_MODEL_NAME}
      - GITLAB_URL=${GITLAB_URL}
      - GITLAB_TOKEN=${GITLAB_TOKEN}
    volumes:
      - ./prompts:/app/prompts
      - ./rules:/app/rules
      - ./logs:/app/logs
```

### Kubernetes (Продакшн)

**Компоненты**:
- Deployment: 3 реплики для высокой доступности
- Service: ClusterIP для внутреннего доступа
- Ingress: Внешний доступ с TLS
- ConfigMap: Промпты и правила
- Secret: GitLab токен, model API ключ
- PersistentVolume: Хранение логов

### Air-Gap передача

**Подготовка** (Подключённая среда):
1. Экспорт Docker образов: `docker save -o review-api.tar review-api:latest`
2. Скачивание npm пакетов: `npm pack @cline/cli @qwen-code/qwen-code`
3. Создание Python offline репозитория: `pip download -r requirements.txt -d packages/`
4. Архивация промптов и правил: `tar -czf rules-prompts.tar.gz prompts/ rules/`

**Установка** (Изолированная среда):
1. Загрузка Docker образов: `docker load -i review-api.tar`
2. Установка npm пакетов: `npm install -g cline-cli.tgz qwen-code.tgz`
3. Установка Python пакетов: `pip install --no-index --find-links=packages/ -r requirements.txt`
4. Извлечение правил/промптов: `tar -xzf rules-prompts.tar.gz`
5. Конфигурация переменных окружения
6. Развёртывание с docker-compose или kubectl

---

## Метрики успеха

### Метрики охвата
- **Выполненные типы ревью**: Отслеживание наиболее используемых типов ревью
- **Найденные проблемы по типу**: Измерение эффективности каждого типа ревью
- **Доля ложных срабатываний**: Отслеживание проблем, отмеченных как неправильные разработчиками (цель <10%)

### Метрики производительности
- **Время ревью**: Среднее время на ревью (цель <5 минут)
- **Время ответа API**: p95 < 30 секунд
- **Эффективность параллельных задач**: Утилизация слотов параллельных задач

### Метрики качества
- **Предотвращённые критические проблемы**: Количество проблем безопасности/багов, выявленных до продакшена
- **Доля принятия разработчиками**: Процент слитых fix MR (цель >70%)
- **Принятие рефакторинга**: Процент слитых refactoring MR (цель >50%)

### Удовлетворённость разработчиков
- **Сэкономленное время ручного ревью**: Часы, сэкономленные в неделю
- **Оценка качества ревью**: Оценка разработчиками полезности ревью (шкала 1-5, цель >4.0)
- **Доля ложных отрицаний**: Проблемы, пропущенные ревью, но найденные позже (цель <5%)

---

## Будущие улучшения

### Фаза 2 (Q2 2026)
- Реализация JIRA Task Matcher Agent
- Реализация Changelog Generator Agent
- Library Updater Agent с MCP RAG

### Фаза 3 (Q3 2026)
- Поддержка Python, JavaScript/TypeScript кодовых баз
- Фреймворк разработки пользовательских проверок
- Интеграция с SonarQube для дополнительных метрик

### Фаза 4 (Q4 2026)
- AI-powered генерация кода для распространённых паттернов
- Интерактивный режим ревью (разработчик может задавать вопросы)
- Обучение на исторических проблемах (избегать повторения прошлых ошибок)

---

## Приложения

### A. Глоссарий

- **CLI Агент**: Command-line AI инструмент (Cline или Qwen Code), выполняющий анализ кода
- **Тип ревью**: Конкретная категория анализа кода (ERROR_DETECTION, SECURITY_AUDIT, UNIT_TEST_COVERAGE, MEMORY_BANK и т.д.)
- **Fix MR**: Merge request, автоматически созданный с исправлениями проблем, ответвлённый от MR source branch
- **Refactoring MR**: Merge request с предложениями по рефакторингу (если значительные), ответвлённый от MR source branch
- **SIGNIFICANT рефакторинг**: Крупномасштабный рефакторинг, требующий отдельного MR (>3 классов, breaking changes, >200 LOC)
- **MINOR рефакторинг**: Мелкомасштабный рефакторинг, включённый в fix MR (переименования, извлечение констант)
- **UNIT_TEST_COVERAGE**: Тип ревью, который автоматически генерирует недостающие юнит-тесты
- **MEMORY_BANK**: Тип ревью, который поддерживает базу знаний проекта (Memory Bank)
- **Memory Bank**: Структурированная коллекция markdown файлов, документирующих контекст проекта, паттерны и решения
- **System Prompt**: Глобальный промпт, препендируемый ко всем ревью со стандартами стиля кода и интеграцией Memory Bank
- **MR Source Branch**: Feature ветка, которая проверяется (источник MR)
- **MR Target Branch**: Ветка, в которую будет слит MR (например, main, develop)

### B. Ссылки

- [Документация Spring Boot](https://spring.io/projects/spring-boot)
- [Спецификация языка Java](https://docs.oracle.com/javase/specs/)
- [Принципы SOLID](https://en.wikipedia.org/wiki/SOLID)
- [Документация Cline CLI](https://docs.cline.bot)
- [Документация Qwen Code](https://qwenlm.github.io)

### C. Лог решений

| Дата | Решение | Обоснование |
|------|---------|-------------|
| 2025-11 | Использовать CLI агенты вместо прямых вызовов моделей | Лучшее понимание кода, управление контекстом |
| 2025-11 | Выполнение одного агента (не комбинированное) | Избежать конфликтующих рекомендаций |
| 2025-11 | Минимальное использование GitLab API | Снизить rate limits, лучшая производительность |
| 2025-11 | 13 типов ревью (расширено с 11) | Добавлены UNIT_TEST_COVERAGE и MEMORY_BANK для полного охвата |
| 2025-11 | Отдельные refactoring MR для значительных изменений | Дать разработчикам выбор |
| 2025-11 | Fix/refactor ветки от MR source (не target) | Позволяет разработчикам сначала интегрировать изменения в feature ветку |
| 2025-11 | System prompt с интеграцией Memory Bank | Консистентный стиль кода + контекстно-зависимые рекомендации |
| 2025-11 | CLI пишет файлы, FastAPI обрабатывает Git операции | Чёткое разделение ответственности для обновлений Memory Bank |
| 2025-11 | Автогенерация юнит-тестов с UNIT_TEST_COVERAGE | Обеспечение покрытия кода без ручного написания тестов |
| 2025-11 | Автообновление Memory Bank с каждым MR | Живая документация, эволюционирующая с проектом |

---

**Статус документа**: Живой документ, обновляется по мере реализации функций и эволюции требований.

**Обратная связь**: Отправляйте обратную связь и предложения через GitLab issues в репозитории review service.

