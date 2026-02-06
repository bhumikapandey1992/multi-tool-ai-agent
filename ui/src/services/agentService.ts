import type { AgentResponse } from "../types";

export const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';

export async function runAgentTask(task: string, csvData?: string): Promise<AgentResponse> {
    const url = API_BASE + '/run';

    const form = new FormData();
    form.append('task', task);

    if (csvData) {
        // Attach CSV data as a Blob so backend receives UploadFile
        const blob = new Blob([csvData], { type: 'text/csv' });
        form.append('file', blob, 'data.csv');
    }

    // Use AbortController to avoid hanging requests
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    try {
        const resp = await fetch(url, { method: 'POST', body: form, signal: controller.signal });
        clearTimeout(timeout);

        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(`Backend error ${resp.status}: ${text}`);
        }

        const json = await resp.json();
        return json as AgentResponse;
    } catch (err: any) {
        if (err.name === 'AbortError') {
            throw new Error(`Request to ${url} timed out after 15s`);
        }
        // Network-level errors (e.g., connection refused) surface here
        throw new Error(`Network error when contacting ${url}: ${err?.message || String(err)}`);
    }
}
