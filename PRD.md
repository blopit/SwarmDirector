## Summary

This document outlines the full software design for the prototype phase of our hierarchical AI agent system, detailing architecture, components, data storage, API design, non-functional requirements, and a development timeline for rapid iteration ([atlassian.com][1]). We leverage Flask for backend routing, SQLite for embedded data storage, and Microsoft’s AutoGen framework for agent orchestration, enabling a lightweight yet functional proof of concept ([digitalocean.com][2], [github.com][3]). This lean setup facilitates quick feedback loops without heavy infrastructure and supports core flows including Director routing, parallel draft reviews, and streaming agents ([stackoverflow.com][4]).

## 1. Objectives

The prototype’s primary objective is to validate the Director → CommunicationsDept → EmailAgent workflow end-to-end, including self-review by multiple DraftReviewAgents for high accuracy ([github.com][5]). We also aim to demonstrate autogen streaming agents at the edge for low-latency interactions and lay groundwork for future department additions ([microsoft.github.io][6]).

## 2. High-Level Architecture

The system comprises three core agent classes: DirectorAgent, CommunicationsDept, and EmailAgent ([microsoft.github.io][6]). DirectorAgent is exposed via a Flask HTTP endpoint and routes incoming task requests based on a simple keyword-based intent classifier ([julio-souto.medium.com][7]). CommunicationsDept chains two DraftReviewAgent instances in parallel to produce a consensus draft before delegating to EmailAgent ([github.com][5]). EmailAgent wraps SMTP functionality using Flask-Mail and Python’s smtplib to send finalized messages ([mailtrap.io][8]).

## 3. Component Details

### 3.1 DirectorAgent

DirectorAgent is implemented in `app.py` as a Flask route at `/task` that accepts JSON payloads containing `type` and `args` fields ([julio-souto.medium.com][7]). It applies a simple LLM-based or keyword-based router to dispatch tasks to the correct department’s `run` method ([microsoft.github.io][9]).

### 3.2 CommunicationsDept

CommunicationsDept extends AutoGen’s `ChatAgent` class and manages message drafting workflows ([github.com][3]). It spawns two DraftReviewAgent instances via a `MultiAgentChain`, then merges critiques into a final draft using reconciliation logic ([altexsoft.com][10]).

### 3.3 DraftReviewAgent

Each DraftReviewAgent uses AutoGen to critique a draft in isolation, returning a JSON diff of suggested edits ([github.com][5]).

### 3.4 EmailAgent

EmailAgent is a `ToolAgent` configured with the Flask-Mail extension to interface with SMTP servers for email delivery ([flask-mail.readthedocs.io][11]). It parses the draft object for recipient, subject, and body fields and invokes `mail.send` to dispatch the message, returning success or error codes ([mailtrap.io][12]).

## 4. Data Storage

We use SQLite for the prototype to store agent logs, task metadata, and draft versions in an embedded, file-based database ([digitalocean.com][2]). This eliminates external dependencies and simplifies setup, with migration to PostgreSQL planned for MVP ([stackoverflow.com][4]).

## 5. API Design

A single RESTful endpoint (`POST /task`) accepts JSON with `type`, `user_id`, and `payload` fields to centralize task submission ([learn.microsoft.com][13]). Responses include HTTP status codes, a `task_id`, and a `result` object containing department-specific outputs ([stackoverflow.blog][14]). Error handling follows standard JSON error envelopes with `error_code` and `message` fields for consistent client behavior ([medium.com][15]).

## 6. Sequence Flow

Upon receiving a request, DirectorAgent logs the request in SQLite and invokes the routing logic ([atlassian.com][1]). The routed department agent (CommunicationsDept) initiates two concurrent calls to DraftReviewAgent via AutoGen’s `MultiAgentChain` ([microsoft.github.io][6]). After collecting reviews, CommunicationsDept consolidates the critiques, finalizes the draft, and calls EmailAgent to send the email ([github.com][5]). EmailAgent uses Flask-Mail to dispatch the message and updates the task status in the database before DirectorAgent returns the result to the client ([mailtrap.io][8]).

## 7. Non-Functional Requirements

