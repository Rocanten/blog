Title: Настройка логирования в docker при помощи Loki на s3 и Grafana
Date: 2023-09-22 23:16
Category: devops
Slug: nastrojka-logirovaniya-v-docker-pri-pomoshchi-loki-na-s3-i-grafana
Summary: Настройка логов на окружении, где размещены ваши сервисы позволяет сэкономить многие часы отладки и поиска неисправностей в продакшене. На самом деле, поднять полноценную систему логирования на сервере с Docker - не самая сложная задача. Давайте посмотрим как это сделать.


# Настройка логирования в docker при помощи Loki на s3 и Grafana

## Обзор

Для начала, давайте посмотрим верхнеуровнево на то, что мы хотим сделать

![docker_logging_diagram.png]({static}/images/docker_logging_diagram.png)

Кратко о том, что происходит на схеме:

1. Docker logging driver считывает логи со всех контейнеров, которые логируют что-либо в нашем докере
2. Docker logging driver считывает логи из файлов логов хоста
3. Docker logging driver отправляет считанные логи в Loki через его API
4. За кадром loki индексирует логи и организует их хранение
5. Пользователь открывает Grafana(она поднята в том же докере, где и все остальное)
6. Grafana делает запросы к Loki на получение логов и визуализирует их

Перейдем к настройке всего этого добра.

## Установка и настройка драйвера логирования

