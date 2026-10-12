## [1]. Use Flask with SQLite
Date: 2026-10-09
Status: Decided
Context: The application needs a simple backend that can run in one container and store data locally.
Decision: Use Flask because it is lightweight and easy to use. Use SQLite because it is required for the project and does not need a separate database service.
Alternatives considered: Django was rejected because it would add more complexity than this small application needs.
Consequences: The application will be simple to run and maintain, with the backend and database in one container.

## [2]. Separate habits from completion tracking
Date: 2026-10-12
Status: Decided
Context: The application needs two meaningful feature domains instead of only basic habit CRUD.
Decision: Keep habit management responsible for creating, listing, and deleting habits. Keep completion tracking responsible for daily completion history and streak calculations, using the habit ID to connect the two domains.
Alternatives considered: Keeping all behavior in one module was rejected because the domains would be harder to separate in a future service-based design.
Consequences: Each domain has a clear responsibility and can be tested independently while still running in the same application for Assignment 1.
