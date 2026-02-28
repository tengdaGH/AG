---
name: global_coding_standards
description: Enforces strict global coding standards for the project, primarily mandating the absolute use of English for all codebase elements to ensure internationalization, stability, and compatibility.
tags:
  - english
  - standards
  - conventions
  - global
---

# Global Coding Standards

To ensure long-term stability, ecosystem compatibility, and internationalization scalability of the testing platforms, the following coding standards are **strictly enforced**.

## 1. Absolute English Requirement
- **Code is 100% English**: ALL code, including variable names, function names, database schemas, object keys, and comments, MUST be written entirely in English.
- **No Chinese / Pinyin in Codebase**: Do not use Chinese characters, Pinyin representations, or non-ASCII characters for any logic, state, testing mocks, or infrastructural naming (e.g., use `fetchData` not `huoquData`, use `studentName` not `xueshengMingzi`).
- **UI Content Exception**: The ONLY exception where non-English languages are permitted is in strings rendered as literal UI text to the end-user (e.g., `<button>提交答案</button>`), or in localized JSON asset files specifically handling internationalization (i18n).

## 2. Naming Conventions (English Only)
- **Variables / Functions**: `camelCase` (e.g., `isLoggedIn`, `handleSubmission`)
- **Components / Classes**: `PascalCase` (e.g., `CTestInput`, `TestSequencer`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `API_BASE_URL`)
- **Database Fields / API Payloads**: `snake_case` (e.g., `user_id`, `target_answer`) to ensure standard alignment with typical REST/SQL conventions.

## 3. Comments and Documentation
- Inline comments, JSDoc blocks, and technical documentation within `.ts`, `.tsx`, and `.py` files **must be in English**. This enables cross-functional or multi-national teams to understand the system without translation overhead.

## 4. Enforcement
- Whenever writing new files or modifying existing code, adhere strictly to these English conventions. Refactor any newly discovered non-English identifiers or comments to English immediately unless they are user-facing UI strings.
