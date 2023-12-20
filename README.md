# PychApp
### - мессенджер, работающий с использованием криптографических примитивов AES и RSA для безопасного общения.

### Данное решение состоит из 2 компонент:
1. Сервер (`pych`). Он основывается на технологиях `Falcon`, `WSocket`, `Mongo` . ` Pych` является посредником между своими клиентами - он помогает им обменяться секретными данными (ключами) для общения и установить сессию для передачи самих сообщений.

Тестовый сервис развернут следующим образом:
```python
# микросервис, выполняющий все действия, связанные с криптографией, пользователями и чатами (falcon)
base="http://89.104.70.246:8081/status"

# микросервис для подписки на чат (wsocket)
ws="http://89.104.70.246:8080/ws"
```

Собственный инстанс можно поднять при помощи `docker-compose`
```bash
# в папке srv
docker compose up
```


Для серверов с низкой пропускной способностью желательно использовать образ на docker-hub
- https://hub.docker.com/repository/docker/xpoleones/pychapp


Без контейнеризации инстанс можно запустить при помощи `go-task`
```
go-task/task run
```


Перед этим можно выбрать (или настроить дефолтный) конфигурационный файл, который будет использоваться `pych` для запуска.

2. Клиент. Консольная утилита, что взаимодействует с `pych` для регистрации пользователя, загрузки публичных клкючей, создания чатов и инициализации процесса переписки.

С руководством пользователя можно ознакомиться: [здесь](cli/README.md)

### Документация
Подробнее о сервисе `pych` можно почитать здесь: http://89.104.70.246:8070/