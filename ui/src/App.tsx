import React, { useState } from 'react';
import { runAgentTask } from './services/agentService';
import type { AgentResponse, CSVData } from './types';

// Component Definitions
const Header: React.FC = () => (
    <header className="mb-10 text-center">
        <div className="inline-flex items-center justify-center p-3 mb-4 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-200">
            <i className="fa-solid fa-robot text-2xl text-white"></i>
        </div>
        <h1 className="text-4xl font-bold text-slate-900 tracking-tight">Nova Agent</h1>
        <p className="mt-2 text-slate-500 font-medium">
            Planner <i className="fa-solid fa-arrow-right mx-2 text-xs opacity-50"></i> Tool Selection <i className="fa-solid fa-arrow-right mx-2 text-xs opacity-50"></i> Execution
        </p>
    </header>
);

const Chip: React.FC<{ label: string; icon: string; onClick: () => void }> = ({ label, icon, onClick }) => (
    <button
        onClick={onClick}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-full text-sm font-medium text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 transition-all duration-200 active:scale-95 shadow-sm"
    >
        <i className={`${icon} opacity-70`}></i>
        {label}
    </button>
);

const SectionTitle: React.FC<{ title: string; icon: string }> = ({ title, icon }) => (
    <h3 className="flex items-center gap-2 text-lg font-bold text-slate-800 mb-4">
        <i className={`${icon} text-indigo-500`}></i>
        {title}
    </h3>
);

