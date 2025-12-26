FROM eclipse-temurin:8-jre-alpine

WORKDIR /app

ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata curl \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY target/service_foundation-*.jar app.jar

RUN addgroup -S spring && adduser -S service_foundation -G spring \
    && mkdir -p /var/log/service_foundation \
    && chown -R service_foundation:spring /var/log/service_foundation
USER service_foundation:spring

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1

ENV LOG_DIR="/var/log/service_foundation"

ENTRYPOINT ["sh", "-c", "mkdir -p ${LOG_DIR} && java $JAVA_OPTS -jar /app/app.jar"]
