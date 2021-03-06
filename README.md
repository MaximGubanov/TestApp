## Описание
Приложение считывает данные из таблицы GoogleSheet, через Google API и сохранет в локальную БД на ПК. А так же приложение работает в режиме онлайн и следит за изменением таблицы. В случае изменений, делает сверку и обновляет БД. Так же приложение проверяет дату поставок из таблицы и отправляет черз bot-telegram сообщение в чат-группу. В качестве СУБД использовался Postgres и ORM SQLAlchemy.

## Инструкция
- ### До того как тестировать 
    - *Вступите в группу по сылке https://t.me/+NCtPfQYAJeM0MDYy , чтобы получать сообщения от бота*

    - Сама страница документа [GoogleSheet][1]


1. __Вариант через Docker__<br>

    *клонируйте репозиторий к себе локально*
   ```
    git clone https://github.com/MaximGubanov/TestApp.git
   ```
   *перейдите в корневую директорию приложения*
   ```
   cd TestApp
   ```
   *запустите файл ___docker-compose.yml___*
   ```
   docker-compose up
   ```
   docker подтянет postgres, adminer и сам образ приложения. Можете зайти в браузер и проверить БД через Adminer, используя след. данные:<br>
   ```
    http://localhost:8080/ - введите этот адрес в строке браузера

    Движок - PostreSQL
    Север - db
    Имя пользователя - test
    Пароль - test
    База данных - test
   ```
2. __Скачать из репозитория GitHub__<br>
    ***ВАЖНО:***<br>
     *Для запуска приложения нужно выполнить файл __main.py__*, но перед этим:
     + нужно организовать бд на основе PostgreSQL, создать БД, получить все данные для подключения к БД, все настройки прописываются в __\__init\__.py__.
     + Так же зарегистрироваться на Google Platform, создать таблицу, подключить GoogleSheetAPI, получить API Keys или Service Accounts, если использовать Service Accounts - скачать *__файл-JSON__* для получения доступа к таблице. ID таблицы и API-ключ прописываются в  __\__init\__.py__.


[1]: https://docs.google.com/spreadsheets/d/1JYUGbSWgyl2Jq5J_YKeH2TtjPQcLzVXm2_PSRJoWAwI/edit#gid=0