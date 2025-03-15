// Dashboard JavaScript for Space Station Cargo Management System

// Initialize dashboard when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Load dashboard data
    loadDashboardData();
    
    // Set up event listeners
    setupDashboardEventListeners();
});

// Set up dashboard-specific event listeners
function setupDashboardEventListeners() {
    // Refresh dashboard button
    const refreshDashboardBtn = document.getElementById('refreshDashboardBtn');
    if (refreshDashboardBtn) {
        refreshDashboardBtn.addEventListener('click', function() {
            loadDashboardData();
        });
    }
    
    // Simulate next day button
    const simulateNextDayBtn = document.getElementById('simulateNextDayBtn');
    if (simulateNextDayBtn) {
        simulateNextDayBtn.addEventListener('click', simulateNextDay);
    }
}

// Load all dashboard data
async function loadDashboardData() {
    try {
        // Show loading indicators
        setLoadingState(true);
        
        // Load counts
        await loadCounts();
        
        // Load expiry chart
        await loadExpiryChart();
        
        // Load zone distribution
        await loadZoneDistribution();
        
        // Load recent activity
        await loadRecentActivity();
        
        // Hide loading indicators
        setLoadingState(false);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Error loading dashboard data. Please try again.', 'danger');
        setLoadingState(false);
    }
}

// Set loading state for dashboard elements
function setLoadingState(isLoading) {
    const loadingIndicators = [
        { id: 'totalItemsCount', value: '--' },
        { id: 'wasteItemsCount', value: '--' },
        { id: 'containersCount', value: '--' },
        { id: 'currentDate', value: '--' }
    ];
    
    if (isLoading) {
        // Set placeholders during loading
        loadingIndicators.forEach(indicator => {
            const element = document.getElementById(indicator.id);
            if (element) {
                element.textContent = indicator.value;
            }
        });
        
        // Clear charts
        document.getElementById('expiryChart').innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('zoneDistributionChart').innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Clear activity table
        document.getElementById('recentActivityTable').innerHTML = '<tr><td colspan="5" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></td></tr>';
    }
}

// Load count statistics
async function loadCounts() {
    try {
        // Get total items count
        const itemsResponse = await fetch('/api/items');
        const itemsData = await itemsResponse.json();
        
        if (itemsData.success) {
            let totalItems = 0;
            let wasteItems = 0;
            
            itemsData.data.forEach(item => {
                totalItems++;
                if (item.is_waste) {
                    wasteItems++;
                }
            });
            
            document.getElementById('totalItemsCount').textContent = totalItems;
            document.getElementById('wasteItemsCount').textContent = wasteItems;
        }
        
        // Get containers count
        const containersResponse = await fetch('/api/containers');
        const containersData = await containersResponse.json();
        
        if (containersData.success) {
            document.getElementById('containersCount').textContent = containersData.data.length;
        }
        
        // Set current date
        document.getElementById('currentDate').textContent = new Date().toLocaleDateString();
    } catch (error) {
        console.error('Error loading counts:', error);
        throw error;
    }
}

// Load and draw the expiry chart
async function loadExpiryChart() {
    try {
        const response = await fetch('/api/time/forecast/expiry?days=30');
        const data = await response.json();
        
        if (data.success) {
            const forecast = data.data.forecast;
            
            // Prepare chart data
            const chartData = forecast.map(entry => ({
                date: new Date(entry.date),
                daysFromNow: entry.days_from_now,
                count: entry.items.length
            })).sort((a, b) => a.daysFromNow - b.daysFromNow);
            
            // Draw chart
            drawExpiryChart(chartData);
        } else {
            document.getElementById('expiryChart').innerHTML = '<div class="alert alert-warning">Error loading expiry data</div>';
        }
    } catch (error) {
        console.error('Error loading expiry chart:', error);
        document.getElementById('expiryChart').innerHTML = '<div class="alert alert-danger">Error loading expiry data</div>';
        throw error;
    }
}

