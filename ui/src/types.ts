
export interface ToolCall {
    tool_name: string;
    status: 'pending' | 'success' | 'error';
    reason?: string;
    error?: string;
}

export interface AgentResponse {
    plan: string[];
    tool_calls: ToolCall[];
    result: string;
}

export interface CSVData {
    headers: string[];
    rows: string[][];
    rawContent: string;
}
