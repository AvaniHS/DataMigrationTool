### SYSTEM ARCHITECTURE & CODE GENERATION DIRECTIVES

You are compiling a configuration-driven, multi-tenant ELT migration engine in Python. You must strictly adhere to an interface-driven, modular design pattern. Global scripts or tightly coupled database routines are strictly prohibited.

#### 1. Compilation Execution Pipeline
The engine must process every blueprint step through a sequential, non-overlapping phase contract:
1. **Extraction/Staging Phase:** Evaluate `sources` and map table/file definitions to local staging database identifiers.
2. **Pre-Filtering Phase:** Apply `pre_filters` immediately onto the staged tables before relational assembly.
3. **Relational Assembly Phase:** Construct the structural DAG of `joins` using explicit aliasing.
4. **Derivation/Calculation Layer:** Project expressions, conditions, and constants into named Common Table Expressions (CTEs).
5. **Post-Filtering Phase:** Apply execution parameters from `post_filters` onto the finalized CTE matrix.
6. **Target Mapping & Projection Phase:** Map clean data targets, applying safe data type conversions (`TRY_CAST`).

#### 2. Component Domain Separation (SRP Contracts)
* **`parsers/`:** Responsible *only* for reading file streams, validating schemas, and outputting immutable DTO objects (`MasterMigrationBlueprint`). It must contain zero SQL generation, string interpolation, or connection-pooling logic.
* **`dialects/`:** Must expose a strict abstract base class (`BaseDialect`). Concrete classes (e.g., `PostgresDialect`) must contain only pure string formatting utilities (e.g., handling safe casting or string concatenation formats). They are completely stateless.
* **`compilers/`:** The orchestrator module. It consumes valid DTO objects and a `BaseDialect` implementation to output the complete SQL transaction string. It must contain zero hardcoded database keywords or file-system interactions.

#### 3. SQL Code Generation Constraints
* **CTE Structural Requirement:** All generated SQL scripts must follow a clean Common Table Expression (CTE) format. Inlining deep joins or mathematical formulas directly inside the final target `INSERT` block is strictly prohibited.
* **Idempotency Guardrails:** Every compiled block must yield an execution script that can safely run repeatedly against the same environment. It must dynamically generate an `UPSERT` syntax string by mapping the `primary_keys` list to an `ON CONFLICT (...) DO UPDATE` target constraint block.

#### 4. Design & Operational Requirements
* **Design Patterns:** Enforce strict decoupling using creational and behavioral design patterns. Implement a **Factory Pattern** for dynamically initializing connection adapters based on the connection type registry, and a **Strategy Pattern** to encapsulate distinct target database SQL dialects (`BaseDialect`).
* **Defensive Error Handling:** Code must never trap generic exceptions or allow critical failures to pass silently. Wrap execution layers in explicit, granular `try-except-finally` structural blocks, ensuring database connections, network sockets, and file handles are explicitly and safely released or closed during unhandled crash states.
* **Structured Telemetry & Logging:** Standardize on structured JSON logging mapped throughout the entire pipeline lifecycle. Every sequence module must emit log schemas capturing runtime execution metadata, including: batch cycle latency benchmarks, table partition indices, extraction row-counts, and structured error dictionaries for isolated row failures.