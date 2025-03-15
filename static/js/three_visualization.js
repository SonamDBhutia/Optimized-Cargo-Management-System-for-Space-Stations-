// Three.js visualization for Space Station Cargo Management System

// Global three.js variables
let scene, camera, renderer, controls;
let containerMesh, itemMeshes = {};
let raycaster, mouse;
let highlightedItemId = null;

// Initialize the container visualization
function initializeContainerVisualization(containerId, highlightItemId = null) {
    // If highlightItemId is provided, we'll highlight that item initially
    highlightedItemId = highlightItemId;
    
    // Get the container element
    const containerElement = document.getElementById('containerVisualization');
    
    // Clear any existing content
    while (containerElement.firstChild) {
        containerElement.removeChild(containerElement.firstChild);
    }
    
    // Initialize the scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    
    // Set up camera
    const width = containerElement.clientWidth;
    const height = containerElement.clientHeight;
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(200, 200, 200);
    
    // Set up renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    containerElement.appendChild(renderer.domElement);
    
    // Set up orbit controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    
    // Set up raycaster for mouse interaction
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();
    
    // Add event listener for mouse moves to enable hover effects
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    
    // Add event listener for click events to select items
    renderer.domElement.addEventListener('click', onMouseClick);
    
    // Add window resize handler
    window.addEventListener('resize', onWindowResize);
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);
    
    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(100, 100, 100);
    directionalLight.castShadow = true;
    scene.add(directionalLight);
    
    // Add a point light inside the container
    const pointLight = new THREE.PointLight(0xffffff, 0.5);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);
    
    // Add a grid helper
    const gridHelper = new THREE.GridHelper(500, 50);
    scene.add(gridHelper);
    
    // Fetch container data and render
    fetchContainerDataAndRender(containerId);
    
    // Start animation loop
    animate();
}

