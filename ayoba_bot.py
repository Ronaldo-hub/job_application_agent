import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import gmail_tool
import documents

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/oauth_callback')
def oauth_callback():
    """Handle OAuth callback from Google."""
    try:
        code = request.args.get('code')
        state = request.args.get('state')  # user_id

        if not code or not state:
            logger.error("Missing code or state in OAuth callback")
            return "Error: Missing authorization code or state.", 400

        # Exchange code for token
        creds = gmail_tool.exchange_code_for_token(code, state)
        logger.info(f"OAuth successful for user {state}")

        return "Authorization successful! You can close this window and return to Ayoba."
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        return "Error during authorization.", 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/upload_doc', methods=['POST'])
def upload_document():
    """Handle document upload via Flask endpoint."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        doc_type = request.form.get('doc_type', 'certificate')  # Default to certificate

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        result = documents.upload_document(file, doc_type)

        if result['success']:
            return jsonify({
                "message": result['message'],
                "doc_id": result['doc_id']
            }), 200
        else:
            return jsonify({"error": result['error']}), 400

    except Exception as e:
        logger.error(f"Error in upload_doc endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ayoba_webhook', methods=['POST'])
def ayoba_webhook():
    """Handle Ayoba webhook for messages and commands."""
    try:
        data = request.get_json()
        logger.info(f"Received Ayoba webhook: {data}")

        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        # Extract message details
        message = data.get('message', {})
        sender = message.get('sender', '')
        content = message.get('content', '')

        if not content:
            return jsonify({"status": "received"}), 200

        # Handle commands
        if content.startswith('!'):
            command = content[1:].strip().lower()

            if command.startswith('upload_doc'):
                # Parse upload_doc command
                # Expected format: !upload_doc certificate|degree|diploma|id
                parts = command.split()
                if len(parts) >= 2:
                    doc_type = parts[1]
                    response_msg = f"Please upload your {doc_type} document using the /upload_doc endpoint or attach it to this message."
                else:
                    response_msg = "Usage: !upload_doc <type> where type is certificate, degree, diploma, or id"

                # Here you would send response back to Ayoba
                # For now, just log it
                logger.info(f"Ayoba command response: {response_msg}")

            elif command == 'list_docs':
                # List uploaded documents
                docs = documents.list_documents()
                if docs:
                    response_msg = f"You have {len(docs)} uploaded documents: " + ", ".join([d['filename'] for d in docs])
                else:
                    response_msg = "No documents uploaded yet."

                logger.info(f"Ayoba command response: {response_msg}")

            elif command == 'help':
                response_msg = "Available commands: !upload_doc <type>, !list_docs, !help"
                logger.info(f"Ayoba command response: {response_msg}")

            else:
                response_msg = f"Unknown command: {command}. Type !help for available commands."
                logger.info(f"Ayoba command response: {response_msg}")

        else:
            # Handle regular messages
            response_msg = "Hello! I'm your job application assistant. Type !help for available commands."
            logger.info(f"Ayoba message response: {response_msg}")

        return jsonify({"status": "received"}), 200

    except Exception as e:
        logger.error(f"Error in Ayoba webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))