# crud-activity

# Travel Planner API

## Purpose

The Travel Planner API is a Flask REST API that allows authenticated users to create, view, update, and delete travel plans. The API uses SQLite for persistent data storage and HTTP Basic Authentication for user authentication and ownership.

The API also provides current weather information for a city using the Open-Meteo external API.

## Technologies

* Python 3.12+
* Flask
* Flask-RESTful
* SQLite
* Requests
* pytest
* uv
* Open-Meteo API
* HTTPS with a self-signed certificate

## Project Structure

```text
travel-planner-api/
├── app.py
├── auth.py
├── db.py
├── services.py
├── validation.py
├── external_api.py
├── pyproject.toml
├── README.md
├── .gitignore
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_auth.py
│   ├── test_trips.py
│   ├── test_weather.py
│   └── test_external_api.py
└── .github/
    └── workflows/
        └── tests.yml
```

## Setup

Clone the repository and move into the project directory.

Install the project dependencies with:

```bash
uv sync
```

The project uses SQLite, so no separate database server is required.

The database file is created automatically when the application starts.

## Running the Tests

Run the complete test suite with:

```bash
uv run pytest
```

The tests use a temporary SQLite database so that the real application database is not modified.

## Running the API

The API can be started with:

```bash
uv run api
```

The API uses HTTPS and expects the following files in the project directory:

```text
MyCertificate.crt
MyCertificate.key
```

These files are intentionally excluded from Git.

The API runs on:

```text
https://localhost:5000
```

Because the certificate is self-signed, a browser or curl may display a certificate warning.

For curl commands, use `-k` when testing locally:

```bash
curl -k https://localhost:5000/
```

## Authentication

The API uses HTTP Basic Authentication.

Users must first register an account using:

```http
POST /register
```

Protected endpoints require the username and password through Basic Authentication.

For example:

```bash
curl -k -u alice:password123 https://localhost:5000/trips
```

Authentication failures return:

```http
401 Unauthorized
```

A user can read another user's trip, but only the owner of a trip can modify or delete it.

Attempting to modify or delete another user's trip returns:

```http
403 Forbidden
```

## API Endpoints

### POST /register

Creates a new user account.

#### Request Body

```json
{
  "username": "alice",
  "password": "password123"
}
```

#### Required Fields

| Field    | Type   | Required |
| -------- | ------ | -------- |
| username | string | Yes      |
| password | string | Yes      |

#### Success

```http
201 Created
```

Example response:

```json
{
  "id": 1,
  "username": "alice"
}
```

#### Errors

* `400 Bad Request` — invalid or missing information
* `409 Conflict` — username already exists

---

### POST /trips

Creates a new travel plan for the authenticated user.

#### Authentication

Required.

#### Request Body

```json
{
  "destination": "Chicago",
  "start_date": "2026-12-01",
  "days": 3
}
```

#### Fields

| Field       | Type    | Required | Description                  |
| ----------- | ------- | -------- | ---------------------------- |
| destination | string  | Yes      | Trip destination             |
| start_date  | string  | Yes      | Date in YYYY-MM-DD format    |
| days        | integer | Yes      | Number of days, from 1 to 30 |

The following fields are controlled by the server and cannot be supplied by the client:

* `id`
* `owner_id`
* `created_at`

#### Success

```http
201 Created
```

Example response:

```json
{
  "id": 1,
  "destination": "Chicago",
  "start_date": "2026-12-01",
  "days": 3,
  "owner_id": 1,
  "created_at": "2026-10-08T16:00:00+00:00"
}
```

#### Errors

* `400 Bad Request` — invalid request data
* `401 Unauthorized` — authentication required

---

### GET /trips

Returns travel plans belonging to the authenticated user's accessible trips.

#### Authentication

Required.

#### Query Parameters

| Parameter   | Type    | Required | Description               |
| ----------- | ------- | -------- | ------------------------- |
| destination | string  | No       | Filters by destination    |
| start_date  | string  | No       | Filters by start date     |
| limit       | integer | No       | Maximum number of results |
| offset      | integer | No       | Number of results to skip |

Example:

```text
GET /trips?destination=Chicago
```

Example:

```text
GET /trips?start_date=2026-12-01&limit=10&offset=0
```

#### Success

```http
200 OK
```

Example response:

```json
[
  {
    "id": 1,
    "destination": "Chicago",
    "start_date": "2026-12-01",
    "days": 3,
    "owner_id": 1,
    "created_at": "2026-10-08T16:00:00+00:00"
  }
]
```

#### Errors

* `400 Bad Request` — invalid query parameters
* `401 Unauthorized` — authentication required

---

### GET /trips/<id>

Returns one travel plan.

#### Authentication

Required.

#### Example

```text
GET /trips/1
```

#### Success

```http
200 OK
```

#### Errors

* `400 Bad Request` — invalid ID
* `401 Unauthorized` — authentication required
* `404 Not Found` — trip does not exist

---

### PATCH /trips/<id>

Updates only the fields included in the request.

#### Authentication

Required.

#### Request Body

```json
{
  "destination": "New York",
  "days": 5
}
```

Any combination of the following fields may be supplied:

* `destination`
* `start_date`
* `days`

Server-controlled fields cannot be changed.

