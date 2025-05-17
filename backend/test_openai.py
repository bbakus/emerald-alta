#!/usr/bin/env python3
"""
Test script for OpenAI API key configuration
This script checks if your OpenAI API key is configured correctly.
"""

from dotenv import load_dotenv
import os
import requests
import json
import time

def test_openai_api():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please create a .env file in the backend directory with your OpenAI API key.")
        print("Example: OPENAI_API_KEY=your_key_here\n")
        return False
    
    # Test the API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'The OpenAI API key is working correctly!'"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    print("Testing OpenAI API connection...")
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            print(f"\n✅ SUCCESS: {content}")
            print("\nYour OpenAI API key is configured correctly.")
            return True
        else:
            print(f"\n❌ ERROR: Unable to connect to OpenAI API (HTTP {response.status_code})")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: Exception when calling OpenAI API: {str(e)}")
        return False

def test_dalle_api():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        return
    
    # Use absolute minimum parameters for the request
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Simplest possible request
    data = {
        "model": "dall-e-2",  # Try with DALL-E 2 first
        "prompt": "A simple cartoon smiley face",
        "n": 1,
        "size": "1024x1024"
    }
    
    print("Testing basic DALL-E 2 API call...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Now try with DALL-E 3
    data["model"] = "dall-e-3"
    print("\nTesting DALL-E 3 API call...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_openai_api()
    test_dalle_api() 