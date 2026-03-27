// Dashboard JavaScript

// Global variables
let simulationRunning = false;
let optimizationEnabled = false;
let simulationData = {
    activeVehicles: 0,
    completedVehicles: 0,
    avgTravelTime: 0,
    avgWaitingTime: 0,
    avgSpeed: 0,
    avgCongestion: 0,
    travelTimeImprovement: 0
};
let historyData = {
    travelTimes: [],
    congestionLevels: [],
    timestamps: []
};
let intersections = [];
let roads = [];
let vehicles = [];
let currentUser = null;

// Charts
let travelTimeChart;
let congestionChart;
let comparisonChart;

// API endpoint (adjust if needed)
const API_BASE_URL = '/api';

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initCharts();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check authentication status
    checkAuthStatus();
    
    // Initialize the traffic map
    initTrafficMap();
    
    // Fetch initial data
    fetchSimulationData();
});

// Initialize Plotly charts
function initCharts() {
    // Travel Time Chart
    const travelTimeChartDiv = document.getElementById('travelTimeChart');
    travelTimeChart = Plotly.newPlot(travelTimeChartDiv, [
        {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            name: 'Travel Time',
            line: { color: '#007bff' }
        }
    ], {
        margin: { t: 10, r: 10, l: 50, b: 50 },
        xaxis: { title: 'Time' },
        yaxis: { title: 'Avg. Travel Time (s)' }
    });
    
    // Congestion Chart
    const congestionChartDiv = document.getElementById('congestionChart');
    congestionChart = Plotly.newPlot(congestionChartDiv, [
        {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            name: 'Congestion',
            line: { color: '#dc3545' }
        }
    ], {
        margin: { t: 10, r: 10, l: 50, b: 50 },
        xaxis: { title: 'Time' },
        yaxis: { title: 'Avg. Congestion (%)' }
    });
    
    // Comparison Chart (initialized but hidden until comparison is run)
    const comparisonChartDiv = document.getElementById('comparisonChart');
    comparisonChart = Plotly.newPlot(comparisonChartDiv, [
        {
            x: ['Travel Time', 'Waiting Time', 'Speed'],
            y: [0, 0, 0],
            type: 'bar',
            name: 'Baseline',
            marker: { color: '#6c757d' }
        },
        {
            x: ['Travel Time', 'Waiting Time', 'Speed'],
            y: [0, 0, 0],
            type: 'bar',
            name: 'Optimized',
            marker: { color: '#28a745' }
        }
    ], {
        margin: { t: 10, r: 10, l: 50, b: 50 },
        barmode: 'group',
        yaxis: { title: 'Value' }
    });
}

// Set up event listeners for buttons and controls
function setupEventListeners() {
    // Navigation
    document.getElementById('controlPanel').addEventListener('click', function(e) {
        e.preventDefault();
        showView('controlPanelView');
    });
    
    document.getElementById('comparisonView').addEventListener('click', function(e) {
        e.preventDefault();
        showView('comparisonViewContent');
    });
    
    // Simulation controls
    document.getElementById('startSimulation').addEventListener('click', startSimulation);
    document.getElementById('stopSimulation').addEventListener('click', stopSimulation);
    document.getElementById('resetSimulation').addEventListener('click', resetSimulation);
    document.getElementById('optimizationToggle').addEventListener('change', toggleOptimization);
    
    // Traffic light controls
    document.getElementById('setLightState').addEventListener('click', setTrafficLightState);
    document.getElementById('resetLights').addEventListener('click', resetTrafficLights);
    
    // Comparison controls
    document.getElementById('runComparison').addEventListener('click', runComparison);
    
    // Authentication
    document.getElementById('loginBtn').addEventListener('click', showLoginModal);
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('loginForm').addEventListener('submit', function(e) {
        e.preventDefault();
        login();
    });
    
    // Intersection selection change
    document.getElementById('intersectionSelect').addEventListener('change', function() {
        updateRoadSelectOptions();
    });
}

