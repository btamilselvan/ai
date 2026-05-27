---
name: spring-boot-project-standards
description: Enforces corporate standards for Spring Boot 4.0+ projects, including package structure, JWT security, and global error handling.
license: Apache-2.0
metadata:
  version: 1.0.0
  authors:
    - name: Trocks
      email: trocks@example.com
---

# Spring Boot Project Standards

Whenever you are tasked with creating, initializing, or modifying a Spring Boot project, you MUST adhere to the standards defined in this skill.

## 1. Project Metadata & Structure
- **Group ID**: `com.trocks`
- **Package Root**: `com.trocks.{{projectName}}`
- **Java Version**: 21 (LTS)
- **Dependency Management**: Use Maven (`pom.xml`) unless Gradle is explicitly requested.
- **Spring Boot Version**: 4.0.x (latest stable release at the time of project creation).
- **application.yml**: Must be used for all configuration; do not use `application.properties`.


### Mandatory Package Hierarchy:
- `.controller`: RestControllers only; no business logic.
- `.service`: Interface-driven business logic.
- `.jpa`: Package for JPA entities and repositories (if using JPA).
- `.jpa/repository`: Spring Data JPArepositories.
- `.jpa/entity`: JPA entities.
- `.security`: JWT Filters, Providers, and SecurityConfig.
- `.dto`: Request/Response POJOs (use Java Records).
- `.exception`: GlobalExceptionHandler and custom error models.

## 2. Security Architecture (JWT)
You must implement a stateless JWT authentication flow. You must create a `JwtAuthenticationFilter` that validates incoming JWT tokens on protected endpoints. The filter should extract the token from the `Authorization` header, validate its signature, and set the authentication context if valid.

### Required Components:

1. **JwtAuthenticationFilter**: Must extend `OncePerRequestFilter`. It must extract the 'Bearer' token and validate the signature.
2. **JwtAuthenticationProvider**: Must implement `AuthenticationProvider`.
3. **SecurityConfig**: 
   - Must use `SecurityFilterChain` bean.
   - Must disable CSRF for API routes.
   - Must set `SessionCreationPolicy.STATELESS`.
   - Must register the `JwtAuthenticationFilter` before `UsernamePasswordAuthenticationFilter`.
   - Must register CORS configuration to allow requests from `http://localhost:3000` (React frontend).

## 3. Global Exception Handling
Every project MUST have a unified error response format to prevent leaking stack traces and to ensure frontend compatibility.
**Standard Error Object:**
```json
{
  "timestamp": "ISO-8601 UTC",
  "status": 4xx/5xx,
  "error": "Short Error Name",
  "message": "Human readable explanation",
  "path": "/requested/endpoint"
}
```

## 4. REST Controller Standards
You must create a HealthController with a GET endpoint at `/health` that returns the current server time and a status of "UP". This serves as a template for all future controllers.

### REST Controller Guidelines:
- All controllers must be annotated with `@RestController`.
- All endpoints must return a consistent response format using a **ResponseDto**:
```json
{
  "status": "success/failure",
  "data": { ... },
  "message": "Optional human-readable message"
}
```
## 5. JPA & Database
You must create a JPA entity named `ExampleEntity` in the `.jpa.entity` package with at least three fields: `id`, `name`, and `createdAt`. The `id` field must be of type `Long` and annotated with `@Id` and `@GeneratedValue(strategy = GenerationType.IDENTITY)`. The `name` field should be a `String`, and the `createdAt` field should be of type `LocalDateTime`.

### Database Guidelines:
- Use Spring Data JPA for database interactions.
- Use H2 in-memory database for development and testing. For production, use PostgreSQL.
- Add database connection properties in `application.yml` with profiles for `dev` and `prod`.

## 6. Integration
You must create endpoints in the `HealthController` that demonstrate integration with the `ExampleEntity`. This includes CRUD operations for `ExampleEntity` to demonstrate full integration. The integration should follow the standard layered architecture, where the controller calls the service layer, and the service layer interacts with the repository layer.

## 7. OpenAPI Documentation
You must integrate OpenAPI (Swagger) documentation into the project. Use Springdoc OpenAPI for automatic generation of API documentation. Ensure that all endpoints, request/response models, and error responses are properly documented with annotations.

## 8. Logging
- Use SLF4J with log4j2 for logging.
- Exclude logback dependencies to prevent conflicts.

## 9. Testing
- Use JUnit 5 for unit testing.
- Use Mockito for mocking dependencies in service layer tests.
- Use Spring Boot Test for integration testing of controllers and repositories.
- Ensure that all tests are located in the `src/test/java` directory and follow the same package structure as the main codebase.

## 10. Project Validation
You must make sure there are no compilation errors, and all tests must pass successfully before considering the project complete. Additionally, ensure that the application starts without errors and that the `/health` endpoint returns the expected response.