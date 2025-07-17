# LLM Query

A proof-of-concept application demonstrating the power of using Large Language Models (LLMs) to construct and analyze SQL queries for database interaction.

## Overview

This project showcases how LLMs can be leveraged to:
1. Convert natural language questions into valid SQL queries
2. Analyze and summarize database query results in human-readable format
3. Provide explanations of SQL queries for educational purposes

The application connects to a MySQL database (specifically the Sakila sample database) and allows users to query it using natural language instead of writing SQL directly.

## Features

- **Natural Language to SQL**: Converts user questions into executable SQL queries
- **Query Explanation**: Provides detailed explanations of generated SQL queries
- **Result Analysis**: Summarizes query results in natural language with markdown formatting
- **Movie Analysis**: Demonstrates LLM capabilities by analyzing movie data
- **Token Management**: Handles authentication with automatic token refresh

## Architecture

The application consists of:

- **Flask Web Application** (`llm_query.py`): Handles HTTP requests and renders templates
- **LLM Integration Tools** (`llm_tools.py`): Manages API calls to the LLM service
- **Web Interface** (`templates/index.html`, `templates/query.html`): User interface for interacting with the system

## Prerequisites

- Python 3.7+
- MySQL database (Sakila sample database)
- Access to an LLM API service

## Environment Variables

Create a `.env` file with the following variables:

```
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
BASE_URL=your_llm_api_base_url
TENANT_NAME=your_tenant_name
AGENT_NAME=your_agent_name
client_id=your_client_id
client_secret=your_client_secret
app_to_access=your_app_to_access
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up the environment variables
4. Run the application:
   ```
   python llm_query.py
   ```

## Usage

### Basic Movie Search
1. Navigate to the home page
2. Type "movies" in the search box to see the first 3 films with LLM analysis

### Natural Language Queries
1. Navigate to `/query`
2. Enter a question about the database in natural language
3. View the generated SQL, explanation, and results with analysis

## Example Queries

- "Show me the most popular movies in the comedy category"
- "Which actors have appeared in the most films?"
- "Find all rentals that were returned late last month"
- "What are the rental anomalies for horror movies?"

## Technical Details

The application uses:
- Flask for the web framework
- MySQL Connector for database access
- Requests library for API calls
- JSON for data formatting
- Markdown for result presentation

## Future Enhancements

- Add support for more complex queries
- Implement query history and saving
- Add visualization of query results
- Expand to support multiple database types
- Implement user authentication and personalization

## License

[Specify your license here]

## Contributors

[List contributors here]