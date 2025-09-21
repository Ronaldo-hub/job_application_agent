#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";
import { google } from 'googleapis';
// Environment variables
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const GOOGLE_REFRESH_TOKEN = process.env.GOOGLE_REFRESH_TOKEN;
const DRIVE_FOLDER_ID = process.env.DRIVE_FOLDER_ID || 'root';
const COLAB_TIMEOUT_MINUTES = parseInt(process.env.COLAB_TIMEOUT_MINUTES || '30');
// Validate required environment variables
if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET || !GOOGLE_REFRESH_TOKEN) {
    throw new Error('Missing required Google API credentials. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN environment variables.');
}
// Google Drive API setup
const oauth2Client = new google.auth.OAuth2(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, 'urn:ietf:wg:oauth:2.0:oob' // For non-interactive flows
);
oauth2Client.setCredentials({
    refresh_token: GOOGLE_REFRESH_TOKEN
});
const drive = google.drive({ version: 'v3', auth: oauth2Client });
class ColabMcpServer {
    tasks = new Map();
    driveService;
    constructor() {
        this.driveService = drive;
    }
    async initialize() {
        // Load existing tasks from Drive
        await this.loadTasksFromDrive();
    }
    async loadTasksFromDrive() {
        try {
            const response = await this.driveService.files.list({
                q: `'${DRIVE_FOLDER_ID}' in parents and name contains 'task_' and trashed=false`,
                fields: 'files(id, name, modifiedTime)',
                orderBy: 'modifiedTime desc'
            });
            for (const file of response.data.files) {
                try {
                    const content = await this.downloadFile(file.id);
                    const task = JSON.parse(content);
                    this.tasks.set(task.id, task);
                }
                catch (error) {
                    console.error(`Failed to load task ${file.name}:`, error);
                }
            }
        }
        catch (error) {
            console.error('Failed to load tasks from Drive:', error);
        }
    }
    async downloadFile(fileId) {
        const response = await this.driveService.files.get({
            fileId: fileId,
            alt: 'media'
        }, { responseType: 'text' });
        return response.data;
    }
    async uploadFile(filename, content, folderId = DRIVE_FOLDER_ID) {
        const fileMetadata = {
            name: filename,
            parents: [folderId]
        };
        const media = {
            mimeType: 'application/json',
            body: content
        };
        const response = await this.driveService.files.create({
            resource: fileMetadata,
            media: media,
            fields: 'id'
        });
        return response.data.id;
    }
    generateTaskId() {
        return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    // Tool implementations
    async uploadCode(code, filename, requirements = []) {
        const taskId = this.generateTaskId();
        const task = {
            id: taskId,
            type: 'code_execution',
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            code,
            filename,
            requirements
        };
        // Save task to Drive
        await this.uploadFile(`task_${taskId}.json`, JSON.stringify(task));
        // Upload code file
        await this.uploadFile(filename, code);
        this.tasks.set(taskId, task);
        return task;
    }
    async runCalculation(taskId, executionParams = {}) {
        const task = this.tasks.get(taskId);
        if (!task) {
            throw new Error(`Task ${taskId} not found`);
        }
        if (task.status !== 'pending') {
            throw new Error(`Task ${taskId} is not in pending status`);
        }
        // Update task status
        task.status = 'running';
        task.updated_at = new Date().toISOString();
        task.execution_params = executionParams;
        // Save updated task
        await this.uploadFile(`task_${taskId}.json`, JSON.stringify(task));
        // Create Colab task file
        const colabTask = {
            type: 'code_execution',
            task_id: taskId,
            code: task.code,
            filename: task.filename,
            requirements: task.requirements,
            execution_params: executionParams,
            timeout_minutes: COLAB_TIMEOUT_MINUTES
        };
        await this.uploadFile('colab_task.json', JSON.stringify(colabTask));
        this.tasks.set(taskId, task);
        return task;
    }
    async getResults(taskId) {
        const task = this.tasks.get(taskId);
        if (!task) {
            throw new Error(`Task ${taskId} not found`);
        }
        if (task.status === 'running') {
            // Check for results in Drive
            try {
                const response = await this.driveService.files.list({
                    q: `'${DRIVE_FOLDER_ID}' in parents and name = 'result_${taskId}.json' and trashed=false`,
                    fields: 'files(id, name)'
                });
                if (response.data.files.length > 0) {
                    const resultContent = await this.downloadFile(response.data.files[0].id);
                    const result = JSON.parse(resultContent);
                    // Update task with results
                    task.status = result.status === 'success' ? 'completed' : 'failed';
                    task.updated_at = new Date().toISOString();
                    task.result = result.result;
                    if (result.error)
                        task.error = result.error;
                    await this.uploadFile(`task_${taskId}.json`, JSON.stringify(task));
                    this.tasks.set(taskId, task);
                    return result;
                }
            }
            catch (error) {
                console.error('Error checking for results:', error);
            }
            throw new Error(`Task ${taskId} is still running`);
        }
        if (task.status === 'completed') {
            return {
                status: 'success',
                result: task.result
            };
        }
        if (task.status === 'failed') {
            throw new Error(`Task ${taskId} failed: ${task.error}`);
        }
        throw new Error(`Task ${taskId} has unknown status: ${task.status}`);
    }
    async authenticate(testConnection = false) {
        try {
            // Test Drive API connection
            const response = await this.driveService.files.list({
                pageSize: 1,
                fields: 'files(id, name)'
            });
            const result = {
                status: 'success',
                message: 'Google Drive authentication successful',
                folder_id: DRIVE_FOLDER_ID
            };
            if (testConnection) {
                result.test_results = {
                    api_accessible: true,
                    files_found: response.data.files.length
                };
            }
            return result;
        }
        catch (error) {
            throw new Error(`Authentication failed: ${error.message}`);
        }
    }
    async listTasks(statusFilter, limit = 10) {
        let tasks = Array.from(this.tasks.values());
        if (statusFilter) {
            tasks = tasks.filter(task => task.status === statusFilter);
        }
        // Sort by updated_at descending
        tasks.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        return tasks.slice(0, limit);
    }
}
// Create MCP server
const server = new Server({
    name: "colab-mcp-server",
    version: "1.0.0"
});
// Initialize Colab MCP Server
const colabServer = new ColabMcpServer();
// For now, create a simple HTTP server to handle tool calls
// This is a temporary solution until we implement proper MCP tool registration
import express from 'express';
const app = express();
app.use(express.json());
// Tool endpoints
app.post('/tools/upload_code', async (req, res) => {
    try {
        const { code, filename, requirements = [] } = req.body;
        const task = await colabServer.uploadCode(code, filename, requirements);
        res.json({ result: `Code uploaded successfully. Task ID: ${task.id}` });
    }
    catch (error) {
        res.status(500).json({ error: error.message });
    }
});
app.post('/tools/run_calculation', async (req, res) => {
    try {
        const { task_id, execution_params = {} } = req.body;
        const task = await colabServer.runCalculation(task_id, execution_params);
        res.json({ result: `Calculation started. Task ID: ${task.id}, Status: ${task.status}` });
    }
    catch (error) {
        res.status(500).json({ error: error.message });
    }
});
app.post('/tools/get_results', async (req, res) => {
    try {
        const { task_id } = req.body;
        const result = await colabServer.getResults(task_id);
        res.json({ result: `Results for task ${task_id}:\n${JSON.stringify(result, null, 2)}` });
    }
    catch (error) {
        res.status(500).json({ error: error.message });
    }
});
app.post('/tools/authenticate', async (req, res) => {
    try {
        const { test_connection = false } = req.body;
        const result = await colabServer.authenticate(test_connection);
        res.json({ result: JSON.stringify(result, null, 2) });
    }
    catch (error) {
        res.status(500).json({ error: error.message });
    }
});
app.post('/tools/list_tasks', async (req, res) => {
    try {
        const { status_filter, limit = 10 } = req.body;
        const tasks = await colabServer.listTasks(status_filter, limit);
        const taskList = tasks.map(task => ({
            id: task.id,
            type: task.type,
            status: task.status,
            created_at: task.created_at,
            filename: task.filename
        }));
        res.json({ result: `Tasks (${tasks.length}):\n${JSON.stringify(taskList, null, 2)}` });
    }
    catch (error) {
        res.status(500).json({ error: error.message });
    }
});
// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});
// Initialize and start server
async function main() {
    try {
        await colabServer.initialize();
        const PORT = process.env.PORT || 3000;
        app.listen(PORT, () => {
            console.log(`Colab MCP server running on port ${PORT}`);
        });
        // Also start MCP stdio server for compatibility
        const transport = new StdioServerTransport();
        await server.connect(transport);
        console.error('Colab MCP server running on stdio');
    }
    catch (error) {
        console.error('Failed to start Colab MCP server:', error);
        process.exit(1);
    }
}
main();
//# sourceMappingURL=index.js.map