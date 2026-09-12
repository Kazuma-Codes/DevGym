# ---- Stage 1: build the React frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend-react/package.json frontend-react/package-lock.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build

# ---- Stage 2: build the Spring Boot jar with the frontend embedded ----
FROM maven:3.9-eclipse-temurin-21 AS server-build
WORKDIR /app/server
COPY server/pom.xml .
RUN mvn -q -B dependency:go-offline
COPY server/src ./src
COPY --from=frontend-build /app/frontend/dist ./src/main/resources/static
RUN mvn -q -B package -DskipTests

# ---- Stage 3: minimal runtime ----
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN mkdir -p /data
COPY --from=server-build /app/server/target/interview-server-1.0.0.jar app.jar
EXPOSE 8080
ENV SQLITE_PATH=/data/interview.db
ENTRYPOINT ["java", "-jar", "app.jar"]
