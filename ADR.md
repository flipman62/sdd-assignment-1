## [1]. Use Flask with SQLite
Date: 2026-10-09
Status: Decided
Context: The application needs a simple backend that can run in one container and store data locally.
Decision: Use Flask because it is lightweight and easy to use. Use SQLite because it is required for the project and does not need a separate database service.
Alternatives considered: Django was rejected because it would add more complexity than this small application needs.
Consequences: The application will be simple to run and maintain, with the backend and database in one container.
