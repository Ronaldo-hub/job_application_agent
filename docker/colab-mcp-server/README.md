# Google Colab MCP Server

This MCP (Model Context Protocol) server enables executing resource-intensive calculations in Google Colab through a standardized interface. It provides tools for uploading code, running calculations, retrieving results, and managing authentication.

## Features

- **upload_code**: Upload Python code or Jupyter notebooks to Google Colab
- **run_calculation**: Execute uploaded code in Colab environment
- **get_results**: Retrieve computation results
- **authenticate**: Set up and validate Google Drive authentication
- **list_tasks**: List current and recent tasks

## Environment Variables

The following environment variables are required:

```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token
DRIVE_FOLDER_ID=your_drive_folder_id
COLAB_TIMEOUT_MINUTES=30
```

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Create OAuth 2.0 credentials (Client ID and Client Secret)
5. Configure the OAuth consent screen

### 2. Obtain Refresh Token

You'll need to obtain a refresh token for non-interactive authentication:

1. Use the Google OAuth Playground or create a simple script to get the refresh token
2. The refresh token allows the server to authenticate without user interaction

### 3. Google Drive Setup

1. Create a folder in Google Drive (e.g., "JobAgent")
2. Get the folder ID from the URL
3. Share the folder with the service account if using one

## Docker Deployment

### Build the Container

```bash
cd docker/colab-mcp-server
docker build -t colab-mcp-server .
```

### Run with Docker Compose

The server is integrated into the main docker-compose.yml file:

```bash
docker-compose up colab-mcp-server
```

### Run Standalone

```bash
docker run -p 3000:3000 \
  -e GOOGLE_CLIENT_ID=your_client_id \
  -e GOOGLE_CLIENT_SECRET=your_client_secret \
  -e GOOGLE_REFRESH_TOKEN=your_refresh_token \
  -e DRIVE_FOLDER_ID=your_folder_id \
  colab-mcp-server
```

## API Endpoints

The server provides both MCP stdio interface and HTTP REST API:

### HTTP API

- `POST /tools/upload_code` - Upload code for execution
- `POST /tools/run_calculation` - Start code execution
- `POST /tools/get_results` - Retrieve execution results
- `POST /tools/authenticate` - Test authentication
- `POST /tools/list_tasks` - List tasks
- `GET /health` - Health check

### MCP Tools

The server implements MCP tools that can be called through the stdio interface:

#### upload_code
```json
{
  "code": "print('Hello, Colab!')",
  "filename": "hello.py",
  "requirements": ["numpy", "pandas"]
}
```

#### run_calculation
```json
{
  "task_id": "task_123456",
  "execution_params": {"param1": "value1"}
}
```

#### get_results
```json
{
  "task_id": "task_123456",
  "result_format": "json"
}
```

## Integration with Colab Processor

The MCP server communicates with the existing `colab_processor.py` through Google Drive files:

1. MCP server uploads task files to Drive
2. Colab processor monitors Drive for new tasks
3. Colab processor executes tasks and saves results
4. MCP server retrieves results from Drive

## Security Considerations

- Store refresh tokens securely (never in code)
- Use environment variables for all credentials
- Implement proper access controls on Google Drive folders
- Regularly rotate refresh tokens
- Monitor API usage and costs

## Error Handling

The server includes comprehensive error handling:

- Authentication failures
- Network timeouts
- Code execution errors
- File upload/download issues
- Invalid task parameters

## Monitoring

- Health check endpoint at `/health`
- Structured logging for all operations
- Task status tracking
- Execution time monitoring

## Development

### Local Development

```bash
cd docker/colab-mcp-server
npm install
npm run dev
```

### Testing

```bash
# Build and test
npm run build
npm start
```

## Architecture

The server follows the architecture outlined in `colab_mcp_architecture.md`:

- MCP server container communicates with Google Drive
- Colab processor runs in Google Colab environment
- Results are exchanged through Drive files
- Authentication uses OAuth 2.0 refresh tokens

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify refresh token is valid and not expired
2. **Drive API Errors**: Check folder permissions and API quotas
3. **Timeout Issues**: Adjust `COLAB_TIMEOUT_MINUTES` for long-running tasks
4. **Network Issues**: Ensure stable internet connection for API calls

### Logs

Check container logs for detailed error information:

```bash
docker logs job_agent_colab_mcp
```

## Contributing

1. Follow TypeScript best practices
2. Add comprehensive error handling
3. Update documentation for new features
4. Test with both HTTP API and MCP stdio interface