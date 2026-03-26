import Graph from 'graphology';
import Sigma from 'sigma';
import EdgeCurveProgram from 'sigma/rendering/webgl/programs/edge.curve';

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
        defaultEdgeType: 'curve',
        edgeProgramClasses: {
            curve: EdgeCurveProgram,
        },
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
        const response = await fetch('http://localhost:8000/graph');
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
        const response = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            statusEl.innerText = `File queued: ${file.name}. Polling for Pushout.`;
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
    pollingTimer = setInterval(async () => {
        await fetchGraph();
        // If we notice new nodes or it's been active for 30 seconds we can stop, or just keep polling.
        // For simplicity, we just keep polling in this localized asynchronous client
    }, pollingInterval);
}

// Boot
initSigma();
