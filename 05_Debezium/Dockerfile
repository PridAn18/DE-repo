FROM confluentinc/cp-kafka-connect:7.0.1

# Укажи нужную версию Debezium
ENV DEBEZIUM_VERSION=1.9.7.Final

# Установка Postgres-коннектора Debezium
RUN curl -L https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgresql/${DEBEZIUM_VERSION}/debezium-connector-postgresql-${DEBEZIUM_VERSION}-plugin.tar.gz \
    | tar -xz -C /usr/share/java

RUN mkdir -p /etc/kafka-connect/plugins
