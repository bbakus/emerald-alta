# Emerald Altar

A fantasy RPG game with a Mesoamerican mythology theme.

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory with the following content:
   ```
   # Environment Variables for Emerald Altar Backend
   # API Keys
   OPENAI_API_KEY=your_openai_api_key_here

   # Application Settings
   FLASK_APP=app
   FLASK_ENV=development
   ```

4. Replace `your_openai_api_key_here` with your actual OpenAI API key.

5. Test your OpenAI API key configuration:
   ```
   python test_openai.py
   ```
   If successful, you should see a confirmation message.

6. Run the application:
   ```
   python run.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

## Environment Variables

The application uses the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI chat generation and quest creation
- `FLASK_APP`: Sets the Flask application entry point
- `FLASK_ENV`: Sets the Flask environment (development or production)

These variables should be set in a `.env` file in the backend directory.

## GitHub & Security

### Protecting Your API Keys

When pushing to GitHub or any public repository:

1. The `.gitignore` file is already configured to prevent `.env` files from being committed
2. Always check your commits with `git status` before pushing to ensure sensitive files aren't included
3. NEVER commit your `.env` file containing real API keys
4. Use `.env.example` as a template to show which environment variables are needed (without real values)
5. If you accidentally commit an API key, consider it compromised and regenerate it immediately

### Setting Up After Cloning

If you've cloned this repository:

1. Copy `.env.example` to `.env` in the backend directory: `cp backend/.env.example backend/.env`
2. Add your own OpenAI API key to the `.env` file
3. Follow the standard setup instructions above

## Troubleshooting

### OpenAI API Issues

If you encounter issues with the OpenAI API:

1. Make sure your API key is correctly set in the `.env` file
2. Ensure you have sufficient credits in your OpenAI account
3. Run the test script to check your configuration:
   ```
   python test_openai.py
   ```
4. Check the application logs for detailed error messages