// Show the selected view and hide others
function showView(viewId) {
    // Hide all views
    document.getElementById('dashboardView').classList.add('d-none');
    document.getElementById('controlPanelView').classList.add('d-none');
    document.getElementById('comparisonViewContent').classList.add('d-none');
    
    // Show selected view
    document.getElementById(viewId).classList.remove('d-none');
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    
    // Set active nav link based on view
    if (viewId === 'dashboardView') {
        document.querySelector('.navbar-nav .nav-link:first-child').classList.add('active');
    } else if (viewId === 'controlPanelView') {
        document.getElementById('controlPanel').classList.add('active');
    } else if (viewId === 'comparisonViewContent') {
        document.getElementById('comparisonView').classList.add('active');
    }
}

// Check authentication status
function checkAuthStatus() {
    fetch(`${API_BASE_URL}/auth/status`)
        .then(response => response.json())
        .then(data => {
            if (data.authenticated) {
                currentUser = {
                    username: data.username,
                    role: data.role
                };
                updateAuthUI(true);
            } else {
                updateAuthUI(false);
            }
        })
        .catch(error => {
            console.error('Error checking auth status:', error);
            updateAuthUI(false);
        });
}

// Update UI based on authentication status
function updateAuthUI(isAuthenticated) {
    if (isAuthenticated && currentUser) {
        document.getElementById('loginBtn').classList.add('d-none');
        document.getElementById('logoutBtn').classList.remove('d-none');
        document.getElementById('userInfo').classList.remove('d-none');
        document.getElementById('username').textContent = currentUser.username;
        document.getElementById('userRole').textContent = currentUser.role;
        
        // Enable manager/admin features if appropriate
        if (currentUser.role === 'admin' || currentUser.role === 'manager') {
            document.querySelectorAll('.manager-only').forEach(el => el.classList.remove('d-none'));
            document.querySelectorAll('.auth-warning').forEach(el => el.classList.add('d-none'));
        }
    } else {
        document.getElementById('loginBtn').classList.remove('d-none');
        document.getElementById('logoutBtn').classList.add('d-none');
        document.getElementById('userInfo').classList.add('d-none');
        
        // Disable manager/admin features
        document.querySelectorAll('.manager-only').forEach(el => el.classList.add('d-none'));
        document.querySelectorAll('.auth-warning').forEach(el => el.classList.remove('d-none'));
    }
}

// Show login modal
function showLoginModal() {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
}

// Login function
function login() {
    const username = document.getElementById('usernameInput').value;
    const password = document.getElementById('passwordInput').value;
    const errorElement = document.getElementById('loginError');
    
    fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentUser = {
                username: data.username,
                role: data.role
            };
            updateAuthUI(true);
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
        } else {
            errorElement.textContent = data.message || 'Login failed';
            errorElement.classList.remove('d-none');
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        errorElement.textContent = 'An error occurred during login';
        errorElement.classList.remove('d-none');
    });
}

// Logout function
function logout() {
    fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        currentUser = null;
        updateAuthUI(false);
    })
    .catch(error => {
        console.error('Logout error:', error);
    });
}

// Initialize traffic map
function initTrafficMap() {
    const mapContainer = document.getElementById('trafficMap');
    
    // Fetch map data (roads, intersections)
    Promise.all([
        fetch(`${API_BASE_URL}/roads`).then(res => res.json()),
        fetch(`${API_BASE_URL}/intersections`).then(res => res.json())
    ])
    .then(([roadsData, intersectionsData]) => {
        roads = roadsData;
        intersections = intersectionsData;
        
        // Render the map
        renderTrafficMap();
        
        // Populate intersection select
        populateIntersectionSelect();
    })
    .catch(error => {
        console.error('Error fetching map data:', error);
    });
}

