## Test Task for Python Developer: Async REST Service Development

### Objective:

Develop an asynchronous REST service using aiohttp, pydantic, and redis for real-time cryptocurrency conversion.

### Core Task:

Create an endpoint at /api/v1/convert to facilitate the conversion between various cryptocurrencies.

### Supported Exchanges:

The service should support the following cryptocurrency exchanges (You can access the public APIs of these exchanges
without credentials):

* Binance
* KuCoin

### Request Schema:

```json
{
  "currency_from": "USDT",
  "currency_to": "TRX",
  "exchange": null,
  "amount": 100,
  "cache_max_seconds": 1000
}
```

### Response Schema:

```json
{
  "currency_from": "USDT",
  "currency_to": "TRX",
  "exchange": "binance",
  "rate": "8.21",
  "result": "821",
  "updated_at": 1714304596
}
```

### Key Requirements:

#### 1. Dynamic Exchange Handling:

* If no specific exchange is designated (exchange is null), the service should iterate through the supported exchanges
  until the requested currency pair is found.
* If the currency pair is not available on any listed exchange, an error message should be returned to the user.

#### 2. Caching Mechanism:

* Cache the available currency pairs and their conversion rates in Redis.
* If the user requests a refresh interval (cache_max_seconds), and the data is
  older than specified, re-fetch the data.
* If cache_max_seconds is set to null, always fetch the latest data regardless of
  the cache.

#### 3. Indirect Currency Conversion:

* If a direct conversion rate between currency_from and currency_to is not available, attempt to find a common
  intermediary currency (e.g., converting TRX to ADA via USDT if direct TRX to ADA is unavailable).

#### 4. Robust Network Handling:

* Properly handle network errors or exchange unavailability by attempting the next
  available exchange.
* If all exchanges are down, return an error message to the user indicating the
  issue.

## Project Instructions:

### Installation

To install the project, run the following command:

```shell
make install
```

This command will install the necessary dependencies and set up the project.

Note: You need Python 3.11 installed.

### Running the Project

To run the project, use one of the following commands:

* Local Run: To run the project locally, use:

```shell
make run
```

* Gunicorn Run: To run the project with gunicorn, use:

```shell
make gunicorn
```

These commands will start the project and make it available for use.

### Code Quality

To ensure code quality, we use the following tools:

* Linting: To run the linter, use:

```shell
make lint
```

This command will check the code for any syntax errors or formatting issues.

* Formatting: To format the code, use:

```shell
make format
```

This command will format the code according to the project's style guidelines.

### Docker

To run the project in a Docker container, use the following command:

```shell
make docker.up
```

To stop the project in a Docker container, use the following command:
```shell
make docker.down
```


This command will start the Docker container and make the project available for use.

Note: Make sure you have Docker installed and configured properly before running this command.