// Draw the expiry chart using D3.js
function drawExpiryChart(data) {
    // Clear the chart container
    document.getElementById('expiryChart').innerHTML = '';
    
    // If no data, show a message
    if (data.length === 0) {
        document.getElementById('expiryChart').innerHTML = '<div class="alert alert-info">No items expiring in the next 30 days</div>';
        return;
    }
    
    // Set up dimensions
    const margin = { top: 20, right: 30, bottom: 40, left: 40 };
    const width = document.getElementById('expiryChart').clientWidth - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select('#expiryChart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // X axis (days from now)
    const x = d3.scaleBand()
        .domain(data.map(d => d.daysFromNow))
        .range([0, width])
        .padding(0.1);
    
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d => `Day ${d}`))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');
    
    // Y axis (number of items)
    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count)])
        .nice()
        .range([height, 0]);
    
    svg.append('g')
        .call(d3.axisLeft(y));
    
    // Add bars
    svg.selectAll('.bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'bar')
        .attr('x', d => x(d.daysFromNow))
        .attr('width', x.bandwidth())
        .attr('y', d => y(d.count))
        .attr('height', d => height - y(d.count))
        .attr('fill', d => {
            // Color based on urgency
            if (d.daysFromNow <= 7) return '#dc3545'; // Danger (red)
            if (d.daysFromNow <= 14) return '#ffc107'; // Warning (yellow)
            return '#0d6efd'; // Primary (blue)
        });
    
    // Add labels on bars
    svg.selectAll('.label')
        .data(data)
        .enter()
        .append('text')
        .attr('class', 'label')
        .attr('x', d => x(d.daysFromNow) + x.bandwidth() / 2)
        .attr('y', d => y(d.count) - 5)
        .attr('text-anchor', 'middle')
        .text(d => d.count)
        .attr('fill', 'white');
    
    // Add chart title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', 0 - (margin.top / 2))
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .style('fill', 'white')
        .text('Items Expiring in Next 30 Days');
}

// Load and draw the zone distribution chart
async function loadZoneDistribution() {
    try {
        // Fetch zones
        const zonesResponse = await fetch('/api/zones');
        const zonesData = await zonesResponse.json();
        
        if (!zonesData.success) {
            document.getElementById('zoneDistributionChart').innerHTML = '<div class="alert alert-warning">Error loading zone data</div>';
            return;
        }
        
        // Fetch all items
        const itemsResponse = await fetch('/api/items?waste=false');
        const itemsData = await itemsResponse.json();
        
        if (!itemsData.success) {
            document.getElementById('zoneDistributionChart').innerHTML = '<div class="alert alert-warning">Error loading item data</div>';
            return;
        }
        
        // Fetch all containers
        const containersResponse = await fetch('/api/containers');
        const containersData = await containersResponse.json();
        
        if (!containersData.success) {
            document.getElementById('zoneDistributionChart').innerHTML = '<div class="alert alert-warning">Error loading container data</div>';
            return;
        }
        
        // Map containers to zones
        const containerZoneMap = {};
        containersData.data.forEach(container => {
            containerZoneMap[container.id] = container.zone_id;
        });
        
        // Count items by zone
        const zoneCounts = {};
        zonesData.data.forEach(zone => {
            zoneCounts[zone.id] = {
                name: zone.name,
                count: 0
            };
        });
        
        // Count items in each zone
        itemsData.data.forEach(item => {
            if (item.container_id) {
                const zoneId = containerZoneMap[item.container_id];
                if (zoneId && zoneCounts[zoneId]) {
                    zoneCounts[zoneId].count++;
                }
            }
        });
        
        // Convert to array for chart
        const chartData = Object.values(zoneCounts);
        
        // Draw chart
        drawZoneDistributionChart(chartData);
    } catch (error) {
        console.error('Error loading zone distribution:', error);
        document.getElementById('zoneDistributionChart').innerHTML = '<div class="alert alert-danger">Error loading zone distribution data</div>';
        throw error;
    }
}