// Render traffic map with roads, intersections and vehicles
function renderTrafficMap() {
    const mapContainer = document.getElementById('trafficMap');
    
    // Clear existing map elements
    mapContainer.innerHTML = '';
    
    // Set map dimensions
    const mapWidth = mapContainer.clientWidth;
    const mapHeight = mapContainer.clientHeight;
    
    // Calculate scale factors
    const maxX = Math.max(...intersections.map(i => i.x), 100);
    const maxY = Math.max(...intersections.map(i => i.y), 100);
    const scaleX = (mapWidth - 40) / maxX;
    const scaleY = (mapHeight - 40) / maxY;
    
    // Render roads
    roads.forEach(road => {
        const roadElement = document.createElement('div');
        roadElement.className = `road ${road.direction === 'horizontal' ? 'horizontal' : 'vertical'}`;
        
        // Find start and end intersections
        const startIntersection = intersections.find(i => i.id === road.start_intersection_id);
        const endIntersection = intersections.find(i => i.id === road.end_intersection_id);
        
        if (startIntersection && endIntersection) {
            const startX = startIntersection.x * scaleX + 20;
            const startY = startIntersection.y * scaleY + 20;
            const endX = endIntersection.x * scaleX + 20;
            const endY = endIntersection.y * scaleY + 20;
            
            // Calculate length and angle
            const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
            const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
            
            // Set road position and dimensions
            roadElement.style.left = `${startX}px`;
            roadElement.style.top = `${startY}px`;
            roadElement.style.width = `${length}px`;
            roadElement.style.transform = `rotate(${angle}deg)`;
            
            // Set congestion color
            if (road.congestion < 30) {
                roadElement.classList.add('congestion-low');
            } else if (road.congestion < 70) {
                roadElement.classList.add('congestion-medium');
            } else {
                roadElement.classList.add('congestion-high');
            }
            
            mapContainer.appendChild(roadElement);
        }
    });
    
    // Render intersections
    intersections.forEach(intersection => {
        const intersectionElement = document.createElement('div');
        intersectionElement.className = 'intersection';
        intersectionElement.style.left = `${intersection.x * scaleX + 20}px`;
        intersectionElement.style.top = `${intersection.y * scaleY + 20}px`;
        mapContainer.appendChild(intersectionElement);
    });
    
    // Render vehicles
    vehicles.forEach(vehicle => {
        const vehicleElement = document.createElement('div');
        vehicleElement.className = `vehicle ${vehicle.type.toLowerCase()}`;
        vehicleElement.style.left = `${vehicle.x * scaleX + 20}px`;
        vehicleElement.style.top = `${vehicle.y * scaleY + 20}px`;
        mapContainer.appendChild(vehicleElement);
    });
}

// Populate intersection select dropdown
function populateIntersectionSelect() {
    const select = document.getElementById('intersectionSelect');
    select.innerHTML = '';
    
    intersections.forEach(intersection => {
        const option = document.createElement('option');
        option.value = intersection.id;
        option.textContent = `Intersection ${intersection.id}`;
        select.appendChild(option);
    });
    
    // Update road select options based on first intersection
    updateRoadSelectOptions();
}

// Update road select options based on selected intersection
function updateRoadSelectOptions() {
    const intersectionId = document.getElementById('intersectionSelect').value;
    const roadSelect = document.getElementById('roadSelect');
    
    roadSelect.innerHTML = '';
    
    // Filter roads connected to the selected intersection
    const connectedRoads = roads.filter(road => 
        road.start_intersection_id === intersectionId || 
        road.end_intersection_id === intersectionId
    );
    
    connectedRoads.forEach(road => {
        const option = document.createElement('option');
        option.value = road.id;
        option.textContent = `Road ${road.id}`;
        roadSelect.appendChild(option);
    });
}

