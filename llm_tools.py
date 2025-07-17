import os
import requests
import json

class TokenManager:
    _instance = None
    _token = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_token(cls):
        return cls._token

    @classmethod
    def set_token(cls, token):
        cls._token = token


def generate_token(base_url, tenant_name):
    print("Generating token")
    url = f"{base_url}/auth-engine-api/v1/api-key/token"
    headers = {
        "accept": "/",
        "Content-Type": "application/json",
        "FlowTenant": tenant_name,
    }
    payload = {
        "clientId": os.getenv("client_id"),
        "clientSecret": os.getenv("client_secret"),
        "appToAccess": os.getenv("app_to_access"),
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Token generated")
        return response.json().get("access_token")
    else:
        print(f"Error generating token: {response.status_code} - {response.text}")
        return None


# Step 2: Use Token to Call API
def call_llm_api(base_url, tenant_name, agent_name, user_message):
    token_manager = TokenManager()
    if not token_manager.get_token():
        new_token = generate_token(base_url, tenant_name)
        token_manager.set_token(new_token)

    url = f"{base_url}/ai-orchestration-api/v1/openai/chat/completions"
    headers = {
        "FlowTenant": tenant_name,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "FlowAgent": agent_name,
        "Authorization": f"Bearer {token_manager.get_token()}",
    }
    payload = {
        "stream": False,
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 3000,
        "model": "gpt-4o-mini",
    }
    print("Calling llm api")
    response = requests.post(url, headers=headers, json=payload)
    
    # Check for Invalid JWT error and retry once with new token
    if response.status_code == 401 and "Invalid JWT" in response.text:
        print("Invalid JWT detected, generating new token and retrying...")
        new_token = generate_token(base_url, tenant_name)
        if new_token:
            token_manager.set_token(new_token)
            headers["Authorization"] = f"Bearer {new_token}"
            response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("Response received")
        return response.json()
    else:
        print(f"Error calling API: {response.status_code} - {response.text}")
        return None


def generate_sql_query(base_url, tenant_name, agent_name, user_question, schema_context):
    """Generate SQL query based on user question and schema context"""
    
    prompt = f"""Given this database schema context:
{schema_context}

Generate a SQL query to answer this question: {user_question}

The query should always use the full column names to avoid ambiguity, and it should be a valid SQL query that can be executed directly on the database.
MySQL does not have DATE_TRUNC, please use "DATE_FORMAT(your_date_column, '%Y-%m-01') AS truncated_date". This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
The response should be in JSON, containing the SQL query and an explanation of what the query does.
The response should not contain any additional text or formatting.
"""
    print("Attempting to create query with LLM")
    response = call_llm_api(base_url, tenant_name, agent_name, prompt)
    
    if response and 'choices' in response:
        content = response['choices'][0]['message']['content']
        # Parse the response to extract SQL query
        try:
            json_data = json.loads(content.strip())  # Ensure the content is valid JSON
            sql = json_data.get('sql_query', json_data.get('query', json_data.get('sql', ''))).strip()
            print(f"Generated SQL: {sql}")
            explanation = json_data.get('explanation', '').strip()
            return sql, explanation
        except:
            return None, f"Could not parse LLM response. {response}"
    
    return None, f"LLM response did not contain choices. {response}"
