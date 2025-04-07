// Space Station Cargo Management System - Frontend JavaScript

// Base API URL
const API_URL = 'http://localhost:8000/api';

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    
    // Show the first section by default
    sections[0].classList.add('active');
    navLinks[0].classList.add('active');
    
    // Navigation event listeners
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');
        });
    });
    
    // Placement Section
    const placementFileInput = document.getElementById('placement-file');
    const uploadPlacementButton = document.getElementById('upload-placement');
    const placementResult = document.getElementById('placement-result');
    const placementsContainer = document.getElementById('placements-container');
    const rearrangementsContainer = document.getElementById('rearrangements-container');
    const rearrangementSteps = document.getElementById('rearrangement-steps');
    
    uploadPlacementButton.addEventListener('click', async function() {
        if (!placementFileInput.files[0]) {
            alert('Please select a CSV file');
            return;
        }
        
        try {
            // First, read the CSV file and parse it
            const file = placementFileInput.files[0];
            const text = await file.text();
            const lines = text.split('\n');
            const headers = lines[0].split(',');
            
            // Parse CSV into items array
            const items = [];
            for (let i = 1; i < lines.length; i++) {
                if (!lines[i].trim()) continue; // Skip empty lines
                
                const values = lines[i].split(',');
                const item = {};
                
                for (let j = 0; j < headers.length; j++) {
                    const header = headers[j].trim();
                    const value = values[j]?.trim();
                    
                    if (header === 'id' || header === 'item_id') {
                        item.id = value;
                    } else if (header === 'name') {
                        item.name = value;
                    } else if (header === 'width' || header === 'width_cm') {
                        item.width = parseFloat(value);
                    } else if (header === 'depth' || header === 'depth_cm') {
                        item.depth = parseFloat(value);
                    } else if (header === 'height' || header === 'height_cm') {
                        item.height = parseFloat(value);
                    } else if (header === 'mass' || header === 'mass_kg') {
                        item.mass = parseFloat(value);
                    } else if (header === 'priority') {
                        item.priority = parseInt(value);
                    } else if (header === 'expiry_date') {
                        if (value && value !== 'N/A') item.expiry_date = value;
                    } else if (header === 'usage_limit') {
                        if (value && value !== 'N/A') item.usage_limit = parseInt(value);
                    }
                }
                
                items.push(item);
            }
            
            // Make API call with JSON data
            const response = await fetch(`${API_URL}/placement`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ items })
            });
            
            const data = await response.json();
            
            if (data.success) {
                placementResult.style.display = 'block';
                
                // Display placements
                if (data.placements && data.placements.length > 0) {
                    const table = createTable(['Item ID', 'Container ID', 'Position']);
                    
                    data.placements.forEach(placement => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${placement.itemId}</td>
                            <td>${placement.containerId}</td>
                            <td>Start: (${placement.position.startCoordinates.width}, ${placement.position.startCoordinates.depth}, ${placement.position.startCoordinates.height})<br>
                                End: (${placement.position.endCoordinates.width}, ${placement.position.endCoordinates.depth}, ${placement.position.endCoordinates.height})</td>
                        `;
                        table.querySelector('tbody').appendChild(row);
                    });
                    
                    placementsContainer.innerHTML = '';
                    placementsContainer.appendChild(table);
                } else {
                    placementsContainer.innerHTML = '<p>No placements made</p>';
                }
                
                // Display rearrangements if any
                if (data.rearrangements && data.rearrangements.length > 0) {
                    rearrangementsContainer.style.display = 'block';
                    
                    const list = document.createElement('ol');
                    
                    data.rearrangements.forEach(step => {
                        const item = document.createElement('li');
                        item.textContent = `${step.action} ${step.itemId} from ${step.fromContainer || 'N/A'} to ${step.toContainer || 'N/A'}`;
                        list.appendChild(item);
                    });
                    
                    rearrangementSteps.innerHTML = '';
                    rearrangementSteps.appendChild(list);
                } else {
                    rearrangementsContainer.style.display = 'none';
                }
            } else {
                alert(`Error: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    // Search and Retrieval Section
    const searchItemId = document.getElementById('search-item-id');
    const searchItemName = document.getElementById('search-item-name');
    const searchButton = document.getElementById('search-button');
    const searchResult = document.getElementById('search-result');
    const searchItemsContainer = document.getElementById('search-items-container');
    
    const retrieveItemId = document.getElementById('retrieve-item-id');
    const retrieveAstronautId = document.getElementById('retrieve-astronaut-id');
    const retrieveButton = document.getElementById('retrieve-button');
    const retrieveResult = document.getElementById('retrieve-result');
    const retrievalStepsContainer = document.getElementById('retrieval-steps-container');
    
    const placeItemId = document.getElementById('place-item-id');
    const placeAstronautId = document.getElementById('place-astronaut-id');
    const placeContainerId = document.getElementById('place-container-id');
    const placeButton = document.getElementById('place-button');
    
    searchButton.addEventListener('click', async function() {
        const itemId = searchItemId.value.trim();
        const itemName = searchItemName.value.trim();
        
        if (!itemId && !itemName) {
            alert('Please enter either Item ID or Item Name');
            return;
        }
        
        let url = `${API_URL}/search?`;
        if (itemId) {
            url += `item_id=${encodeURIComponent(itemId)}`;
        } else {
            url += `name=${encodeURIComponent(itemName)}`;
        }
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            searchResult.style.display = 'block';
            
            if (data.items && data.items.length > 0) {
                const table = createTable(['ID', 'Name', 'Container', 'Priority', 'Status']);
                
                data.items.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.id}</td>
                        <td>${item.name}</td>
                        <td>${item.container_id || 'N/A'}</td>
                        <td>${item.priority}</td>
                        <td>${item.status}</td>
                    `;
                    table.querySelector('tbody').appendChild(row);
                });
                
                searchItemsContainer.innerHTML = '';
                searchItemsContainer.appendChild(table);
            } else {
                searchItemsContainer.innerHTML = '<p>No items found</p>';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    retrieveButton.addEventListener('click', async function() {
        const itemId = retrieveItemId.value.trim();
        const astronautId = retrieveAstronautId.value.trim();
        
        if (!itemId || !astronautId) {
            alert('Please enter both Item ID and Astronaut ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/retrieve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    item_id: itemId,
                    astronaut_id: astronautId
                })
            });
            
            const data = await response.json();
            
            retrieveResult.style.display = 'block';
            
            if (data.steps && data.steps.length > 0) {
                const list = document.createElement('ol');
                
                data.steps.forEach(step => {
                    const item = document.createElement('li');
                    item.textContent = `${step.action}: ${step.item_id}`;
                    list.appendChild(item);
                });
                
                retrievalStepsContainer.innerHTML = '';
                retrievalStepsContainer.appendChild(list);
            } else {
                retrievalStepsContainer.innerHTML = '<p>No retrieval steps available</p>';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    placeButton.addEventListener('click', async function() {
        const itemId = placeItemId.value.trim();
        const astronautId = placeAstronautId.value.trim();
        const containerId = placeContainerId.value.trim();
        
        if (!itemId || !astronautId || !containerId) {
            alert('Please enter Item ID, Astronaut ID, and Container ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/place`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    item_id: itemId,
                    astronaut_id: astronautId,
                    container_id: containerId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`Item ${itemId} successfully placed in container ${containerId}`);
            } else {
                alert(`Error: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    // Waste Management Section
    const identifyWasteButton = document.getElementById('identify-waste-button');
    const wasteResult = document.getElementById('waste-result');
    const wasteItemsContainer = document.getElementById('waste-items-container');
    
    const undockingContainerId = document.getElementById('undocking-container-id');
    const maxWeight = document.getElementById('max-weight');
    const returnPlanButton = document.getElementById('return-plan-button');
    const returnPlanResult = document.getElementById('return-plan-result');
    const returnPlanContainer = document.getElementById('return-plan-container');
    const returnManifestContainer = document.getElementById('return-manifest-container');
    
    const completeUndockingButton = document.getElementById('complete-undocking-button');
    
    identifyWasteButton.addEventListener('click', async function() {
        try {
            const response = await fetch(`${API_URL}/waste/identify`);
            const data = await response.json();
            
            wasteResult.style.display = 'block';
            
            if (data.waste_items && data.waste_items.length > 0) {
                const table = createTable(['ID', 'Name', 'Reason', 'Container']);
                
                data.waste_items.forEach(item => {
                    const row = document.createElement('tr');
                    const reason = item.expiry_date && new Date(item.expiry_date) <= new Date() ? 'Expired' : 'Usage Limit Reached';
                    row.innerHTML = `
                        <td>${item.id}</td>
                        <td>${item.name}</td>
                        <td>${reason}</td>
                        <td>${item.container_id || 'N/A'}</td>
                    `;
                    table.querySelector('tbody').appendChild(row);
                });
                
                wasteItemsContainer.innerHTML = '';
                wasteItemsContainer.appendChild(table);
            } else {
                wasteItemsContainer.innerHTML = '<p>No waste items found</p>';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    returnPlanButton.addEventListener('click', async function() {
        const containerId = undockingContainerId.value.trim();
        const weight = maxWeight.value.trim();
        
        if (!containerId || !weight) {
            alert('Please enter both Undocking Container ID and Maximum Weight');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/waste/return-plan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    undocking_module_id: containerId,
                    max_weight: parseFloat(weight)
                })
            });
            
            const data = await response.json();
            
            returnPlanResult.style.display = 'block';
            
            if (data.plan && data.plan.length > 0) {
                const list = document.createElement('ol');
                
                data.plan.forEach(step => {
                    const item = document.createElement('li');
                    item.textContent = step.step;
                    list.appendChild(item);
                });
                
                returnPlanContainer.innerHTML = '';
                returnPlanContainer.appendChild(list);
                
                // Display manifest
                if (data.manifest) {
                    const manifest = document.createElement('div');
                    manifest.innerHTML = `
                        <p><strong>Total Weight:</strong> ${data.manifest.total_weight_kg} kg</p>
                        <p><strong>Items:</strong></p>
                    `;
                    
                    const table = createTable(['Item ID', 'Name', 'Mass (kg)']);
                    
                    data.manifest.items.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.item_id}</td>
                            <td>${item.name}</td>
                            <td>${item.mass_kg}</td>
                        `;
                        table.querySelector('tbody').appendChild(row);
                    });
                    
                    manifest.appendChild(table);
                    returnManifestContainer.innerHTML = '';
                    returnManifestContainer.appendChild(manifest);
                }
            } else {
                returnPlanContainer.innerHTML = '<p>No return plan available</p>';
                returnManifestContainer.innerHTML = '';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    completeUndockingButton.addEventListener('click', async function() {
        if (!confirm('Are you sure you want to complete the undocking process? This will remove all waste items.')) {
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/waste/complete-undocking`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.message) {
                alert(data.message);
                // Clear waste display
                wasteResult.style.display = 'none';
                returnPlanResult.style.display = 'none';
            } else {
                alert('Undocking completed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    // Time Simulation Section
    const currentDateElement = document.getElementById('current-date');
    const usedItemsTextarea = document.getElementById('used-items');
    const nextDayButton = document.getElementById('next-day-button');
    const daysToSimulate = document.getElementById('days-to-simulate');
    const fastForwardButton = document.getElementById('fast-forward-button');
    const simulationResult = document.getElementById('simulation-result');
    const simulationChangesContainer = document.getElementById('simulation-changes-container');
    
    // Initialize with current date
    async function getCurrentDate() {
        try {
            const response = await fetch(`${API_URL}/simulation/status`);
            const data = await response.json();
            if (data.success) {
                const dateStr = data.currentDate || data.missionDate || 'Not available';
                currentDateElement.textContent = dateStr;
            } else {
                console.error('Error in simulation status response:', data);
                currentDateElement.textContent = 'Error fetching date';
            }
        } catch (error) {
            console.error('Error fetching current date:', error);
            currentDateElement.textContent = 'Error fetching date';
        }
    }
    
    // Call getCurrentDate on page load
    getCurrentDate();
    
    nextDayButton.addEventListener('click', async function() {
        await simulateTime(1);
    });
    
    fastForwardButton.addEventListener('click', async function() {
        const days = parseInt(daysToSimulate.value) || 1;
        await simulateTime(days);
    });
    
    async function simulateTime(days) {
        let usedItems = [];
        
        try {
            usedItems = JSON.parse(usedItemsTextarea.value.trim() || '[]');
        } catch (e) {
            alert('Invalid JSON format for used items');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/simulate/day`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    days: days,
                    used_items: usedItems
                })
            });
            
            const data = await response.json();
            
            if (data.current_date) {
                currentDateElement.textContent = formatDate(data.current_date);
                
                simulationResult.style.display = 'block';
                
                let html = '<h4>Changes:</h4>';
                
                if (data.changes) {
                    if (data.changes.itemsUsed && data.changes.itemsUsed.length > 0) {
                        html += '<h5>Items Used:</h5>';
                        html += createTableHTML(data.changes.itemsUsed, ['itemId', 'name', 'uses']);
                    }
                    
                    if (data.changes.itemsExpired && data.changes.itemsExpired.length > 0) {
                        html += '<h5>Items Expired:</h5>';
                        html += createTableHTML(data.changes.itemsExpired, ['itemId', 'name']);
                    }
                    
                    if (data.changes.itemsDepletedToday && data.changes.itemsDepletedToday.length > 0) {
                        html += '<h5>Items Depleted Today:</h5>';
                        html += createTableHTML(data.changes.itemsDepletedToday, ['itemId', 'name']);
                    }
                }
                
                if (data.waste_items && data.waste_items.length > 0) {
                    html += '<h5>Waste Items:</h5>';
                    html += createTableHTML(data.waste_items, ['id', 'name', 'status']);
                }
                
                simulationChangesContainer.innerHTML = html;
            } else {
                alert('Error: No date returned from simulation');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    }
    
    // Import/Export Section
    const importItemsFile = document.getElementById('import-items-file');
    const importItemsButton = document.getElementById('import-items-button');
    const importContainersFile = document.getElementById('import-containers-file');
    const importContainersButton = document.getElementById('import-containers-button');
    const exportArrangementButton = document.getElementById('export-arrangement-button');
    const importResult = document.getElementById('import-result');
    const importResultContainer = document.getElementById('import-result-container');
    
    importItemsButton.addEventListener('click', async function() {
        if (!importItemsFile.files[0]) {
            alert('Please select a CSV file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', importItemsFile.files[0]);
        
        try {
            const response = await fetch(`${API_URL}/import/items`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            importResult.style.display = 'block';
            
            let html = `<p>Imported ${data.itemsImported || 0} items</p>`;
            
            if (data.errors && data.errors.length > 0) {
                html += '<h4>Errors:</h4>';
                html += createTableHTML(data.errors, ['row', 'message']);
            }
            
            importResultContainer.innerHTML = html;
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    importContainersButton.addEventListener('click', async function() {
        if (!importContainersFile.files[0]) {
            alert('Please select a CSV file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', importContainersFile.files[0]);
        
        try {
            const response = await fetch(`${API_URL}/import/containers`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            importResult.style.display = 'block';
            
            let html = `<p>Imported ${data.containersImported || 0} containers</p>`;
            
            if (data.errors && data.errors.length > 0) {
                html += '<h4>Errors:</h4>';
                html += createTableHTML(data.errors, ['row', 'message']);
            }
            
            importResultContainer.innerHTML = html;
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    exportArrangementButton.addEventListener('click', async function() {
        try {
            const response = await fetch(`${API_URL}/export/arrangement`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'arrangement.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    // Logs Section
    const logActionType = document.getElementById('log-action-type');
    const logAstronautId = document.getElementById('log-astronaut-id');
    const logItemId = document.getElementById('log-item-id');
    const logStartDate = document.getElementById('log-start-date');
    const logEndDate = document.getElementById('log-end-date');
    const getLogsButton = document.getElementById('get-logs-button');
    const logsResult = document.getElementById('logs-result');
    const logsContainer = document.getElementById('logs-container');
    
    getLogsButton.addEventListener('click', async function() {
        let url = `${API_URL}/logs?`;
        
        if (logActionType.value.trim()) {
            url += `action_type=${encodeURIComponent(logActionType.value.trim())}&`;
        }
        
        if (logAstronautId.value.trim()) {
            url += `astronaut_id=${encodeURIComponent(logAstronautId.value.trim())}&`;
        }
        
        if (logItemId.value.trim()) {
            url += `item_id=${encodeURIComponent(logItemId.value.trim())}&`;
        }
        
        if (logStartDate.value) {
            url += `start_date=${encodeURIComponent(logStartDate.value)}&`;
        }
        
        if (logEndDate.value) {
            url += `end_date=${encodeURIComponent(logEndDate.value)}&`;
        }
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            logsResult.style.display = 'block';
            
            if (data.logs && data.logs.length > 0) {
                const table = createTable(['Timestamp', 'Action Type', 'Astronaut ID', 'Item ID', 'Details']);
                
                data.logs.forEach(log => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${formatDate(log.timestamp)}</td>
                        <td>${log.action_type}</td>
                        <td>${log.astronaut_id || 'N/A'}</td>
                        <td>${log.item_id || 'N/A'}</td>
                        <td>${formatDetails(log.details)}</td>
                    `;
                    table.querySelector('tbody').appendChild(row);
                });
                
                logsContainer.innerHTML = '';
                logsContainer.appendChild(table);
            } else {
                logsContainer.innerHTML = '<p>No logs found</p>';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the request');
        }
    });
    
    // Guided Flow Demonstration
    // Step 1: Initialize Empty Containers
    const initContainersFile = document.getElementById('init-containers-file');
    const initContainersButton = document.getElementById('init-containers-button');
    const initContainersResult = document.getElementById('init-containers-result');
    
    initContainersButton.addEventListener('click', async function() {
        if (!initContainersFile.files[0]) {
            alert('Please select the sample_containers.csv file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', initContainersFile.files[0]);
        
        try {
            const response = await fetch(`${API_URL}/import/containers`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                initContainersResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Successfully imported ${data.containersImported} containers!</p>
                    </div>
                `;
            } else {
                initContainersResult.innerHTML = `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to import containers'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            initContainersResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    // Step 2: Resupply Mission
    const resupplyItemsFile = document.getElementById('resupply-items-file');
    const importResupplyItemsButton = document.getElementById('import-resupply-items-button');
    const placeResupplyItemsButton = document.getElementById('place-resupply-items-button');
    const resupplyResult = document.getElementById('resupply-result');
    
    importResupplyItemsButton.addEventListener('click', async function() {
        if (!resupplyItemsFile.files[0]) {
            alert('Please select the sample_items.csv file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', resupplyItemsFile.files[0]);
        
        try {
            const response = await fetch(`${API_URL}/import/items`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                resupplyResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Successfully imported ${data.itemsImported} items!</p>
                    </div>
                `;
            } else {
                resupplyResult.innerHTML = `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to import items'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            resupplyResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    placeResupplyItemsButton.addEventListener('click', async function() {
        try {
            // Fetch all items
            const itemsResponse = await fetch(`${API_URL}/search`);
            const itemsData = await itemsResponse.json();
            
            // Fetch all containers
            const containersResponse = await fetch(`${API_URL}/containers`);
            const containersData = await containersResponse.json();
            
            if (!itemsData.items || !containersData.containers) {
                resupplyResult.innerHTML += `
                    <div class="alert alert-danger">
                        <p>Error: Could not fetch items or containers</p>
                    </div>
                `;
                return;
            }
            
            // Prepare placement request
            const placementRequest = {
                items: itemsData.items,
                containers: containersData.containers
            };
            
            // Call placement API
            const placementResponse = await fetch(`${API_URL}/placement`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(placementRequest)
            });
            
            const placementData = await placementResponse.json();
            
            if (placementData.success) {
                resupplyResult.innerHTML += `
                    <div class="alert alert-success">
                        <p>Successfully placed items in containers!</p>
                    </div>
                    <h4>Placement Results:</h4>
                    ${createTableHTML(placementData.placements, ['itemId', 'containerId', 'position'])}
                `;
            } else {
                resupplyResult.innerHTML += `
                    <div class="alert alert-danger">
                        <p>Error: ${placementData.message || 'Failed to place items'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            resupplyResult.innerHTML += `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    // Step 3: Astronaut Usage
    const usageItemId = document.getElementById('usage-item-id');
    const usageAstronautId = document.getElementById('usage-astronaut-id');
    const usageContainerId = document.getElementById('usage-container-id');
    const searchUsageButton = document.getElementById('search-usage-button');
    const retrieveUsageButton = document.getElementById('retrieve-usage-button');
    const placeUsageButton = document.getElementById('place-usage-button');
    const usageResult = document.getElementById('usage-result');
    
    searchUsageButton.addEventListener('click', async function() {
        const itemId = usageItemId.value.trim();
        
        if (!itemId) {
            alert('Please enter an Item ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/search?item_id=${encodeURIComponent(itemId)}`);
            const data = await response.json();
            
            if (data.found) {
                usageResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Item found!</p>
                    </div>
                    <h4>Item Details:</h4>
                    ${createTableHTML([data.item], ['itemId', 'name', 'containerId', 'position', 'priority', 'status'])}
                `;
            } else {
                usageResult.innerHTML = `
                    <div class="alert alert-warning">
                        <p>Item not found</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            usageResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    retrieveUsageButton.addEventListener('click', async function() {
        const itemId = usageItemId.value.trim();
        const astronautId = usageAstronautId.value.trim();
        
        if (!itemId || !astronautId) {
            alert('Please enter both Item ID and Astronaut ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/retrieve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    itemId: itemId,
                    userId: astronautId,
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                usageResult.innerHTML += `
                    <div class="alert alert-success">
                        <p>Item retrieved successfully!</p>
                    </div>
                    <h4>Retrieval Steps:</h4>
                    <ol>
                        ${data.retrievalSteps.map(step => `<li>${step}</li>`).join('')}
                    </ol>
                `;
            } else {
                usageResult.innerHTML += `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to retrieve item'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            usageResult.innerHTML += `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    placeUsageButton.addEventListener('click', async function() {
        const itemId = usageItemId.value.trim();
        const astronautId = usageAstronautId.value.trim();
        const containerId = usageContainerId.value.trim();
        
        if (!itemId || !astronautId || !containerId) {
            alert('Please enter Item ID, Astronaut ID, and Container ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/place`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    itemId: itemId,
                    userId: astronautId,
                    containerId: containerId,
                    timestamp: new Date().toISOString(),
                    position: {
                        startCoordinates: { width: 0, depth: 0, height: 0 },
                        endCoordinates: { width: 10, depth: 10, height: 10 }
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                usageResult.innerHTML += `
                    <div class="alert alert-success">
                        <p>Item placed successfully!</p>
                    </div>
                `;
            } else {
                usageResult.innerHTML += `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to place item'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            usageResult.innerHTML += `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    // Step 4: Waste Management & Time Simulation
    const flowCurrentDate = document.getElementById('flow-current-date');
    const flowUsedItems = document.getElementById('flow-used-items');
    const flowDays = document.getElementById('flow-days');
    const flowSimulateDayButton = document.getElementById('flow-simulate-day-button');
    const flowFastForwardButton = document.getElementById('flow-fast-forward-button');
    const flowIdentifyWasteButton = document.getElementById('flow-identify-waste-button');
    const flowUndockingContainer = document.getElementById('flow-undocking-container');
    const flowMaxWeight = document.getElementById('flow-max-weight');
    const flowPlanReturnButton = document.getElementById('flow-plan-return-button');
    const flowCompleteUndockingButton = document.getElementById('flow-complete-undocking-button');
    const flowWasteResult = document.getElementById('flow-waste-result');
    
    // Get current date
    async function getCurrentDate() {
        try {
            const response = await fetch(`${API_URL}/simulation/status`);
            const data = await response.json();
            if (data.success) {
                const dateStr = data.currentDate || data.missionDate || 'Not available';
                flowCurrentDate.textContent = dateStr;
                document.getElementById('current-date').textContent = dateStr;
            } else {
                console.error('Error in simulation status response:', data);
                flowCurrentDate.textContent = 'Error fetching date';
            }
        } catch (error) {
            console.error('Error fetching current date:', error);
            flowCurrentDate.textContent = 'Error fetching date';
        }
    }
    
    // Call getCurrentDate on page load
    getCurrentDate();
    
    flowSimulateDayButton.addEventListener('click', async function() {
        let usedItemsArray = [];
        
        try {
            usedItemsArray = JSON.parse(flowUsedItems.value);
        } catch (error) {
            alert('Invalid JSON format for used items');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/simulate/day`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    numOfDays: 1,
                    itemsToBeUsedPerDay: usedItemsArray
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                flowCurrentDate.textContent = data.newDate;
                document.getElementById('current-date').textContent = data.newDate;
                
                flowWasteResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Successfully simulated a day!</p>
                    </div>
                    <h4>Items Used:</h4>
                    ${createTableHTML(data.changes.itemsUsed || [], ['itemId', 'name', 'remainingUses'])}
                    <h4>Items Expired:</h4>
                    ${createTableHTML(data.changes.itemsExpired || [], ['itemId', 'name', 'reason'])}
                `;
            } else {
                flowWasteResult.innerHTML = `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to simulate day'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            flowWasteResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    flowFastForwardButton.addEventListener('click', async function() {
        const days = parseInt(flowDays.value) || 1;
        
        try {
            const response = await fetch(`${API_URL}/simulate/day`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    numOfDays: days
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                flowCurrentDate.textContent = data.newDate;
                document.getElementById('current-date').textContent = data.newDate;
                
                flowWasteResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Successfully fast-forwarded ${days} days!</p>
                    </div>
                    <h4>Items Expired:</h4>
                    ${createTableHTML(data.changes.itemsExpired || [], ['itemId', 'name', 'reason'])}
                `;
            } else {
                flowWasteResult.innerHTML = `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to fast-forward'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            flowWasteResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    flowIdentifyWasteButton.addEventListener('click', async function() {
        try {
            const response = await fetch(`${API_URL}/waste/identify`);
            const data = await response.json();
            
            if (data.success) {
                flowWasteResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Successfully identified waste items!</p>
                    </div>
                    <h4>Waste Items:</h4>
                    ${createTableHTML(data.wasteItems || [], ['itemId', 'name', 'reason'])}
                `;
            } else {
                flowWasteResult.innerHTML = `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to identify waste'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            flowWasteResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    flowPlanReturnButton.addEventListener('click', async function() {
        const containerId = flowUndockingContainer.value.trim();
        const maxWeight = parseFloat(flowMaxWeight.value) || 50;
        
        if (!containerId) {
            alert('Please enter an Undocking Container ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/waste/return-plan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    undockingContainerId: containerId,
                    undockingDate: new Date(flowCurrentDate.textContent).toISOString(),
                    maxWeight: maxWeight
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                flowWasteResult.innerHTML += `
                    <div class="alert alert-success">
                        <p>Successfully created return plan!</p>
                    </div>
                    <h4>Return Plan:</h4>
                    <ol>
                        ${data.returnPlan.map(item => `<li>Move ${item.itemId} to ${item.toContainer}</li>`).join('')}
                    </ol>
                    <h4>Retrieval Steps:</h4>
                    <ol>
                        ${data.retrievalSteps.map(step => `<li>${step}</li>`).join('')}
                    </ol>
                `;
            } else {
                flowWasteResult.innerHTML += `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to create return plan'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            flowWasteResult.innerHTML += `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    flowCompleteUndockingButton.addEventListener('click', async function() {
        const containerId = flowUndockingContainer.value.trim();
        
        if (!containerId) {
            alert('Please enter an Undocking Container ID');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/waste/complete-undocking`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    undockingContainerId: containerId,
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                flowWasteResult.innerHTML += `
                    <div class="alert alert-success">
                        <p>Successfully completed undocking!</p>
                    </div>
                    <p>Removed ${data.itemsRemoved} items from the system.</p>
                `;
            } else {
                flowWasteResult.innerHTML += `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to complete undocking'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            flowWasteResult.innerHTML += `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    // Step 5: Review Logs
    const flowGetLogsButton = document.getElementById('flow-get-logs-button');
    const flowLogsResult = document.getElementById('flow-logs-result');
    
    flowGetLogsButton.addEventListener('click', async function() {
        try {
            const response = await fetch(`${API_URL}/logs`);
            const data = await response.json();
            
            if (data.success) {
                flowLogsResult.innerHTML = `
                    <div class="alert alert-success">
                        <p>Successfully retrieved logs!</p>
                    </div>
                    <h4>Log Entries:</h4>
                    ${createTableHTML(data.logs || [], ['timestamp', 'userId', 'actionType', 'itemId', 'details'])}
                `;
            } else {
                flowLogsResult.innerHTML = `
                    <div class="alert alert-danger">
                        <p>Error: ${data.message || 'Failed to retrieve logs'}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            flowLogsResult.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error: ${error.message || 'An unexpected error occurred'}</p>
                </div>
            `;
        }
    });
    
    // Helper Functions
    function createTable(headers) {
        const table = document.createElement('table');
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        table.appendChild(tbody);
        
        return table;
    }
    
    function createTableHTML(data, columns) {
        if (!data || data.length === 0) {
            return '<p>No data available</p>';
        }
        
        let html = '<table><thead><tr>';
        
        // Create headers
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        
        html += '</tr></thead><tbody>';
        
        // Create rows
        data.forEach(item => {
            html += '<tr>';
            columns.forEach(col => {
                const value = typeof item[col] === 'object' ? JSON.stringify(item[col]) : (item[col] || '');
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleString();
        } catch (e) {
            return dateString;
        }
    }
    
    function formatDetails(details) {
        if (!details) return 'N/A';
        
        try {
            if (typeof details === 'string') {
                const parsed = JSON.parse(details);
                return JSON.stringify(parsed, null, 2);
            }
            return JSON.stringify(details, null, 2);
        } catch (e) {
            return details;
        }
    }
});
