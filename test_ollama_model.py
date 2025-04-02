import requests
import json
import pandas as pd

def test_ollama_model():
    """Test the Ollama model with spring parameters"""
    # Spring parameters
    params = {
        'Free Length': 58,
        'Test Type': 'Compression',
        'L1': {'position': 40, 'force': 23.6},
        'L2': {'position': 33, 'force': 34.14},
        'L3': {'position': 28, 'force': 42.36}
    }
    
    # Format the parameter text
    parameter_text = "SPRING SPECIFICATIONS:\n"
    for key, value in params.items():
        if key not in ['prompt', 'Test Type']:
            if isinstance(value, dict):
                parameter_text += f"- {key}: position = {value.get('position', 'N/A')}mm, force = {value.get('force', 'N/A')}N\n"
            else:
                parameter_text += f"- {key}: {value}\n"
    
    # Add test type
    test_type_text = ""
    if "Test Type" in params:
        test_type = params["Test Type"]
        test_type_text = f"This should be a {test_type} test sequence."
    
    # Create the prompt
    prompt = f"""
{parameter_text}

{test_type_text}

Generate a test sequence for this spring. Reply with ONLY a valid JSON array.
"""
    
    # Make the API request to Ollama
    payload = {
        "model": "spring-assistant-complete",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.5
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            response_data = response.json()
            response_text = response_data.get("response", "")
            
            print("Raw response:")
            print(response_text)
            
            # Try to extract JSON
            json_start_idx = response_text.find("[")
            json_end_idx = response_text.rfind("]") + 1
            
            if json_start_idx >= 0 and json_end_idx > json_start_idx:
                json_content = response_text[json_start_idx:json_end_idx]
                try:
                    data = json.loads(json_content)
                    print("\nParsed JSON data:")
                    print(f"Number of commands: {len(data)}")
                    for i, cmd in enumerate(data):
                        print(f"{i+1}. {cmd.get('Row', 'N/A')}: {cmd.get('CMD', 'N/A')}")
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    print("\nDataFrame columns:")
                    print(df.columns.tolist())
                    print("\nDataFrame shape:")
                    print(df.shape)
                    
                except json.JSONDecodeError as e:
                    print(f"\nError parsing JSON: {e}")
                    print(f"JSON content: {json_content}")
            else:
                print("\nNo JSON found in response")
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_ollama_model() 