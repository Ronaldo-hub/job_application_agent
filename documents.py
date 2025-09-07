import json
import os
import logging
import requests
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
import pdfplumber

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
if not HUGGINGFACE_API_KEY:
    logger.error("HUGGINGFACE_API_KEY not found in environment variables")
    raise ValueError("HUGGINGFACE_API_KEY is required")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
DOCUMENTS_JSON = 'documents.json'

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure upload folder exists."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF document."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

def save_document_metadata(doc_id: str, filename: str, doc_type: str, content: str) -> Dict:
    """Save document metadata to JSON file."""
    try:
        metadata = {
            "id": doc_id,
            "filename": filename,
            "path": os.path.join(UPLOAD_FOLDER, filename),
            "type": doc_type,
            "content_preview": content[:500],  # First 500 chars
            "uploaded_at": str(os.path.getctime(os.path.join(UPLOAD_FOLDER, filename)))
        }

        # Load existing documents
        documents = load_documents_metadata()

        # Add new document
        documents[doc_id] = metadata

        # Save back to file
        with open(DOCUMENTS_JSON, 'w') as f:
            json.dump(documents, f, indent=2)

        logger.info(f"Document metadata saved for {filename}")
        return metadata

    except Exception as e:
        logger.error(f"Error saving document metadata: {e}")
        raise

def load_documents_metadata() -> Dict:
    """Load documents metadata from JSON file."""
    try:
        if os.path.exists(DOCUMENTS_JSON):
            with open(DOCUMENTS_JSON, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading documents metadata: {e}")
        return {}

def upload_document(file, doc_type: str) -> Dict:
    """Handle document upload."""
    try:
        ensure_upload_folder()

        if not file or not allowed_file(file.filename):
            raise ValueError("Invalid file or file type not allowed")

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Extract text content
        content = extract_pdf_text(file_path)

        # Generate unique ID
        doc_id = f"{doc_type}_{os.path.splitext(filename)[0]}"

        # Save metadata
        metadata = save_document_metadata(doc_id, filename, doc_type, content)

        logger.info(f"Document uploaded successfully: {filename}")
        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Document {filename} uploaded successfully"
        }

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def select_relevant_documents(job_details: Dict) -> List[Dict]:
    """Select job-relevant documents using Llama 3.1."""
    try:
        documents = load_documents_metadata()
        if not documents:
            logger.info("No documents available for selection")
            return []

        # Prepare document list for AI analysis
        doc_list = []
        for doc_id, metadata in documents.items():
            doc_list.append({
                "id": doc_id,
                "type": metadata.get("type", ""),
                "content": metadata.get("content_preview", "")
            })

        prompt = f"""
        You are a document relevance analyzer. Your task is to select documents that are most relevant for a job application.

        JOB DETAILS:
        Title: {job_details.get('job_title', 'Unknown')}
        Required Skills: {', '.join(job_details.get('skills', []))}
        Description: {job_details.get('description', '')}

        AVAILABLE DOCUMENTS:
        {json.dumps(doc_list, indent=2)}

        ANALYSIS INSTRUCTIONS:
        1. Review each document's type and content preview
        2. Determine relevance to the job requirements
        3. Consider document types: certificates, degrees, diplomas, IDs
        4. Select documents that would strengthen the job application
        5. Prioritize documents that match job skills or requirements

        Provide your selection in the following JSON format:
        {{
            "selected_documents": [
                {{
                    "doc_id": "document_id",
                    "relevance_score": 1-10,
                    "reason": "why this document is relevant"
                }}
            ],
            "total_selected": number
        }}

        Return only the JSON response.
        """

        # Hugging Face Inference API call
        response = requests.post(
            'https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct',
            headers={
                'Authorization': f'Bearer {HUGGINGFACE_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': 512,
                    'temperature': 0.1,
                    'do_sample': True
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                api_response = result[0].get('generated_text', '').strip()
            else:
                raise Exception("Unexpected API response format")

            # Extract JSON from response
            try:
                start = api_response.find('{')
                end = api_response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = api_response[start:end]
                    selection_result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

                selected_docs = selection_result.get('selected_documents', [])

                # Update metadata with relevance
                for selected in selected_docs:
                    doc_id = selected['doc_id']
                    if doc_id in documents:
                        documents[doc_id]['relevance_score'] = selected.get('relevance_score', 0)
                        documents[doc_id]['relevance_reason'] = selected.get('reason', '')

                # Save updated metadata
                with open(DOCUMENTS_JSON, 'w') as f:
                    json.dump(documents, f, indent=2)

                logger.info(f"Selected {len(selected_docs)} relevant documents")
                return selected_docs

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing selection response: {e}")
                return []

        else:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to select documents: {response.status_code}")

    except requests.RequestException as e:
        logger.error(f"Request error during document selection: {e}")
        return []
    except Exception as e:
        logger.error(f"Error selecting relevant documents: {e}")
        return []

def get_document_path(doc_id: str) -> Optional[str]:
    """Get the file path for a document by ID."""
    try:
        documents = load_documents_metadata()
        if doc_id in documents:
            return documents[doc_id].get('path')
        return None
    except Exception as e:
        logger.error(f"Error getting document path for {doc_id}: {e}")
        return None

def list_documents() -> List[Dict]:
    """List all uploaded documents with metadata."""
    try:
        documents = load_documents_metadata()
        return list(documents.values())
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return []