// Start simulation
function startSimulation() {
    const vehicleCount = document.getElementById('vehicleCount').value;
    const emergencyRatio = document.getElementById('emergencyRatio').value;
    const publicTransportRatio = document.getElementById('publicTransportRatio').value;
    
    fetch(`${API_BASE_URL}/simulation/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            vehicle_count: parseInt(vehicleCount),
            emergency_ratio: parseInt(emergencyRatio),
            public_transport_ratio: parseInt(publicTransportRatio),
            optimization_enabled: optimizationEnabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            simulationRunning = true;
            updateSimulationStatus('Running');
            
            // Start polling for updates
            startDataPolling();
        } else {
            alert('Failed to start simulation: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error starting simulation:', error);
        alert('Error starting simulation');
    });
}

// Stop simulation
function stopSimulation() {
    fetch(`${API_BASE_URL}/simulation/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            simulationRunning = false;
            updateSimulationStatus('Stopped');
            
            // Stop polling for updates
            stopDataPolling();
        } else {
            alert('Failed to stop simulation: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error stopping simulation:', error);
        alert('Error stopping simulation');
    });
}

// Reset simulation
function resetSimulation() {
    fetch(`${API_BASE_URL}/simulation/reset`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            simulationRunning = false;
            updateSimulationStatus('Ready');
            
            // Reset data
            simulationData = {
                activeVehicles: 0,
                completedVehicles: 0,
                avgTravelTime: 0,
                avgWaitingTime: 0,
                avgSpeed: 0,
                avgCongestion: 0,
                travelTimeImprovement: 0
            };
            historyData = {
                travelTimes: [],
                congestionLevels: [],
                timestamps: []
            };
            vehicles = [];
            
            // Update UI
            updateSimulationStats();
            updateCharts();
            renderTrafficMap();
            
            // Stop polling for updates
            stopDataPolling();
        } else {
            alert('Failed to reset simulation: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error resetting simulation:', error);
        alert('Error resetting simulation');
    });
}

// Toggle optimization
function toggleOptimization() {
    optimizationEnabled = document.getElementById('optimizationToggle').checked;
    
    fetch(`${API_BASE_URL}/simulation/toggle_optimization`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            enabled: optimizationEnabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Failed to toggle optimization: ' + data.message);
            // Revert the toggle if the request failed
            document.getElementById('optimizationToggle').checked = !optimizationEnabled;
            optimizationEnabled = !optimizationEnabled;
        }
    })
    .catch(error => {
        console.error('Error toggling optimization:', error);
        alert('Error toggling optimization');
        // Revert the toggle if there was an error
        document.getElementById('optimizationToggle').checked = !optimizationEnabled;
        optimizationEnabled = !optimizationEnabled;
    });
}

// Set traffic light state
function setTrafficLightState() {
    const intersectionId = document.getElementById('intersectionSelect').value;
    const roadId = document.getElementById('roadSelect').value;
    const lightState = document.getElementById('lightStateSelect').value;
    
    fetch(`${API_BASE_URL}/traffic_light/set_state`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            intersection_id: intersectionId,
            road_id: roadId,
            state: lightState
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Traffic light state updated successfully');
            // Update intersection table
            fetchIntersectionData();
        } else {
            alert('Failed to update traffic light: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error setting traffic light state:', error);
        alert('Error setting traffic light state');
    });
}

// Reset all traffic lights
function resetTrafficLights() {
    fetch(`${API_BASE_URL}/traffic_light/reset`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('All traffic lights reset successfully');
            // Update intersection table
            fetchIntersectionData();
        } else {
            alert('Failed to reset traffic lights: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error resetting traffic lights:', error);
        alert('Error resetting traffic lights');
    });
}

