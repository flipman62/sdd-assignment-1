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

## [3]. Store habits and completions in related SQLite tables
Date: 2026-10-12
Status: Decided
Context: Both feature domains need persistent data, while a completion belongs to one habit.
Decision: Store habits in a `habits` table and daily records in a `completions` table linked by `habit_id`. Enforce one completion per habit and date with a unique constraint, and delete completions when their habit is deleted.
Alternatives considered: Storing completions as a list inside each habit was rejected because separate rows are easier to query and test.
Consequences: SQLite enforces the relationship and prevents duplicate daily records. The schema can later be separated along the same domain boundary.

## [4]. Test core behavior with pytest
Date: 2026-10-12
Status: Decided
Context: The assignment requires automated tests and at least 70% coverage of the two domains' core logic.
Decision: Use pytest with pytest-cov and test habit CRUD, completion rules, streaks, persistence, and cascade deletion using temporary SQLite databases. Keep framework-only details thinner than business behavior.
Alternatives considered: Manual testing was rejected because it would not provide repeatable evidence or a coverage measurement.
Consequences: The current suite provides repeatable checks and reached 98% coverage for `app.py`, while keeping the tests understandable for the comprehension check.
