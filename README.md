# Simple Community Directory

This repository contains a lightweight demo web application that showcases a
minimal people directory. The database keeps only the essential fields the team
requested: **first name**, **last name**, and **ZIP code**.

## Tech stack

- **Python standard library** HTTP server for the API and static hosting
- **SQLite** for persistent storage (created automatically on first run)
- **Vanilla JavaScript** + HTML/CSS for the interface

## Getting started

1. Make sure you have Python 3.9 or newer installed.
2. Run the development server:

   ```bash
   python app.py
   ```

3. Open <http://127.0.0.1:5000/> in your browser.

## API

| Method | Endpoint      | Description         |
| ------ | ------------- | ------------------- |
| GET    | `/api/people` | List all directory entries |
| POST   | `/api/people` | Add a new entry (JSON body with `first_name`, `last_name`, `zip_code`) |

## Notes

- The SQLite database file (`people.db`) is ignored by Git and created
  automatically with a few sample entries the first time the server starts.
- The interface intentionally focuses on the simplest possible dataset while
  still demonstrating a complete request/response cycle.