const App: React.FC = () => {
    const [task, setTask] = useState('Generate summary statistics');
    const [csvData, setCsvData] = useState<CSVData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<AgentResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const presets = [
        { label: 'Summarize', icon: 'fa-solid fa-chart-simple', task: 'Generate summary statistics and key metrics for this dataset.' },
        { label: 'Check Quality', icon: 'fa-solid fa-broom', task: 'Check for missing values and data inconsistencies.' },
        { label: 'Relationships', icon: 'fa-solid fa-diagram-project', task: 'Identify correlations between the numerical columns.' },
    ];

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target?.result as string;
            const lines = text.split('\n').filter(l => l.trim() !== '');
            const headers = lines[0]?.split(',') || [];
            const rows = lines.slice(1, 6).map(line => line.split(','));
            setCsvData({ headers, rows, rawContent: text });
        };
        reader.readAsText(file);
    };

    const executeAgent = async () => {
        if (!task.trim()) return;
        setIsLoading(true);
        setError(null);
        setResponse(null);

        try {
            const result = await runAgentTask(task, csvData?.rawContent);
            setResponse(result);
        } catch (err: any) {
            // Surface the real error message so the UI shows useful debugging info
            console.error('Error running agent:', err);
            setError(err?.message ? String(err.message) : 'Failed to execute agent. Check your API key or connection.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
            <Header />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Input Column */}
                <div className="lg:col-span-5 space-y-6">
                    <div className="glass-card p-6 rounded-3xl shadow-xl shadow-slate-200/50">
                        <SectionTitle title="Task Configuration" icon="fa-solid fa-sliders" />

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">User Intent</label>
                                <textarea
                                    value={task}
                                    onChange={(e) => setTask(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none text-slate-700 min-h-[120px] resize-none"
                                    placeholder="Describe what the agent should do..."
                                />
                            </div>

                            <div className="flex flex-wrap gap-2">
                                {presets.map((p) => (
                                    <Chip key={p.label} label={p.label} icon={p.icon} onClick={() => setTask(p.task)} />
                                ))}
                            </div>

                            <div className="pt-4 border-t border-slate-100">
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Context Source</label>
                                <div className="relative">
                                    <input
                                        type="file"
                                        accept=".csv"
                                        onChange={handleFileUpload}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                    />
                                    <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-slate-600 hover:bg-slate-100 transition-colors">
                                        <i className="fa-solid fa-file-csv text-xl text-indigo-400"></i>
                                        <span className="text-sm font-medium truncate">
                      {csvData ? `Selected: ${csvData.headers.length} columns` : 'Upload CSV data (Optional)'}
                    </span>
                                    </div>
                                </div>
                            </div>

                            {csvData && (
                                <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
                                    <table className="min-w-full divide-y divide-slate-200 text-xs">
                                        <thead className="bg-slate-50">
                                        <tr>
                                            {csvData.headers.slice(0, 3).map((h, i) => (
                                                <th key={i} className="px-3 py-2 text-left font-semibold text-slate-600">{h}</th>
                                            ))}
                                            {csvData.headers.length > 3 && <th className="px-3 py-2 text-left font-semibold text-slate-600">...</th>}
                                        </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-slate-100">
                                        {csvData.rows.map((row, i) => (
                                            <tr key={i}>
                                                {row.slice(0, 3).map((cell, j) => (
                                                    <td key={j} className="px-3 py-2 text-slate-500 truncate max-w-[80px]">{cell}</td>
                                                ))}
                                                {row.length > 3 && <td className="px-3 py-2 text-slate-400">...</td>}
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            <button
                                onClick={executeAgent}
                                disabled={isLoading}
                                className={`w-full py-4 rounded-2xl font-bold text-white transition-all shadow-lg flex items-center justify-center gap-2 ${
                                    isLoading
                                        ? 'bg-slate-400 cursor-not-allowed'
                                        : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow-indigo-200 active:scale-[0.98]'
                                }`}
                            >
                                {isLoading ? (
                                    <>
                                        <i className="fa-solid fa-circle-notch fa-spin"></i>
                                        Running Agent...
                                    </>
                                ) : (
                                    <>
                                        <i className="fa-solid fa-bolt"></i>
                                        Run Agent Nova
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Output Column */}
                <div className="lg:col-span-7 space-y-6">
                    {!response && !isLoading && !error && (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center bg-slate-100/50 rounded-3xl border-2 border-dashed border-slate-200">
                            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-sm mb-4">
                                <i className="fa-solid fa-terminal text-3xl text-slate-300"></i>
                            </div>
                            <h4 className="text-xl font-bold text-slate-400">Awaiting Commands</h4>
                            <p className="text-slate-400 mt-2 max-w-xs mx-auto">Configure your task and click "Run Agent" to see the magic happen.</p>
                        </div>
                    )}

                    {error && (
                        <div className="p-6 bg-red-50 border border-red-100 rounded-3xl flex items-start gap-4 animate-in fade-in slide-in-from-bottom-4">
                            <i className="fa-solid fa-circle-exclamation text-red-500 mt-1"></i>
                            <div>
                                <h4 className="font-bold text-red-800">Execution Error</h4>
                                <p className="text-red-600 text-sm">{error}</p>
                            </div>
                        </div>
                    )}

                    {(response || isLoading) && (
                        <div className="space-y-6">
                            {/* Plan Card */}
                            <div className="glass-card p-6 rounded-3xl shadow-xl shadow-slate-200/50">
                                <SectionTitle title="Reasoning & Planning" icon="fa-solid fa-brain" />
                                <div className="space-y-3">
                                    {isLoading ? (
                                        [1, 2, 3].map(i => (
                                            <div key={i} className="h-4 bg-slate-100 rounded-full w-full animate-pulse"></div>
                                        ))
                                    ) : (
                                        response?.plan.map((step, idx) => (
                                            <div key={idx} className="flex gap-4 items-start group">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-50 text-indigo-500 text-[10px] font-bold flex items-center justify-center border border-indigo-100">
                          {idx + 1}
                        </span>
                                                <p className="text-slate-600 text-sm leading-relaxed group-hover:text-slate-900 transition-colors">
                                                    {step}
                                                </p>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Tool Calls Card */}
                            <div className="glass-card p-6 rounded-3xl shadow-xl shadow-slate-200/50">
                                <SectionTitle title="Tool Orchestration" icon="fa-solid fa-screwdriver-wrench" />
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {isLoading ? (
                                        [1, 2].map(i => (
                                            <div key={i} className="h-12 bg-slate-100 rounded-2xl w-full animate-pulse"></div>
                                        ))
                                    ) : (
                                        response?.tool_calls.map((tool, idx) => (
                                            <div key={idx} className="p-3 bg-slate-50 border border-slate-100 rounded-2xl flex items-center justify-between">
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <div className={`p-2 rounded-lg ${tool.status === 'success' ? 'bg-green-100 text-green-600' : 'bg-orange-100 text-orange-600'}`}>
                                                        <i className={`fa-solid ${tool.status === 'success' ? 'fa-check' : 'fa-gear fa-spin'}`}></i>
                                                    </div>
                                                    <div className="min-w-0">
                                                        <h5 className="text-xs font-bold text-slate-700 truncate">{tool.tool_name}</h5>
                                                        <p className="text-[10px] text-slate-400 truncate">{tool.reason || 'Executing...'}</p>
                                                    </div>
                                                </div>
                                                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-tighter">API V1</span>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Result Card */}
                            <div className="bg-slate-900 p-8 rounded-[2rem] shadow-2xl relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4 opacity-10">
                                    <i className="fa-solid fa-quote-right text-6xl text-white"></i>
                                </div>
                                <SectionTitle title="Final Output" icon="fa-solid fa-square-poll-vertical text-white" />
                                <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-mono">
                                    {isLoading ? (
                                        <div className="flex flex-col gap-2">
                                            <div className="h-3 bg-slate-800 rounded w-3/4 animate-pulse"></div>
                                            <div className="h-3 bg-slate-800 rounded w-1/2 animate-pulse"></div>
                                            <div className="h-3 bg-slate-800 rounded w-2/3 animate-pulse"></div>
                                        </div>
                                    ) : (
                                        // Render missing-values report as a table if detected
                                        (() => {
                                            const text = response?.result || '';
                                            if (!text) return 'No result returned.';

                                            const trimmed = text.trim();
                                            // Handle two possible missing-values formats emitted by the backend
                                            // 1) Old: starts with 'Missing values per column:' followed by an ASCII table
                                            // 2) New: starts with 'Missing Values Summary' followed by stats and a whitespace-separated table
                                            const isPerColumn = trimmed.toLowerCase().startsWith('missing values per column');
                                            const isSummary = trimmed.toLowerCase().startsWith('missing values summary');
                                            if (isPerColumn) {
                                                // Parse lines, remove empty lines
                                                const lines = trimmed.split('\n').map(l => l.replace(/\r/g, '').trim()).filter(l => l.length > 0);
                                                // remove title line
                                                lines.shift();
                                                if (lines.length === 0) return text;

                                                // If there's a separator line of dashes, remove it
                                                if (lines.length > 0 && /^[-\s|]+$/.test(lines[0])) {
                                                    lines.shift();
                                                }

                                                // Header is first line
                                                const headerLine = lines.shift() || '';

                                                // Helper to split a line into cells: prefer pipe separators, otherwise split by 2+ spaces
                                                const splitLine = (ln: string) => {
                                                    if (ln.includes('|')) {
                                                        return ln.split('|').map(p => p.trim()).filter(p => p.length > 0);
                                                    }
                                                    return ln.split(/\s{2,}/).map(p => p.trim()).filter(p => p.length > 0);
                                                };

                                                const headers = splitLine(headerLine);
                                                const rows = lines.map(l => splitLine(l));

                                                return (
                                                    <div>
                                                        <h4 className="text-lg font-bold mb-3">Missing values</h4>
                                                        <div style={{ overflow: 'auto' }}>
                                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                                <thead>
                                                                    <tr>
                                                                        {headers.map((h, i) => (
                                                                            <th key={i} style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>{h}</th>
                                                                        ))}
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    {rows.map((r, ri) => (
                                                                        <tr key={ri}>
                                                                            {r.map((c, ci) => (
                                                                                <td key={ci} style={{ padding: 8, borderBottom: '1px solid #e5e7eb' }}>{c}</td>
                                                                            ))}
                                                                        </tr>
                                                                    ))}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </div>
                                                );
                                            }
                                            // New summary format handling
                                            if (isSummary) {
                                                // Split into lines and trim
                                                const allLines = trimmed.split('\n').map(l => l.replace(/\r/g, '').trim()).filter(l => l.length > 0);
                                                // Find the line index where the table header starts (line that begins with 'column')
                                                let tableHeaderIndex = allLines.findIndex(l => /^column\b/i.test(l));
                                                // If not found, fallback to showing text
                                                if (tableHeaderIndex === -1) {
                                                    return text;
                                                }

                                                // Extract summary key-values before the table (e.g., rows, cols, total missing cells)
                                                const summaryLines = allLines.slice(0, tableHeaderIndex);
                                                const stats: Record<string,string> = {};
                                                summaryLines.forEach(line => {
                                                    // lines like '- rows: 3' or 'Missing Values Summary' -> skip title
                                                    const m = line.match(/-?\s*([a-zA-Z ]+):\s*(\d+)/);
                                                    if (m) stats[m[1].trim()] = m[2];
                                                });

                                                // Table lines
                                                const tableLines = allLines.slice(tableHeaderIndex);
                                                // Header line
                                                const headerLine = tableLines.shift() || '';
                                                // Rows are remaining lines; split by whitespace groups
                                                const splitWS = (ln: string) => ln.split(/\s{2,}/).map(p => p.trim()).filter(p => p.length > 0);
                                                const headers = splitWS(headerLine);
                                                const rows = tableLines.map(l => splitWS(l));

                                                return (
                                                    <div>
                                                        <h4 className="text-lg font-bold mb-3">Missing values</h4>
                                                        <div className="text-sm text-slate-400 mb-3">
                                                            {Object.keys(stats).map(k => (
                                                                <div key={k}><strong>{k}:</strong> {stats[k]}</div>
                                                            ))}
                                                        </div>
                                                        <div style={{ overflow: 'auto' }}>
                                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                                <thead>
                                                                    <tr>
                                                                        {headers.map((h, i) => (
                                                                            <th key={i} style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>{h}</th>
                                                                        ))}
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    {rows.map((r, ri) => (
                                                                        <tr key={ri}>
                                                                            {r.map((c, ci) => (
                                                                                <td key={ci} style={{ padding: 8, borderBottom: '1px solid #e5e7eb' }}>{c}</td>
                                                                            ))}
                                                                        </tr>
                                                                    ))}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </div>
                                                );
                                            }

                                            // Default: show plain text
                                            return text;
                                        })()
                                     )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <footer className="mt-20 py-8 border-t border-slate-200 text-center text-slate-400 text-sm">
                <p className="font-medium">Nova Agent Framework &copy; 2024</p>
                <p className="text-xs mt-1 opacity-60">Leveraging Advanced Reasoning Models for Structured Execution</p>
            </footer>
        </div>
    );
};

export default App;