// Run comparison simulation
function runComparison() {
    const duration = document.getElementById('comparisonDuration').value;
    const vehicleCount = document.getElementById('comparisonVehicleCount').value;
    
    // Show loading indicator
    document.getElementById('comparisonResults').classList.add('d-none');
    document.getElementById('comparisonLoading').classList.remove('d-none');
    
    fetch(`${API_BASE_URL}/simulation/compare`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            duration: parseInt(duration),
            vehicle_count: parseInt(vehicleCount)
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading indicator
        document.getElementById('comparisonLoading').classList.add('d-none');
        
        if (data.success) {
            // Show results
            document.getElementById('comparisonResults').classList.remove('d-none');
            
            // Update baseline stats
            document.getElementById('baselineTravelTime').textContent = data.baseline.avg_travel_time.toFixed(1) + ' s';
            document.getElementById('baselineWaitingTime').textContent = data.baseline.avg_waiting_time.toFixed(1) + ' s';
            document.getElementById('baselineSpeed').textContent = data.baseline.avg_speed.toFixed(1) + ' km/h';
            
            // Update optimized stats
            document.getElementById('optimizedTravelTime').textContent = data.optimized.avg_travel_time.toFixed(1) + ' s';
            document.getElementById('optimizedWaitingTime').textContent = data.optimized.avg_waiting_time.toFixed(1) + ' s';
            document.getElementById('optimizedSpeed').textContent = data.optimized.avg_speed.toFixed(1) + ' km/h';
            
            // Calculate improvements
            const travelTimeImprovement = ((data.baseline.avg_travel_time - data.optimized.avg_travel_time) / data.baseline.avg_travel_time * 100).toFixed(1);
            const waitingTimeImprovement = ((data.baseline.avg_waiting_time - data.optimized.avg_waiting_time) / data.baseline.avg_waiting_time * 100).toFixed(1);
            
            document.getElementById('travelTimeImprovementCompare').textContent = travelTimeImprovement + '%';
            document.getElementById('waitingTimeImprovementCompare').textContent = waitingTimeImprovement + '%';
            
            // Update comparison chart
            updateComparisonChart(data.baseline, data.optimized);
        } else {
            alert('Failed to run comparison: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error running comparison:', error);
        alert('Error running comparison');
        document.getElementById('comparisonLoading').classList.add('d-none');
    });
}

// Update comparison chart
function updateComparisonChart(baseline, optimized) {
    const chartData = [
        {
            x: ['Travel Time (s)', 'Waiting Time (s)', 'Speed (km/h)'],
            y: [baseline.avg_travel_time, baseline.avg_waiting_time, baseline.avg_speed],
            type: 'bar',
            name: 'Baseline',
            marker: { color: '#6c757d' }
        },
        {
            x: ['Travel Time (s)', 'Waiting Time (s)', 'Speed (km/h)'],
            y: [optimized.avg_travel_time, optimized.avg_waiting_time, optimized.avg_speed],
            type: 'bar',
            name: 'Optimized',
            marker: { color: '#28a745' }
        }
    ];
    
    Plotly.react('comparisonChart', chartData, {
        margin: { t: 10, r: 10, l: 50, b: 50 },
        barmode: 'group'
    });
}

// Update simulation status indicator
function updateSimulationStatus(status) {
    const statusElement = document.getElementById('simulationStatus');
    statusElement.textContent = status;
    
    // Update status badge color
    statusElement.className = 'badge';
    if (status === 'Running') {
        statusElement.classList.add('bg-success');
    } else if (status === 'Stopped') {
        statusElement.classList.add('bg-danger');
    } else {
        statusElement.classList.add('bg-secondary');
    }
}

// Polling for simulation data updates
let dataPollingInterval;

function startDataPolling() {
    // Clear any existing interval
    if (dataPollingInterval) {
        clearInterval(dataPollingInterval);
    }
    
    // Poll for data every second
    dataPollingInterval = setInterval(() => {
        fetchSimulationData();
    }, 1000);
}

function stopDataPolling() {
    if (dataPollingInterval) {
        clearInterval(dataPollingInterval);
        dataPollingInterval = null;
    }
}

// Fetch simulation data from API
function fetchSimulationData() {
    Promise.all([
        fetch(`${API_BASE_URL}/simulation/stats`).then(res => res.json()),
        fetch(`${API_BASE_URL}/simulation/history`).then(res => res.json()),
        fetch(`${API_BASE_URL}/vehicles`).then(res => res.json())
    ])
    .then(([statsData, historyData, vehiclesData]) => {
        // Update simulation data
        simulationData = statsData;
        historyData = historyData;
        vehicles = vehiclesData;
        
        // Update UI
        updateSimulationStats();
        updateCharts();
        renderTrafficMap();
        
        // Fetch intersection data for control panel
        if (document.getElementById('controlPanelView').classList.contains('d-none') === false) {
            fetchIntersectionData();
        }
    })
    .catch(error => {
        console.error('Error fetching simulation data:', error);
    });
}