Чтобы в Loki появлялись логи, надо чтобы кто-то их туда отправлял. У Docker есть для этого специальный механизм - драйверы логирования. Они есть для многих сервисов, например для Splunk, Amazon Cloud Watch, ELK и многих других. Нас интересует плагин [Loki docker plugin](https://grafana.com/docs/loki/latest/send-data/docker-driver/). 

Устанавливаем драйвер логирования:

```yaml
sudo docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions
```

Теперь у нас есть возможность отправлять логи в Loki. Это можно сделать двумя способами:

1. Указывать специальные параметры при запуске каждого контейнера
2. Принудительно отправлять все логи со всех запускаемых на данном хосте контейнеров в Loki

Я думаю, что в большинстве случаев второй вариант предпочтителен, так как требует настройки один раз и помогает собрать логи со всех, даже тех, кто этого не хочет.
<br />
Для принудительной отправки логов в Loki, необходимо отредактировать файл /etc/docker/daemon.json. Создайте его, если его нет:

```yaml
{
    "log-driver": "loki",
    "log-opts": {
        "loki-url": "http://127.0.0.1:3100/loki/api/v1/push"
    }
}
```

Здесь все довольно просто:

log-driver указывает на то, что логирование будет осуществляться при помощи Loki

loki-url указывает адрес, по которому драйвер должен отправить логи.
<br />
После изменений необходимо перезапустить сервис докера:

```yaml
sudo systemctl restart docker
```

С этого момента все контейнеры, которые были заново созданы, будут отправлять логи прямиком в Loki. Вот только его пока не существует.

Давайте исправим это

## Настройка бакета s3 в Яндекс.Облако

Но сначала нужно получить параметры для доступа к бакету s3, в котором мы будем хранить наши логи. Я привожу инструкцию для Яндекс Облака, но примерно также можно сделать в любом другом сервисе, предоставляющим объектное хранилище.
<br />

Сначала создадим сервисный аккаунт:

1. Заходим в консоль Яндекс Облако: [https://cloud.yandex.ru/](https://cloud.yandex.ru/)
2. Переходим во вкладку Сервисные аккаунты
3. Нажимаем кнопку Создать сервисный аккаунт
4. Задаем имя
5. Выбираем права: storage.editor, storage.uploader, storage.viewer
6. Создаем
7. Переходим в созданный сервисный аккаунт
8. Нажимаем кнопку Создать ключ
9. Выбираем Создать статический ключ доступа
10. Сохраняем себе идентификатор ключа и секретный ключ

<br />

Теперь создаем бакет:

1. В меню Все сервисы выбираем Object storage
2. Нажимаем кнопку Создать бакет
3. Задаем имя
4. Создаем бакет

Вот и все, url вашего бакета будет вида [http://storage.yandexcloud.net/](http://storage.yandexcloud.net/) + название созданного бакета

## Настройка Loki для хранения логов в s3 хранилище
<br /> 
Создайте папку loki в домашней директории:

```yaml
mkdir ~/loki
```
<br /> 
Перейдите в созданную папку:

```yaml
cd ~/loki
```
<br /> 
Создайте и отредактируйте в домашней папке файл local-config.yaml:

```yaml
auth_enabled: false 

server:
  http_listen_port: 3100

common:
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: memberlist
  replication_factor: 1
  path_prefix: /etc/loki

ingester:
  wal:
    dir: "/tmp/wal"
    replay_memory_ceiling: 4GB

schema_config:
  configs:
  - from: 2023-09-12
    store: boltdb-shipper
    object_store: s3
    schema: v11
    index:
      prefix: index_
      period: 24h

storage_config:
 boltdb_shipper:
   active_index_directory: /loki/index
   cache_location: /loki/index_cache
   shared_store: s3
 aws:
   s3: s3://{Access key}:{Access key secret}@{s3 bucket url}
   s3forcepathstyle: true

compactor:
  working_directory: /loki/compactor
  shared_store: s3
  compaction_interval: 5m
```
<br />
Разберем все параметры

<br />
Мы не планируем использовать multi tenancy, так что смело отключаем:

```yaml
auth_enabled: false
```
<br />
Loki будет ожидать логи и запросы от графаны на 3100 порту:

```yaml
http_listen_port: 3100
```
<br />
IP адрес инстанса Loki:

```yaml
instance_addr: 127.0.0.1
```
<br />
Следующая настройка позволяет повысить доставляемость логов в постоянное хранилище за счет создания двух и более реплик Loki. Нам это сейчас не нужно, но в некоторых проектах может быть полезно.

```yaml
store: memberlist
```
<br />
Следующий фрагмент определяет настройки ingester. Это компонент внутри Loki, который отвечает за запись логов в постоянное хранилище(например, s3) и считывает их оттуда.

dir указывает директорию, в которой будут храниться логи, пока они не отправлены в постоянное хранилище

replay_memory_ceiling указывает размер логов, хранящийся локально. Если объем логов достигнет данного значения, ingester их немедленно отправит в постоянное хранилище.

```yaml
ingester:
  wal:
    dir: "/tmp/wal"
    replay_memory_ceiling: 4GB
```
<br />
Следующий блок определяет настройки хранения индекса. 

from - начиная с какой даты будут созданы индексы

store - тип хранилища индексов. У нас будет boltdb-shipper, который позволяет использовать локальные индексы, которые периодически синхронизируются с хранилищем

object_store - тип хранилища логов. Мы настраиваем s3

```yaml
schema_config:
  configs:
  - from: 2023-09-12
    store: boltdb-shipper
    object_store: s3
    schema: v11
```
<br />
Далее идут настройки boltdb_shipper.

active_index_directory - локальная директория для хранения индексов

cache_location - локальная директория для хранения кэша индексов

shared_store - постоянное хранилище индексов

```yaml
 boltdb_shipper:
   active_index_directory: /loki/index
   cache_location: /loki/index_cache
   shared_store: s3
```
<br />
Наконец-то, сами настройки s3. Тут все просто.

s3 - строка для доступа к бакету, где будут храниться логи

s3forcepathstyle - доступ к бакету по пути

```yaml
   s3: s3://{Access key}:{Access key secret}@{s3 bucket url}
   s3forcepathstyle: true
```
<br />
Compactor оптимизирует шарды индексов для лучшей производительности

working_directory - сюда compactor будет скачивать файлы для последующей оптимизации

shared_store - постоянное хранилище индексов

compaction_interval - как часто проводить оптимизацию

```yaml
compactor:
  working_directory: /loki/compactor
  shared_store: s3
  compaction_interval: 5m
```

## Пишем docker-compose для Loki и Grafana

Мы на финишной прямой! Осталось создать docker-compose.yml файл и запустить нашу связку Loki + Grafana.
<br />
Итак, создадим на docker-compose.yml в той же папке ~/loki:

```yaml
version: "3"

networks:
  loki:

services:
  loki:
    image: grafana/loki:2.9.0
    hostname: loki
    ports:
      - "3100:3100"
    volumes:
      - ~/loki:/etc/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - loki

  grafana:
    environment:
      - GF_PATHS_PROVISIONING=/etc/grafana/provisioning
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    entrypoint:
      - sh
      - -euc
      - |
        mkdir -p /etc/grafana/provisioning/datasources
        cat <<EOF > /etc/grafana/provisioning/datasources/ds.yaml
        apiVersion: 1
        datasources:
        - name: Loki
          type: loki
          access: proxy
          orgId: 1
          url: http://loki:3100
          basicAuth: false
          isDefault: true
          version: 1
          editable: false
        EOF
        /run.sh
    image: grafana/grafana:latest
    ports:
      - "3200:3000"
    networks:
      - loki
```
<br />
Разумеется, рассмотрим все повнимательнее.
<br />
Для начала задаем сеть с названием loki, чтобы у нас не было проблем с доступностью сервисов друг для друга:

```yaml
networks:
  loki:
```
<br />
Далее идет блок с Loki.

image - берем стандартный docker образ grafana/loki

hostname - задаем на всякий случай hostname

ports - паблишим и маппим стандартный порт Loki

volumes - маппим нашу папку с настройками в директорию /etc/loki контейнера с Loki

command - указываем путь к файлу настройки

networks - включаем сервис loki в сеть loki

```yaml
services:
  loki:
    image: grafana/loki:2.9.0
    hostname: loki
    ports:
      - "3100:3100"
    volumes:
      - ~/loki:/etc/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - loki
```
<br />
Теперь к настройкам Grafana.

Задаем переменные окружения:

```yaml
  grafana:
    environment:
      - GF_PATHS_PROVISIONING=/etc/grafana/provisioning
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
```
<br />
Теперь при помощи entrypoint указываем сервису, что нужно создать datasource, который будет обращаться к нашему loki. Это можно будет сделать руками после запуска контейнера в интерфейсе Grafana, но лучше автоматизировать

```yaml
  entrypoint:
      - sh
      - -euc
      - |
        mkdir -p /etc/grafana/provisioning/datasources
        cat <<EOF > /etc/grafana/provisioning/datasources/ds.yaml
        apiVersion: 1
        datasources:
        - name: Loki
          type: loki
          access: proxy
          orgId: 1
          url: http://loki:3100
          basicAuth: false
          isDefault: true
          version: 1
          editable: false
        EOF
        /run.sh
    image: grafana/grafana:latest
    ports:
      - "3200:3000"
    networks:
      - loki
```
<br />
Вот и все!
<br />
Запускаем docker compose:

```yaml
sudo docker compose up -d --build
```

Ждем, когда все запустится и переходим в браузере по адресу {ip сервера}:3200.

Должна открыться Grafana. Переходим в раздел Explore, выбираем нужный контейнер и делаем запросы логов.

## Что в итоге

В итоге мы получили удобную систему логов для всех контейнеров, которые когда-либо будут созданы на данном хосте. Более того, мы можем перенаправлять в Loki логи с других хостов, просто указав внешний ip в настройках драйвера логирования докера.

Особенно приятно, что все логи теперь храняться в облаке на s3, а значит никуда не пропадут, могут храниться там вечно за копейки и больше у вас никогда не забьется диск из-за большого лог файла!

Ну и конечно же больше не надо лазить по бесконечным лог файлам грепами или выполнять docker logs.
<br /><br /><br /><br /><br />