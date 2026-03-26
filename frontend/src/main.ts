import Graph from 'graphology';
import Sigma from 'sigma';

const container = document.getElementById('sigma-container') as HTMLElement;
let sigmaInstance: Sigma | null = null;
let graph = new Graph();

const pollingInterval = 3000;
let pollingTimer: NodeJS.Timeout | null = null;
const statusEl = document.getElementById('status') as HTMLElement;

// Main initializer
async function initSigma() {
    sigmaInstance = new Sigma(graph, container, {
        allowInvalidContainer: true,
        labelFont: 'Inter',
        labelWeight: '500',
        labelSize: 12,
        labelColor: { color: '#ffffff' }
    });
    
    // Initial fetch
    await fetchGraph();
}

async function fetchGraph() {
    try {
        const response = await fetch('/graph');
        const data = await response.json();
        
        graph.clear();
        
        if (data.nodes && data.nodes.length > 0) {
            data.nodes.forEach((n: any) => {
                // Determine colors based on equivalence fusion
                let color = "#3b82f6"; // Base blue
                if (n.colors && n.colors.length > 1) {
                    color = "#ec4899"; // Fused pink
                }
                
                // Bounded Poincare mapping expands from [-1, 1] to [-100, 100] coordinates
                const x = n.poincare_coord ? n.poincare_coord[0] * 100 : Math.random() * 100;
                const y = n.poincare_coord ? n.poincare_coord[1] * 100 : Math.random() * 100;
                
                graph.addNode(n.id, {
                    x: x,
                    y: y,
                    size: n.colors && n.colors.length > 1 ? 15 : 8,
                    label: n.label,
                    color: color
                });
            });
            
            data.links.forEach((l: any) => {
                try {
                    graph.addEdge(l.source, l.target, { type: 'curve', label: l.label, color: '#555', size: 1.5 });
                } catch(e) {}
            });
                        
            statusEl.innerText = `Graph loaded: \n${graph.order} Nodes, ${graph.size} Edges.`;
        } else {
            statusEl.innerText = "Graph is empty.";
        }
    } catch (e) {
        console.error("Fetch graph failed:", e);
    }
}

// Upload listener
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-upload') as HTMLInputElement;

// Progress DOM
const progressContainer = document.getElementById('progress-container') as HTMLElement;
const progressBar = document.getElementById('progress-bar') as HTMLElement;
const progressText = document.getElementById('progress-text') as HTMLElement;

uploadBtn?.addEventListener('click', async () => {
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file first.");
        return;
    }
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    statusEl.innerText = `Upload started: ${file.name}`;
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            startPolling();
        } else {
            statusEl.innerText = "Server rejected upload.";
        }
    } catch (e) {
        statusEl.innerText = `Upload Error: ${e}`;
    }
});

function startPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    
    // Reset visuals
    progressContainer.style.display = 'block';
    progressText.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.style.backgroundColor = '#ec4899';
    progressText.innerText = '0%';
    
    pollingTimer = setInterval(async () => {
        await fetchGraph();
        await fetchStatus();
    }, pollingInterval);
}

async function fetchStatus() {
    try {
        const response = await fetch('/status');
        const data = await response.json();
        
        if (data.is_processing) {
            statusEl.innerText = `${data.step} (${data.filename})`;
            if (data.total_chunks > 0) {
                const perc = Math.round((data.current_chunk / data.total_chunks) * 100);
                progressBar.style.width = `${perc}%`;
                progressBar.style.backgroundColor = '#3b82f6'; // Switch to blue processing
                progressText.innerText = `${data.current_chunk} / ${data.total_chunks} chunks [${perc}%]`;
            }
        } else {
            if (data.step === "Complete") {
                statusEl.innerText = `Idle: Pushed ${data.filename}.`;
                progressBar.style.width = '100%';
                progressBar.style.backgroundColor = '#10b981'; // Switch to green success
                progressText.innerText = '100% (Complete)';
            } else if (data.step && data.step.startsWith("Error")) {
                statusEl.innerText = `System Failed: ${data.step}`;
                progressBar.style.backgroundColor = '#ef4444'; // Red fail
            }
        }
    } catch(e) {
        console.error("Fetch status failed:", e);
    }
}

// Boot
initSigma();