The system must handle at least 10 concurrent requests during prototype demos without significant slowdown ([altexsoft.com][16]). Logs and data integrity must be preserved across crashes, leveraging SQLite’s ACID compliance ([sqlite.org][17]). Response times should remain under 500 ms for individual API calls under typical demo workloads ([altexsoft.com][16]). The prototype must support autogen streaming without token loss, ensuring real-time feedback for edge agents ([microsoft.github.io][6]).

## 8. Prototype Timeline

* **Week 1:** Set up project skeleton with Flask service and SQLite schema ([julio-souto.medium.com][7])
* **Week 2:** Implement DirectorAgent and basic routing logic ([microsoft.github.io][6])
* **Week 3:** Develop CommunicationsDept and integrate parallel DraftReviewAgents ([github.com][5])
* **Week 4:** Build EmailAgent with SMTP integration and test end-to-end email flow ([mailtrap.io][8])
* **Week 5:** Add autogen streaming edge interface and complete end-to-end prototype demo ([microsoft.github.io][9])

---

With this design document, you have a clear, step-by-step blueprint for building and validating the prototype. Let me know when you’re ready to start coding, and we can dive into stub implementations!

[1]: https://www.atlassian.com/work-management/knowledge-sharing/documentation/software-design-document?utm_source=chatgpt.com "Software Design Document [Tips & Best Practices] - Atlassian"
[2]: https://www.digitalocean.com/community/tutorials/how-to-use-an-sqlite-database-in-a-flask-application?utm_source=chatgpt.com "How To Use an SQLite Database in a Flask Application - DigitalOcean"
[3]: https://github.com/microsoft/autogen?utm_source=chatgpt.com "microsoft/autogen: A programming framework for agentic AI ... - GitHub"
[4]: https://stackoverflow.com/questions/27787667/use-sqlite3-for-prototyping-in-a-flask-app?utm_source=chatgpt.com "Use sqlite3 for prototyping in a flask app - python - Stack Overflow"
[5]: https://github.com/ag2ai/ag2?utm_source=chatgpt.com "ag2ai/ag2: AG2 (formerly AutoGen): The Open-Source ... - GitHub"
[6]: https://microsoft.github.io/autogen/stable//index.html?utm_source=chatgpt.com "AutoGen"
[7]: https://julio-souto.medium.com/a-flask-tutorial-in-few-minutes-with-sqlite-sqlalchemy-and-jinja2-95d36578904e?utm_source=chatgpt.com "A Flask Tutorial in few minutes with SQLite, SQLAlchemy and Jinja2"
[8]: https://mailtrap.io/blog/flask-email-sending/?utm_source=chatgpt.com "Flask Send Email: Tutorial with Code Snippets [2025] - Mailtrap"
[9]: https://microsoft.github.io/autogen/0.2/?utm_source=chatgpt.com "AutoGen 0.2 - Microsoft Open Source"
[10]: https://www.altexsoft.com/blog/functional-and-non-functional-requirements-specification-and-types/?utm_source=chatgpt.com "Functional and Nonfunctional Requirements Specification - AltexSoft"
[11]: https://flask-mail.readthedocs.io/?utm_source=chatgpt.com "Flask-Mail 0.10.0 documentation"
[12]: https://mailtrap.io/blog/flask-send-email-gmail/?utm_source=chatgpt.com "Flask Send Email Gmail: Tutorial with Code Snippets [2025] - Mailtrap"
[13]: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design?utm_source=chatgpt.com "Web API Design Best Practices - Azure Architecture Center"
[14]: https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/?utm_source=chatgpt.com "Best practices for REST API design - The Stack Overflow Blog"
[15]: https://medium.com/%40lewis.devs/how-to-send-an-e-mail-with-flask-a13e751a5cab?utm_source=chatgpt.com "How to send an e-mail with Flask and Flask-Mail? | by Lewis ALLEDJI"
[16]: https://www.altexsoft.com/blog/non-functional-requirements/?utm_source=chatgpt.com "Nonfunctional Requirements: Examples, Types and Approaches"
[17]: https://www.sqlite.org/transactional.html?utm_source=chatgpt.com "SQLite Is Transactional"
