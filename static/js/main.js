// Main JavaScript file for Space Station Cargo Management System

// Global variables
let mainCurrentContainer = null;
let selectedItem = null;
let astronautName = '';

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Space Station Cargo Management System initialized');
    
    // Set up event listeners for common elements
    setupEventListeners();
    
    // Show notification for any flash messages
    showFlashMessages();
});

// Set up event listeners for common UI elements
function setupEventListeners() {
    // Add item button event listeners
    const addNewItemBtn = document.getElementById('addNewItemBtn');
    if (addNewItemBtn) {
        addNewItemBtn.addEventListener('click', showAddItemModal);
    }
    
    // Save item button
    const saveItemBtn = document.getElementById('saveItemBtn');
    if (saveItemBtn) {
        saveItemBtn.addEventListener('click', saveNewItem);
    }
    
    // Priority slider value display
    const itemPriority = document.getElementById('itemPriority');
    if (itemPriority) {
        itemPriority.addEventListener('input', function() {
            document.getElementById('priorityValueDisplay').textContent = this.value;
        });
    }
    
    // Search item button
    const searchItemBtn = document.getElementById('searchItemBtn');
    if (searchItemBtn) {
        searchItemBtn.addEventListener('click', showSearchItemModal);
    }
    
    // Search item submit button
    const searchItemSubmitBtn = document.getElementById('searchItemSubmitBtn');
    if (searchItemSubmitBtn) {
        searchItemSubmitBtn.addEventListener('click', searchForItem);
    }
    
    // Retrieve recommended item button
    const retrieveRecommendedItemBtn = document.getElementById('retrieveRecommendedItemBtn');
    if (retrieveRecommendedItemBtn) {
        retrieveRecommendedItemBtn.addEventListener('click', showAstronautNameModal);
    }
    
    // View containers button
    const viewContainersBtn = document.getElementById('viewContainersBtn');
    if (viewContainersBtn) {
        viewContainersBtn.addEventListener('click', () => {
            window.location.href = '/containers';
        });
    }
    
    // Check waste button
    const checkWasteBtn = document.getElementById('checkWasteBtn');
    if (checkWasteBtn) {
        checkWasteBtn.addEventListener('click', checkForWasteItems);
    }
    
    // Confirm retrieval button
    const confirmRetrievalBtn = document.getElementById('confirmRetrievalBtn');
    if (confirmRetrievalBtn) {
        confirmRetrievalBtn.addEventListener('click', executeItemRetrieval);
    }
}

// Show flash messages as alerts
function showFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(message);
            alert.close();
        }, 5000);
    });
}

// Show modal for adding a new item
function showAddItemModal() {
    // Load zones for dropdown
    loadZones().then(() => {
        const modal = new bootstrap.Modal(document.getElementById('addItemModal'));
        modal.show();
    });
}

