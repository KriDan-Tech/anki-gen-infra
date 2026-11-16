# api-gateway

## Владение и интерфейс
Входной HTTP routing, JWT authentication, sanitization/forwarding к сервисам. Контракт роутов и настройки перечислены в `api-gateway/README.md`; не дублировать здесь endpoint inventory.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `api-gateway/src/main/java/com/ankigen/gateway/routing/GatewayRoutes.java`, `config/SecurityConfig.java`, README и pom (2026-11-16). Локальный HEAD `main` @72b83fb. `api-gateway/pom.xml` pin-ит Spring Boot 4.0.0; README фиксирует Java 21 и Spring Cloud 2025.1.4. Shared internal routes/security должны подтверждаться кодом, не историческим architecture text.

## Утверждённая цель
Gateway проводит UI upload→page selection→quote→pay→completion journey к backend-owned API, сохраняя identity boundary. Он не владеет тарифной логикой, PDF lifecycle или deck state; эти гарантии принадлежат соответствующим сервисам.

## Разрывы и неизвестное
Статическая маршрутизация/JWT sanitization не подтверждает production exposure, действующие hostnames или deployed rules. Проверять доверенные headers/internal endpoints с конфигом инфраструктуры; не обещать защиту, не подтверждённую соответствующим source.

## Практическая навигация (осмотр 2026-11-16)
[GatewayRoutes](https://github.com/KriDan-Tech/anki-gen-api-gateway/blob/main/src/main/java/com/ankigen/gateway/routing/GatewayRoutes.java) собирает RouterFunction из `GatewayProperties`; [SecurityConfig](https://github.com/KriDan-Tech/anki-gen-api-gateway/blob/main/src/main/java/com/ankigen/gateway/config/SecurityConfig.java) задаёт security/JWT boundary. При route/auth change совместно сверять [README](https://github.com/KriDan-Tech/anki-gen-api-gateway/blob/main/README.md), [pom.xml](https://github.com/KriDan-Tech/anki-gen-api-gateway/blob/main/pom.xml), [API verification](https://github.com/KriDan-Tech/anki-gen-api-gateway/blob/main/docs/api-verification.md) и [infra Compose](https://github.com/KriDan-Tech/anki-gen-infra/blob/main/docker-compose.yml); checked-in конфиг не доказывает deployed routing.