#### Success

```http
200 OK
```

#### Errors

* `400 Bad Request` — invalid request data
* `401 Unauthorized` — authentication required
* `403 Forbidden` — authenticated user is not the owner
* `404 Not Found` — trip does not exist

---

### DELETE /trips/<id>

Deletes a travel plan.

#### Authentication

Required.

#### Example

```text
DELETE /trips/1
```

#### Success

```http
204 No Content
```

#### Errors

* `400 Bad Request` — invalid ID
* `401 Unauthorized` — authentication required
* `403 Forbidden` — authenticated user is not the owner
* `404 Not Found` — trip does not exist

---

### GET /weather

Returns current weather information for a city.

#### Authentication

Not required.

#### Query Parameters

| Parameter | Type   | Required |
| --------- | ------ | -------- |
| city      | string | Yes      |

Example:

```text
GET /weather?city=Chicago
```

#### Success

```http
200 OK
```

Example response:

```json
{
  "city": "Chicago",
  "country": "United States",
  "latitude": 41.85,
  "longitude": -87.65,
  "temperature_f": 58.4,
  "weather_code": 3,
  "time": "2026-10-08T15:00"
}
```

#### Errors

* `400 Bad Request` — city is missing or invalid
* `404 Not Found` — city could not be located
* `502 Bad Gateway` — external weather service failed

---

### POST /weather

Returns current weather information using a JSON request body.

#### Request Body

```json
{
  "city": "Chicago"
}
```

#### Success

```http
200 OK
```

The response format is the same as `GET /weather`.

---

## Validation

The API validates all client-provided information.

Examples of invalid requests include:

* Missing required fields
* Incorrect data types
* Blank strings
* Invalid dates
* Days outside the allowed range
* Unknown JSON fields
* Attempts to modify server-controlled fields
* Invalid IDs
* Invalid pagination values

Invalid requests return JSON responses using the following format:

```json
{
  "message": "Description of the error."
}
```

## Database

The API uses Python's standard-library `sqlite3` module.

The database contains two main tables:

### users

Stores registered users.

```text
id
username
password_hash
```

### trips

Stores travel plans.

```text
id
destination
start_date
days
owner_id
created_at
```

The `owner_id` field connects each trip to the user who created it.

All SQL statements that use client-provided values use SQLite parameterized queries with `?` placeholders.

## External API

The weather functionality uses the free Open-Meteo API.

Two different external endpoints are used:

### 1. Geocoding API

The geocoding endpoint searches for a city and returns its latitude and longitude.

```text
https://geocoding-api.open-meteo.com/v1/search
```

The city name is passed as an argument.

### 2. Forecast API

The forecast endpoint uses the latitude and longitude returned by the geocoding API to retrieve current weather information.

```text
https://api.open-meteo.com/v1/forecast
```

The latitude and longitude are passed as arguments.

No API key is required.

## Environment Variables

This project does not require an external API key.

If additional secrets are added in the future, they should be stored in environment variables or a `.env` file and should never be committed to Git.

The following files are also excluded from Git:

```text
.env
MyCertificate.crt
MyCertificate.key
travel.db
*.db
```

## Complete curl Session

The following is an example session using the API.

### 1. Register a user

```bash
curl -k -X POST https://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

### 2. Create a trip

```bash
curl -k -X POST https://localhost:5000/trips \
  -u alice:password123 \
  -H "Content-Type: application/json" \
  -d '{"destination":"Chicago","start_date":"2026-12-01","days":3}'
```

### 3. List trips

```bash
curl -k -u alice:password123 \
  https://localhost:5000/trips
```

### 4. Filter trips

```bash
curl -k -u alice:password123 \
  "https://localhost:5000/trips?destination=Chicago"
```

### 5. Get one trip

```bash
curl -k -u alice:password123 \
  https://localhost:5000/trips/1
```

### 6. Update a trip

```bash
curl -k -X PATCH https://localhost:5000/trips/1 \
  -u alice:password123 \
  -H "Content-Type: application/json" \
  -d '{"days":5}'
```

### 7. Get weather

```bash
curl -k \
  "https://localhost:5000/weather?city=Chicago"
```

### 8. Delete a trip

```bash
curl -k -X DELETE https://localhost:5000/trips/1 \
  -u alice:password123
```

## HTTPS

The API is configured to run over HTTPS using:

```text
MyCertificate.crt
MyCertificate.key
```

The certificate and private key are excluded from version control through `.gitignore`.

## Testing

The project contains tests for:

* User registration
* Authentication
* Invalid authentication
* Trip creation
* Trip retrieval
* Trip filtering
* Trip updates
* Trip deletion
* Ownership restrictions
* Input validation
* Pagination
* Weather endpoints
* External API requests
* Error handling

Run all tests with:

```bash
uv run pytest
```

The tests use a temporary database rather than the application's real database.

## Git Workflow

The project was developed using separate feature branches for major components.

Branches include:

```text
main
feature/auth
feature/crud
feature/weather
feature/tests
feature/documentation
```

The feature branches are retained in the repository as required.

##AI Usage

AI assistance was used during development to help understand assignment requirements, troubleshoot errors, explain Python and Flask concepts, and assist with code structure and testing.
