from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from datetime import datetime, timedelta
import asyncio
import aiohttp
import threading
from concurrent.futures import ThreadPoolExecutor
from kernel import ChatSingleton
from semantic_kernel.functions.kernel_arguments import KernelArguments
import markdown  # Added import for markdown processing

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default-dev-key")

# Configuration
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Azure Storage configuration
CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER", "chat-uploads")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to convert markdown to HTML
def convert_markdown_to_html(text):
    # Use the markdown library to convert the markdown text to HTML
    # Enable tables and other GitHub Flavored Markdown extensions
    html = markdown.markdown(text, extensions=['tables', 'fenced_code', 'codehilite'])
    return html

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Generate SAS URL for a blob
def generate_sas_url(blob_name):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        
        # Generate SAS token with read permissions for 24 hours
        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=CONTAINER_NAME,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        
        sas_url = f"{blob_client.url}?{sas_token}"
        return sas_url
    except Exception as e:
        print(f"Error generating SAS URL: {str(e)}")
        return None

# Process message with Semantic Kernel agent - synchronous wrapper
def process_message_with_agent(message, user_id=None, file_url=None):
    """
    Synchronous wrapper for processing messages with the Semantic Kernel agent.
    Uses the ChatSingleton to maintain conversation context.
    """
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Define the async processing function
        async def _process_async():
            try:
                # Get the singleton instance
                chat_singleton = await ChatSingleton.get_instance()
                kernel = chat_singleton.get_kernel()
                chat_completion = chat_singleton.get_chat_completion()
                agent = chat_singleton.get_agent()
                history = chat_singleton.get_history()
                execution_settings = chat_singleton.get_execution_settings()
                
                # Prepare the user message with file information if available
                user_message_content = message
                if file_url:
                    # Include file URL information in the message to make it available for the agent
                    user_message_content = f"{message}\n\nI've uploaded a document, the file URL is: {file_url}. Prioritize using the plugin fields."
                
                # Add user message to history
                history.add_message({"role": "user", "content": user_message_content})
                
                # Create kernel arguments to include file_url
                arguments = KernelArguments()
                if file_url:
                    # Format file_url as a dictionary with url property
                    arguments["file_url"] = {"url": file_url}
                
                # Fix for async_generator - properly consume the generator
                result_content = ""
                async for partial in agent.invoke(history):
                    result_content += partial.content if hasattr(partial, "content") else str(partial)
                
                # Add agent's initial response to history
                history.add_message({"role": "assistant", "content": result_content})

                # Get response from chat completion with arguments
                # result = await chat_completion.get_chat_message_content(
                #     chat_history=history,
                #     settings=execution_settings,
                #     kernel=kernel,
                #     arguments=arguments
                # )
                
                # Add assistant's response to history
                #history.add_message({"role": "assistant", "content": result.content})

                response = {
                    "text": f"{result_content}",
                    "timestamp": datetime.now().strftime("%H:%M")
                }
                
                return response
            except Exception as e:
                print(f"Error in _process_async: {str(e)}")
                return {
                    "text": f"I encountered an error while processing your request. Error: {str(e)}",
                    "timestamp": datetime.now().strftime("%H:%M")
                }
        
        # Run the async function in the event loop
        result = loop.run_until_complete(_process_async())
        loop.close()
        return result
        
    except Exception as e:
        print(f"Error in process_message_with_agent: {str(e)}")
        return {
            "text": f"I encountered an error while processing your request. Error: {str(e)}",
            "timestamp": datetime.now().strftime("%H:%M")
        }

@app.route('/')
def index():
    # Initialize chat history if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    return render_template('index.html', chat_history=session['chat_history'])

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form.get('message', '')
    
    if not message and 'file' not in request.files:
        return jsonify({'error': 'No message or file provided'}), 400
    
    file_url = None
    
    # Handle file upload if present
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            # Secure the filename and generate a unique name
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Save locally first
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Upload to Azure Blob Storage
            if CONNECTION_STRING:
                try:
                    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
                    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=unique_filename)
                    
                    with open(file_path, "rb") as data:
                        blob_client.upload_blob(data)
                    
                    # Generate SAS URL for the uploaded blob
                    file_url = generate_sas_url(unique_filename)
                except Exception as e:
                    print(f"Error uploading to Azure Storage: {str(e)}")
            
    # Process the message with the agent
    user_message = {
        "sender": "user",
        "text": message,
        "timestamp": datetime.now().strftime("%H:%M"),
        "file_url": file_url
    }
    
    # Add user message to chat history
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append(user_message)
    
    # Get user_id from session for conversation tracking
    user_id = session.get('user_id', None)
    
    # Process the message with the agent - use the synchronous wrapper directly
    agent_response = process_message_with_agent(message, user_id, file_url)
    
    # Convert markdown to HTML for the agent's response
    html_content = convert_markdown_to_html(agent_response["text"])
    
    agent_message = {
        "sender": "agent",
        "text": html_content,  # Now using the HTML-converted content
        "timestamp": agent_response["timestamp"]
    }
    
    # Add agent response to chat history
    session['chat_history'].append(agent_message)
    session.modified = True
    
    return jsonify({
        'user_message': user_message,
        'agent_response': agent_message
    })

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    
    # Clear the chat history in the singleton as well
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def clear_singleton_history():
        chat_singleton = await ChatSingleton.get_instance()
        chat_singleton.clear_history()
    
    loop.run_until_complete(clear_singleton_history())
    loop.close()
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)