// Fetch intersection data for control panel
function fetchIntersectionData() {
    fetch(`${API_BASE_URL}/intersections/details`)
        .then(response => response.json())
        .then(data => {
            updateIntersectionTable(data);
        })
        .catch(error => {
            console.error('Error fetching intersection data:', error);
        });
}

// Update intersection table
function updateIntersectionTable(intersectionData) {
    const tableBody = document.querySelector('#intersectionTable tbody');
    tableBody.innerHTML = '';
    
    intersectionData.forEach(intersection => {
        const row = document.createElement('tr');
        
        // Intersection ID
        const idCell = document.createElement('td');
        idCell.textContent = intersection.id;
        row.appendChild(idCell);
        
        // Vehicle count
        const vehicleCell = document.createElement('td');
        vehicleCell.textContent = intersection.vehicle_count;
        row.appendChild(vehicleCell);
        
        // Congestion level
        const congestionCell = document.createElement('td');
        const congestionLevel = intersection.congestion_level;
        congestionCell.textContent = congestionLevel + '%';
        
        // Add color class based on congestion level
        if (congestionLevel < 30) {
            congestionCell.classList.add('text-success');
        } else if (congestionLevel < 70) {
            congestionCell.classList.add('text-warning');
        } else {
            congestionCell.classList.add('text-danger');
        }
        
        row.appendChild(congestionCell);
        
        // Traffic lights
        const lightsCell = document.createElement('td');
        
        intersection.traffic_lights.forEach(light => {
            const lightIndicator = document.createElement('span');
            lightIndicator.className = 'traffic-light';
            
            // Add color class based on light state
            if (light.state === 'RED') {
                lightIndicator.classList.add('red');
            } else if (light.state === 'YELLOW') {
                lightIndicator.classList.add('yellow');
            } else {
                lightIndicator.classList.add('green');
            }
            
            lightsCell.appendChild(lightIndicator);
            
            // Add road ID text
            const roadText = document.createTextNode(` Road ${light.road_id} `);
            lightsCell.appendChild(roadText);
        });
        
        row.appendChild(lightsCell);
        
        tableBody.appendChild(row);
    });
}

// Update simulation statistics display
function updateSimulationStats() {
    document.getElementById('activeVehicles').textContent = simulationData.activeVehicles;
    document.getElementById('completedVehicles').textContent = simulationData.completedVehicles;
    document.getElementById('avgTravelTime').textContent = simulationData.avgTravelTime.toFixed(1) + ' s';
    document.getElementById('avgWaitingTime').textContent = simulationData.avgWaitingTime.toFixed(1) + ' s';
    document.getElementById('avgSpeed').textContent = simulationData.avgSpeed.toFixed(1) + ' km/h';
    document.getElementById('avgCongestion').textContent = simulationData.avgCongestion.toFixed(1) + '%';
    
    // Show improvement if optimization is enabled
    if (optimizationEnabled && simulationData.travelTimeImprovement > 0) {
        document.getElementById('improvementRow').style.display = 'flex';
        document.getElementById('travelTimeImprovement').textContent = simulationData.travelTimeImprovement.toFixed(1) + '%';
    } else {
        document.getElementById('improvementRow').style.display = 'none';
    }
}

// Update charts with latest data
function updateCharts() {
    // Update travel time chart
    Plotly.update('travelTimeChart', {
        x: [historyData.timestamps],
        y: [historyData.travelTimes]
    }, {}, [0]);
    
    // Update congestion chart
    Plotly.update('congestionChart', {
        x: [historyData.timestamps],
        y: [historyData.congestionLevels]
    }, {}, [0]);
}