// Fetch container data and render the container with its items
async function fetchContainerDataAndRender(containerId) {
    try {
        const response = await fetch(`/api/containers/${containerId}`);
        const data = await response.json();
        
        if (data.success) {
            const container = data.data;
            
            // Render container
            renderContainer(container);
            
            // Render items
            if (container.items && container.items.length > 0) {
                container.items.forEach(item => {
                    renderItem(item, container);
                });
            }
            
            // If we have a highlighted item, make it blink
            if (highlightedItemId) {
                highlightItem(highlightedItemId);
            }
        } else {
            console.error('Error fetching container data:', data.error);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Render the container as a wireframe box
function renderContainer(container) {
    // Container dimensions
    const width = container.width;
    const depth = container.depth;
    const height = container.height;
    
    // Create a wireframe box geometry
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const wireframe = new THREE.EdgesGeometry(geometry);
    const material = new THREE.LineBasicMaterial({ color: 0x4080ff, linewidth: 2 });
    containerMesh = new THREE.LineSegments(wireframe, material);
    
    // Position the container so its bottom center is at the origin
    containerMesh.position.set(width / 2, height / 2, depth / 2);
    
    // Add to scene
    scene.add(containerMesh);
    
    // Create a helper to show the open face
    const openFaceGeometry = new THREE.PlaneGeometry(width, height);
    const openFaceMaterial = new THREE.MeshBasicMaterial({ 
        color: 0x4080ff, 
        transparent: true, 
        opacity: 0.1,
        side: THREE.DoubleSide
    });
    const openFaceMesh = new THREE.Mesh(openFaceGeometry, openFaceMaterial);
    openFaceMesh.position.set(width / 2, height / 2, 0);
    scene.add(openFaceMesh);
    
    // Add container label
    const textOptions = {
        font: 'bold 12px Arial',
        fillStyle: 'white',
        textAlign: 'center'
    };
    
    // Center camera on container
    controls.target.set(width / 2, height / 2, depth / 2);
    controls.update();
}

// Render an item as a colored box with label
function renderItem(item, container) {
    if (!item.x_pos || !item.y_pos || !item.z_pos) {
        return; // Skip items without position
    }
    
    // Get item dimensions
    const width = item.rotated ? item.depth : item.width;
    const depth = item.rotated ? item.width : item.depth;
    const height = item.height;
    
    // Create geometry
    const geometry = new THREE.BoxGeometry(width, height, depth);
    
    // Create material based on item properties
    let color;
    if (item.is_waste) {
        color = 0xff0000; // Red for waste
    } else if (item.is_expired) {
        color = 0xff9900; // Orange for expired
    } else {
        // Color based on priority
        if (item.priority >= 80) {
            color = 0x00ff00; // Green for high priority
        } else if (item.priority >= 50) {
            color = 0xffff00; // Yellow for medium priority
        } else {
            color = 0x0099ff; // Blue for low priority
        }
    }
    
    const material = new THREE.MeshLambertMaterial({ 
        color: color, 
        transparent: true, 
        opacity: 0.8 
    });
    
    // Create mesh
    const mesh = new THREE.Mesh(geometry, material);
    
    // Position the mesh
    mesh.position.set(
        item.x_pos + width / 2, 
        item.z_pos + height / 2, 
        item.y_pos + depth / 2
    );
    
    // Add to scene
    scene.add(mesh);
    
    // Store the item mesh with its data for interaction
    itemMeshes[item.id] = {
        mesh: mesh,
        item: item,
        originalColor: color,
        highlighted: false
    };
    
    // Add wireframe to show edges
    const edgesGeometry = new THREE.EdgesGeometry(geometry);
    const edgesMaterial = new THREE.LineBasicMaterial({ color: 0x000000 });
    const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
    mesh.add(edges);
}

// Handle window resize
function onWindowResize() {
    const containerElement = document.getElementById('containerVisualization');
    const width = containerElement.clientWidth;
    const height = containerElement.clientHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// Handle mouse movements for hover effects
function onMouseMove(event) {
    // Calculate mouse position in normalized device coordinates
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

// Handle mouse click events
function onMouseClick(event) {
    // Update the mouse position
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    
    // Update the picking ray with the camera and mouse position
    raycaster.setFromCamera(mouse, camera);
    
    // Calculate objects intersecting the picking ray
    const intersects = [];
    
    for (const itemId in itemMeshes) {
        const itemObj = itemMeshes[itemId];
        const intersectedObjects = raycaster.intersectObject(itemObj.mesh, true);
        
        if (intersectedObjects.length > 0) {
            intersects.push({
                object: itemObj.mesh,
                itemId: itemId,
                distance: intersectedObjects[0].distance
            });
        }
    }
    
    // Sort intersects by distance
    intersects.sort((a, b) => a.distance - b.distance);
    
    // Handle clicks on items
    if (intersects.length > 0) {
        const clickedItemId = intersects[0].itemId;
        highlightItem(clickedItemId);
        
        // Show item info in panel
        displayItemInfo(clickedItemId);
    } else {
        // Clear any highlighted item
        clearHighlights();
    }
}

// Highlight a specific item
function highlightItem(itemId) {
    // Clear previous highlights
    clearHighlights();
    
    // If we have this item, highlight it
    if (itemMeshes[itemId]) {
        const itemObj = itemMeshes[itemId];
        
        // Store original color if not already stored
        if (!itemObj.originalColor) {
            itemObj.originalColor = itemObj.mesh.material.color.getHex();
        }
        
        // Set highlighted status
        itemObj.highlighted = true;
        highlightedItemId = itemId;
        
        // Setup highlight animation
        animateHighlight();
    }
}

// Highlight an item from outside the visualization
function highlightItemInVisualization(itemId) {
    highlightItem(itemId);
}

// Clear all highlights
function clearHighlights() {
    for (const itemId in itemMeshes) {
        const itemObj = itemMeshes[itemId];
        
        if (itemObj.highlighted) {
            // Reset to original color
            itemObj.mesh.material.color.setHex(itemObj.originalColor);
            itemObj.highlighted = false;
        }
    }
    
    highlightedItemId = null;
}

// Animate the highlight effect
function animateHighlight() {
    if (!highlightedItemId || !itemMeshes[highlightedItemId]) return;
    
    const itemObj = itemMeshes[highlightedItemId];
    
    // Only animate if this item is still highlighted
    if (itemObj.highlighted) {
        // Oscillate the color between white and the original color
        const time = Date.now() * 0.001; // convert to seconds
        const intensity = (Math.sin(time * 5) + 1) / 2; // oscillate between 0 and 1
        
        const originalColor = new THREE.Color(itemObj.originalColor);
        const highlightColor = new THREE.Color(0xffffff);
        
        // Interpolate between original and highlight color
        const color = originalColor.clone().lerp(highlightColor, intensity);
        itemObj.mesh.material.color.copy(color);
        
        // Continue animation in the next frame
        requestAnimationFrame(animateHighlight);
    }
}

// Display detailed item info in the sidebar
function displayItemInfo(itemId) {
    if (!itemMeshes[itemId]) return;
    
    const item = itemMeshes[itemId].item;
    
    // Get all items in the container
    const items = document.querySelectorAll('#containerContents .list-group-item');
    
    // Remove active class from all items
    items.forEach(el => {
        el.classList.remove('active');
    });
    
    // Find the list item for this item and highlight it
    items.forEach(el => {
        const nameElement = el.querySelector('div');
        if (nameElement && nameElement.textContent.includes(item.name)) {
            el.classList.add('active');
            el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    
    // Update controls
    controls.update();
    
    // Handle hover effects
    raycaster.setFromCamera(mouse, camera);
    
    // Find intersections
    const intersectedObjects = [];
    for (const itemId in itemMeshes) {
        const itemObj = itemMeshes[itemId];
        
        // Skip already highlighted items
        if (itemObj.highlighted) continue;
        
        const intersects = raycaster.intersectObject(itemObj.mesh, true);
        
        if (intersects.length > 0) {
            intersectedObjects.push({
                object: itemObj.mesh,
                item: itemObj.item,
                itemId: itemId,
                distance: intersects[0].distance
            });
        } else {
            // Reset color if not highlighted
            itemObj.mesh.material.color.setHex(itemObj.originalColor);
            itemObj.mesh.material.opacity = 0.8;
        }
    }
    
    // Sort by distance to camera
    intersectedObjects.sort((a, b) => a.distance - b.distance);
    
    // Highlight the closest object
    if (intersectedObjects.length > 0 && !highlightedItemId) {
        const closestObj = intersectedObjects[0];
        closestObj.object.material.color.setHex(0xffff00); // Yellow hover effect
        closestObj.object.material.opacity = 0.9;
    }
    
    // Render scene
    renderer.render(scene, camera);
}
