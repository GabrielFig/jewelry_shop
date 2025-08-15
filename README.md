
# 🏷️ Jewelry Shop Allocation API

[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?style=default&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pytest](https://img.shields.io/badge/Pytest-0A9EDC.svg?style=default&logo=Pytest&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00.svg?style=default&logo=SQLAlchemy&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED.svg?style=default&logo=Docker&logoColor=white)](https://www.docker.com/)

Sistema de asignación de inventario para joyería, implementando:
- **Domain-Driven Design** (DDD)
- **Clean Architecture**
- **Unit of Work** y **Repository** patterns
- Event-driven con **Message Bus**

## 🚀 Comenzar

### Prerrequisitos
- Docker 20.10+
- Docker Compose 2.5+

### Ejecución con Docker
```bash
docker-compose up -d --build
```

La API estará disponible en: http://localhost:8000/docs

## 🏗️ Estructura del Proyecto
```text
jewelry_shop/
├── app/                  # Core de la aplicación
│   ├── domain/           # Modelos y servicios de dominio
│   ├── service_layer/    # Casos de uso
│   ├── adapters/         # Implementaciones concretas (DB, APIs)
│   └── entrypoints/      # Web API (FastAPI)
│
├── infrastructure/       # Configuración e inicialización
├── tests/                # Tests unitarios y de integración
└── scripts/              # Utilidades (ej: init_db)
```

## 📝 API Endpoints
| Método | Ruta          | Descripción                     |
|--------|---------------|---------------------------------|
| POST   | /batches      | Registrar nuevo lote de stock   |
| POST   | /allocate     | Asignar pedido a lote           |
| GET    | /notifications| Ver eventos publicados          |

Ejemplo de request:
```json
POST /allocate
{
  "order_id": "order-123",
  "sku": "GOLD_RING",
  "qty": 2
}
```

## 🧪 Testing
Ejecutar todos los tests:
```bash
pytest -v
```

Tipos de tests:
- **Unitarios**: Dominio puro (sin DB)
- **Integración**: Servicios + Fake UoW
- **E2E**: TestClient contra API real

## 🛠️ Configuración
Variables de entorno:
```env
DB_URL=postgresql://user:pass@host:5432/db
LOG_LEVEL=INFO
```

## 🔍 Diagrama de Arquitectura
```mermaid
graph TD
    A[API FastAPI] -->|Usa| B[Service Layer]
    B -->|Depende de| C[Domain Model]
    B -->|Usa| D[Unit of Work]
    D -->|Gestiona| E[Repositories]
    E -->|Persiste| F[(PostgreSQL)]
    C -->|Publica| G[Eventos]
    G -->|Notifica| H[Handlers]
```

## 🧠 Principios Clave
1. **Domain First**: La lógica de negocio no depende de frameworks
2. **Explicit Dependencies**: Inyección mediante interfaces
3. **Transaction Boundary**: UoW maneja la atomicidad
4. **Event-Driven**: Side effects mediante eventos

## 🚨 Troubleshooting
Problema común: 
```text
psycopg2.OperationalError: connection failed
```
Solución:
```bash
docker-compose restart db
```

## 📚 Recursos
- [Libro: Architecture Patterns with Python](https://www.cosmicpython.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/best-practices/)
- [DDD para Pythonistas](https://github.com/cosmicpython/book)
