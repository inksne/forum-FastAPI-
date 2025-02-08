## Форум

Приложение для нахождения собеседников и для общения между ними.

## Руководство по эксплуатации

- Создаём .env и добавляем в него все переменные, которые перечисленны в ```config.py```
- Из корня проекта стартуем команду ```docker compose up```
- Довольствуемся результатом

## Документация

`auth`

Каталог с файлами для создания access и refresh токена для аутентификации.
Также содержит функции для этой самой аутентификации.

`certs`

Каталог с приватным и публичным ключами, так как алгоритм RS256.

`database`

Каталог с подключением к бд и моделями бд.

`static`

Внутри файл с иконкой.

`templates`

Каталог с html-страницами и файлом ```router.py```
В файле идет подключение всех этих html-страниц и взаимодействие с базой данных.
Именно в нем реализуется взаимодействие с вебсокетами.

`test_main.py & pytest.ini`

Внутри файл с простыми API тестами.

В pytest.ini конфигурация для pytest

`config.py`

Получение переменных окружения из ```.env```
Также имеется класс с настройками для JWT и бд.

`crud.py`

Файл с функцией получения пользователя по имени.

`main.py`

Основной файл с созданием приложения, корсами, подключением роутеров и функциями для регистрации и поиска

## CI/CD

В пайплайне я добавил всего лишь две джобы: *build* и *test*.
deploy закоммичена, ибо некуда деплоить (да и на гитхаб раннере docker-compose нету).

## Ссылочка

Ссылочка [есть](https://messenger-eiv7.onrender.com).
Проблема в том, что у меня может слететь платный тариф, и сайт не будет доступен.

Можете распространять код, делать с ним что угодно, если будут вопросы, то вот почта:
```inksne@gmail.com```