// Draw the zone distribution chart using D3.js
function drawZoneDistributionChart(data) {
    // Clear the chart container
    document.getElementById('zoneDistributionChart').innerHTML = '';
    
    // Set up dimensions
    const width = document.getElementById('zoneDistributionChart').clientWidth;
    const height = 250;
    const radius = Math.min(width, height) / 2 - 40;
    
    // Create SVG
    const svg = d3.select('#zoneDistributionChart')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${width / 2},${height / 2})`);
    
    // Color scale
    const color = d3.scaleOrdinal()
        .domain(data.map(d => d.name))
        .range(d3.schemeCategory10);
    
    // Pie generator
    const pie = d3.pie()
        .value(d => d.count)
        .sort(null); // Don't sort, keep the original order
    
    // Arc generator
    const arc = d3.arc()
        .innerRadius(0)
        .outerRadius(radius);
    
    // Label arc
    const labelArc = d3.arc()
        .innerRadius(radius * 0.6)
        .outerRadius(radius * 0.6);
    
    // Check if we have any data with count > 0
    const hasData = data.some(d => d.count > 0);
    
    if (!hasData) {
        // Show a message if there's no data
        svg.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', 0)
            .style('fill', 'white')
            .text('No items stored in containers');
        return;
    }
    
    // Generate pie slices
    const arcs = svg.selectAll('.arc')
        .data(pie(data))
        .enter()
        .append('g')
        .attr('class', 'arc');
    
    // Add colored slices
    arcs.append('path')
        .attr('d', arc)
        .attr('fill', d => color(d.data.name))
        .attr('stroke', 'white')
        .style('stroke-width', '2px')
        .style('opacity', 0.8);
    
    // Add labels
    arcs.append('text')
        .attr('transform', d => `translate(${labelArc.centroid(d)})`)
        .attr('dy', '.35em')
        .text(d => d.data.count > 0 ? d.data.name : '')
        .style('text-anchor', 'middle')
        .style('fill', 'white')
        .style('font-size', '12px');
    
    // Add a legend
    const legend = svg.selectAll('.legend')
        .data(data.filter(d => d.count > 0))
        .enter()
        .append('g')
        .attr('class', 'legend')
        .attr('transform', (d, i) => `translate(${width / 2 - 50},${-height / 2 + 20 + i * 20})`);
    
    legend.append('rect')
        .attr('x', -width / 2 + 20)
        .attr('width', 14)
        .attr('height', 14)
        .attr('fill', d => color(d.name));
    
    legend.append('text')
        .attr('x', -width / 2 + 40)
        .attr('y', 10)
        .text(d => `${d.name} (${d.count})`)
        .style('font-size', '12px')
        .style('fill', 'white');
}

// Load recent activity logs
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/logs?limit=10');
        const data = await response.json();
        
        if (data.success) {
            const logs = data.data;
            const tableBody = document.getElementById('recentActivityTable');
            
            // Clear table
            tableBody.innerHTML = '';
            
            if (logs.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No recent activity</td></tr>';
                return;
            }
            
            // Add logs to table
            logs.forEach(log => {
                const row = document.createElement('tr');
                
                // Format timestamp
                const timestamp = new Date(log.timestamp);
                const formattedTime = timestamp.toLocaleString();
                
                // Capitalize first letter of action
                const action = log.action.charAt(0).toUpperCase() + log.action.slice(1);
                
                // Create table cells
                row.innerHTML = `
                    <td>${formattedTime}</td>
                    <td>${action}</td>
                    <td>${log.item_name || 'Unknown'}</td>
                    <td>${log.to_container_id || log.from_container_id || 'N/A'}</td>
                    <td>${log.astronaut_name || 'System'}</td>
                `;
                
                tableBody.appendChild(row);
            });
        } else {
            document.getElementById('recentActivityTable').innerHTML = '<tr><td colspan="5" class="text-center">Error loading activity</td></tr>';
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
        document.getElementById('recentActivityTable').innerHTML = '<tr><td colspan="5" class="text-center">Error loading activity</td></tr>';
        throw error;
    }
}

// Simulate the next day
async function simulateNextDay() {
    try {
        const button = document.getElementById('simulateNextDayBtn');
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Simulating...';
        button.disabled = true;
        
        const response = await fetch('/api/time/next-day', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items_used: [] })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Day simulated successfully. New date: ' + data.data.new_date, 'success');
            
            // Update current date display
            document.getElementById('currentDate').textContent = new Date(data.data.new_date).toLocaleDateString();
            
            // Refresh dashboard data after a short delay
            setTimeout(() => {
                loadDashboardData();
            }, 1000);
        } else {
            showToast(`Error: ${data.error}`, 'danger');
        }
        
        // Reset button
        button.innerHTML = '<i class="fas fa-calendar-day"></i> Simulate Next Day';
        button.disabled = false;
    } catch (error) {
        console.error('Error simulating next day:', error);
        showToast('Error simulating next day. Please try again.', 'danger');
        
        // Reset button
        const button = document.getElementById('simulateNextDayBtn');
        button.innerHTML = '<i class="fas fa-calendar-day"></i> Simulate Next Day';
        button.disabled = false;
    }
}