// Load zones for the dropdown
async function loadZones() {
    try {
        const response = await fetch('/api/zones');
        const data = await response.json();
        
        if (data.success) {
            const zoneSelect = document.getElementById('itemPreferredZone');
            if (zoneSelect) {
                // Clear existing options except the first one
                zoneSelect.innerHTML = '<option value="">-- Select Zone --</option>';
                
                // Add zones as options
                data.data.forEach(zone => {
                    const option = document.createElement('option');
                    option.value = zone.id;
                    option.textContent = zone.name;
                    zoneSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading zones:', error);
        showToast('Error loading zones. Please try again.', 'danger');
    }
}

// Save a new item
async function saveNewItem() {
    const itemData = {
        id: document.getElementById('itemId').value,
        name: document.getElementById('itemName').value,
        width: parseFloat(document.getElementById('itemWidth').value),
        depth: parseFloat(document.getElementById('itemDepth').value),
        height: parseFloat(document.getElementById('itemHeight').value),
        mass: parseFloat(document.getElementById('itemMass').value),
        priority: parseInt(document.getElementById('itemPriority').value),
        expiry_date: document.getElementById('itemExpiryDate').value || null,
        usage_limit: document.getElementById('itemUsageLimit').value || null,
        preferred_zone_id: document.getElementById('itemPreferredZone').value || null
    };
    
    try {
        const response = await fetch('/api/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(itemData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Item added successfully!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addItemModal'));
            modal.hide();
            
            // Reset the form
            document.getElementById('addItemForm').reset();
            
            // Refresh page if we're on items page
            if (window.location.pathname === '/items') {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showToast(`Error: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error saving item:', error);
        showToast('Error saving item. Please try again.', 'danger');
    }
}

// Show the search item modal
function showSearchItemModal() {
    const modal = new bootstrap.Modal(document.getElementById('searchItemModal'));
    
    // Reset search form
    document.getElementById('searchItemName').value = '';
    document.getElementById('searchResultsContainer').classList.add('d-none');
    document.getElementById('searchNoResults').classList.add('d-none');
    
    modal.show();
}

// Search for an item
async function searchForItem() {
    const itemName = document.getElementById('searchItemName').value;
    
    if (!itemName) {
        showToast('Please enter an item name', 'warning');
        return;
    }
    
    try {
        // Show loading state
        document.getElementById('searchItemSubmitBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Searching...';
        document.getElementById('searchItemSubmitBtn').disabled = true;
        
        const response = await fetch('/api/retrieval/suggest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ item_name: itemName })
        });
        
        const data = await response.json();
        
        // Reset button state
        document.getElementById('searchItemSubmitBtn').innerHTML = 'Search';
        document.getElementById('searchItemSubmitBtn').disabled = false;
        
        if (data.success) {
            // Show results
            document.getElementById('searchResultsContainer').classList.remove('d-none');
            document.getElementById('searchNoResults').classList.add('d-none');
            
            const item = data.data.item;
            const retrievalInfo = data.data.retrieval_info;
            
            // Store selected item for retrieval
            selectedItem = item.id;
            
            // Update UI with item details
            document.getElementById('recommendedItemName').textContent = item.name;
            document.getElementById('recommendedItemContainer').textContent = item.container_id || 'Not stored';
            document.getElementById('recommendedItemSteps').textContent = retrievalInfo.steps;
            
            // Format expiry date
            const expiryText = item.expiry_date ? 
                new Date(item.expiry_date).toLocaleDateString() : 
                'No expiry date';
            document.getElementById('recommendedItemExpiry').textContent = expiryText;
            
            // Enable view location button if item is stored
            const viewLocationBtn = document.getElementById('viewRecommendedItemLocationBtn');
            if (item.container_id) {
                viewLocationBtn.classList.remove('d-none');
                viewLocationBtn.onclick = () => {
                    showContainerVisualization(item.container_id, item.id);
                };
            } else {
                viewLocationBtn.classList.add('d-none');
            }
        } else {
            // Show no results message
            document.getElementById('searchResultsContainer').classList.add('d-none');
            document.getElementById('searchNoResults').classList.remove('d-none');
        }
    } catch (error) {
        console.error('Error searching for item:', error);
        showToast('Error searching for item. Please try again.', 'danger');
    }
}

// Show astronaut name modal before retrieving an item
function showAstronautNameModal() {
    if (!selectedItem) {
        showToast('No item selected', 'warning');
        return;
    }
    
    // Reset form
    document.getElementById('astronautName').value = '';
    document.getElementById('useItemCheck').checked = false;
    
    const modal = new bootstrap.Modal(document.getElementById('astronautNameModal'));
    modal.show();
}

// Execute item retrieval
async function executeItemRetrieval() {
    if (!selectedItem) {
        showToast('No item selected', 'warning');
        return;
    }
    
    const astronautName = document.getElementById('astronautName').value;
    const useItem = document.getElementById('useItemCheck').checked;
    
    if (!astronautName) {
        showToast('Please enter astronaut name', 'warning');
        return;
    }
    
    try {
        // Show loading state
        document.getElementById('confirmRetrievalBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        document.getElementById('confirmRetrievalBtn').disabled = true;
        
        const response = await fetch('/api/retrieval/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_id: selectedItem,
                astronaut_name: astronautName,
                use_item: useItem
            })
        });
        
        const data = await response.json();
        
        // Reset button state
        document.getElementById('confirmRetrievalBtn').innerHTML = 'Confirm Retrieval';
        document.getElementById('confirmRetrievalBtn').disabled = false;
        
        if (data.success) {
            // Close both modals
            const astronautModal = bootstrap.Modal.getInstance(document.getElementById('astronautNameModal'));
            astronautModal.hide();
            
            const searchModal = bootstrap.Modal.getInstance(document.getElementById('searchItemModal'));
            searchModal.hide();
            
            showToast(`Item ${data.data.name} retrieved successfully by ${astronautName}`, 'success');
            
            // Reset selected item
            selectedItem = null;
            
            // Refresh page after a short delay if we're on a relevant page
            const path = window.location.pathname;
            if (path === '/' || path === '/items' || path === '/containers') {
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        } else {
            showToast(`Error: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error retrieving item:', error);
        showToast('Error retrieving item. Please try again.', 'danger');
        
        // Reset button state
        document.getElementById('confirmRetrievalBtn').innerHTML = 'Confirm Retrieval';
        document.getElementById('confirmRetrievalBtn').disabled = false;
    }
}

// Check for waste items
async function checkForWasteItems() {
    try {
        const button = document.getElementById('checkWasteBtn');
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
        button.disabled = true;
        
        const response = await fetch('/api/waste/check');
        const data = await response.json();
        
        button.innerHTML = '<i class="fas fa-trash"></i> Check Waste';
        button.disabled = false;
        
        if (data.success) {
            const newlyWastedCount = data.data.newly_wasted_count;
            
            if (newlyWastedCount > 0) {
                showToast(`Found ${newlyWastedCount} new waste item(s)`, 'warning');
                
                // Redirect to waste page
                setTimeout(() => {
                    window.location.href = '/waste';
                }, 1500);
            } else {
                showToast('No new waste items found', 'info');
            }
        } else {
            showToast(`Error: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error checking waste:', error);
        showToast('Error checking waste. Please try again.', 'danger');
        
        const button = document.getElementById('checkWasteBtn');
        button.innerHTML = '<i class="fas fa-trash"></i> Check Waste';
        button.disabled = false;
    }
}

// Show container visualization
function showContainerVisualization(containerId, highlightItemId = null) {
    mainCurrentContainer = containerId;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('visualizationModal'));
    modal.show();
    
    // Update container info
    document.getElementById('containerIdDisplay').textContent = 'Loading...';
    document.getElementById('containerZoneDisplay').textContent = 'Loading...';
    document.getElementById('containerSizeDisplay').textContent = 'Loading...';
    document.getElementById('containerContents').innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    
    // Initialize 3D visualization
    initializeContainerVisualization(containerId, highlightItemId);
    
    // Fetch container details
    fetchContainerDetails(containerId);
}

// Fetch container details
        console.error('Error fetching container details:', error);
        document.getElementById('containerContents').innerHTML = '<div class="alert alert-danger">Error loading container details</div>';
    }
}

// Helper function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const html = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toastContainer').insertAdjacentHTML('beforeend', html);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    // Show the toast
    toast.show();
}

// Make showToast available globally for use in other scripts
window.showToast = showToast;

// Make showToast available globally for use in other scripts
window.showToast = showToast;
    toast.show();
    
    // Remove the toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}
// Fetch container details
async function fetchContainerDetails(containerId) {
    try {
        if (!containerId) {
            console.error('Container ID is undefined or null');
            showToast('Error: Container ID is missing', 'danger');
            return;
        }
        
        const response = await fetch(`/api/containers/${containerId}`);
        
        if (!response.ok) {
            const errorMsg = `Server responded with status: ${response.status}`;
            console.error(errorMsg);
            showToast(`Error: ${errorMsg}`, 'danger');
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            const container = data.data;
            
            // Update container info
            document.getElementById('containerIdDisplay').textContent = container.id;
            document.getElementById('containerZoneDisplay').textContent = container.zone_name;
            document.getElementById('containerSizeDisplay').textContent = `${container.width} × ${container.depth} × ${container.height} cm`;
            
            // Update container contents
            const contentsElement = document.getElementById('containerContents');
            contentsElement.innerHTML = '';
            
            if (container.items && container.items.length > 0) {
                const list = document.createElement('ul');
                list.className = 'list-group';
                
                container.items.forEach(item => {
                    const listItem = document.createElement('li');
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center bg-dark text-white border-secondary';
                    
                    if (item.is_waste) {
                        listItem.classList.add('waste-item');
                    } else if (item.is_expired) {
                        listItem.classList.add('expired-item');
                    }
                    
                    // Create priority indicator
                    const priorityIndicator = document.createElement('span');
                    priorityIndicator.className = 'priority-indicator';
                    
                    if (item.priority >= 80) {
                        priorityIndicator.classList.add('priority-high');
                    } else if (item.priority >= 50) {
                        priorityIndicator.classList.add('priority-medium');
                    } else {
                        priorityIndicator.classList.add('priority-low');
                    }
                    
                    // Item details
                    const itemDetails = document.createElement('div');
                    itemDetails.className = 'ms-2 me-auto';
                    itemDetails.innerHTML = `<strong>${item.name}</strong> (${item.id})`;
                    
                    // Add details for position
                    if (item.x_pos !== null && item.y_pos !== null && item.z_pos !== null) {
                        const positionText = document.createElement('small');
                        positionText.className = 'd-block text-muted';
                        positionText.textContent = `Position: (${item.x_pos}, ${item.y_pos}, ${item.z_pos})`;
                        itemDetails.appendChild(positionText);
                    }
                    
                    // Add expiry date if present
                    if (item.expiry_date) {
                        const expiryText = document.createElement('small');
                        expiryText.className = 'd-block text-muted';
                        expiryText.textContent = `Expires: ${formatDate(item.expiry_date)}`;
                        itemDetails.appendChild(expiryText);
                    }
                    
                    // Add usage info if present
                    if (item.usage_limit) {
                        const usageText = document.createElement('small');
                        usageText.className = 'd-block text-muted';
                        usageText.textContent = `Uses: ${item.uses_remaining}/${item.usage_limit}`;
                        itemDetails.appendChild(usageText);
                    }
                    
                    // Add item elements to list item
                    listItem.appendChild(priorityIndicator);
                    listItem.appendChild(itemDetails);
                    
                    // Add list item to list
                    list.appendChild(listItem);
                });
                
                contentsElement.appendChild(list);
            } else {
                contentsElement.innerHTML = '<div class="alert alert-secondary">This container is empty.</div>';
            }
        } else {
            const errorMsg = data.error || 'Unknown error occurred';
            console.error('Error fetching container data:', errorMsg);
            showToast(`Error: ${errorMsg}`, 'danger');
            
            // Update container info with error message
            document.getElementById('containerIdDisplay').textContent = containerId;
            document.getElementById('containerZoneDisplay').textContent = 'Error';
            document.getElementById('containerSizeDisplay').textContent = 'Error loading container data';
            document.getElementById('containerContents').innerHTML = '<div class="alert alert-danger">Error loading container data. Please try again.</div>';
        }
    } catch (error) {
        console.error('Error viewing container details:', error);
        showToast('Error loading container details. Please try again.', 'danger');
        
        // Update container info with error message
        document.getElementById('containerIdDisplay').textContent = containerId;
        document.getElementById('containerZoneDisplay').textContent = 'Error';
        document.getElementById('containerSizeDisplay').textContent = 'Error loading container data';
        document.getElementById('containerContents').innerHTML = '<div class="alert alert-danger">Error loading container data. Please try again.</div>';
    }
}
