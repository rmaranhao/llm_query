from dotenv import load_dotenv
import os
import mysql.connector
from flask import Flask, request, render_template, jsonify
from llm_tools import call_llm_api, generate_sql_query

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get database credentials from environment variables
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": "sakila",
    "auth_plugin": "mysql_native_password",
}

# Database schema context for the LLM
SCHEMA_CONTEXT = """
List commands should be limited to 50 entries.
Rental duration is always in days.

Key tables and their relationships:
- film: Contains movie information (title, description, rating, etc)
- actor: Contains actor information (first_name, last_name)
- film_actor: Links films and actors
- category: Movie categories/genres (name)
- film_category: Links films and categories 
- inventory: Tracks movie copies in stores
- rental: Tracks movie rentals (rental_id, rental_date, inventory_id, customer_id, return_date, staff_id, last_update)
- payment: Payment records for rentals

Views:
- rental_anomalies_by_month: Analyzes rental patterns and identifies anomalies per month (rental_month, title, category, rental_rate, rental_count, avg_rental_duration_days)
  * Rental duration is in days;
  * Shows unusual rental patterns or pricing compared to category averages 
  * Identifies anomaly types:
    - Never Rented
    - Significantly Under-Rented
    - Significantly Over-Rented
    - Overpriced for Category
    - Underpriced for Category
    - High Rental Rate vs Replacement Cost
  * Compares against category averages and standard deviations
"""

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def get_first_3_films():
    connection = get_db_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM film LIMIT 3")
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    

def format_films_with_llm(films):
    if not films:
        return None
    
    # Create a formatted string of film data
    films_text = "Here are the films from the database:\n"
    for film in films:
        films_text += f"Title: {film['title']}\n"
        films_text += f"Description: {film['description']}\n"
        films_text += f"Rating: {film['rating']}\n"
        films_text += "---\n"
    
    # Prepare prompt for LLM - using dedent to remove leading spaces
    prompt = f"""Please analyze these movies and provide a structured summary with improved language:
{films_text}

Format the response in clean markdown with:
# Movie Analysis

## Overview
(Brief overview of the films)

## Patterns
(Notable patterns in ratings or themes)

## Observations
(Interesting observations)

Use proper markdown formatting with headers, bullet points, and emphasis.
If the query contains a limit clause assume its a system limitation and alert the user that results are partial."""
    
    # Call LLM API
    base_url = os.getenv("BASE_URL", "https://flow.ciandt.com")
    tenant_name = os.getenv("TENANT_NAME", "cit")
    agent_name = os.getenv("AGENT_NAME", "Chat")
    
    print("Attempting to summarize data")
    response = call_llm_api(base_url, tenant_name, agent_name, prompt)
    
    if response and 'choices' in response:
        # Clean up the response by removing extra whitespace
        content = response['choices'][0]['message']['content']
        # Split into lines, strip each line, and rejoin
        cleaned_content = '\n' + '\n'.join(line.strip() for line in content.splitlines())
        return cleaned_content
    return "Sorry, I couldn't analyze the films at this time."


@app.route("/", methods=["GET", "POST"])
def index():
    films = None
    analysis = None
    if request.method == "POST":
        query = request.form.get("query")
        if query and query.lower() == "movies":
            films = get_first_3_films()
            if films:
                analysis = format_films_with_llm(films)
    return render_template("index.html", films=films, analysis=analysis)


@app.route("/query", methods=["GET", "POST"])
def query():
    if request.method == "GET":
        return render_template("query.html")
        
    # Handle POST request
    user_question = request.form.get("question")
    if not user_question:
        return jsonify({"error": "No question provided"})

    # Generate SQL query using LLM
    base_url = os.getenv("BASE_URL", "https://flow.ciandt.com")
    tenant_name = os.getenv("TENANT_NAME", "cit")
    agent_name = os.getenv("AGENT_NAME", "Chat")
    
    sql_query, explanation = generate_sql_query(
        base_url, tenant_name, agent_name, 
        user_question, SCHEMA_CONTEXT
    )
    
    if not sql_query:
        return jsonify({"error": f"Could not generate SQL query: {explanation}"})

    # Clean up the SQL query
    sql_query = sql_query.strip().rstrip(';')  # Remove trailing semicolon and whitespace
    
    # Execute the query
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"})
            
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            if not results:
                results = []  # Return empty list instead of None
        except mysql.connector.Error as err:
            return jsonify({"error": f"Query {sql_query} execution failed: {err}"})
        finally:
            cursor.close()
            connection.close()
        print(f"Executed SQL query: {sql_query}")
        # Format results with LLM
        results_text = f"Query results ({len(results)} rows):\n{str(results)}"
        prompt = f"""Analyze these database query results and provide a natural language summary:
{results_text}

Original question: {user_question}
SQL Query used: {sql_query}
Query explanation: {explanation}

Format the response in markdown with clear sections."""

        print("Attempting to summarize data")
        analysis = call_llm_api(base_url, tenant_name, agent_name, prompt)
        if analysis and 'choices' in analysis:
            analysis_text = analysis['choices'][0]['message']['content']
        else:
            analysis_text = "Could not analyze results in {analysis}"

        print(f"All done. Returning results.")
        return jsonify({
            "query": sql_query,
            "explanation": explanation,
            "results": results,
            "analysis": analysis_text
        })

    except mysql.connector.Error as err:
        return jsonify({"analysis": f"Analysis error: {err}"})


if __name__ == "__main__":
    app.run(debug=True)
