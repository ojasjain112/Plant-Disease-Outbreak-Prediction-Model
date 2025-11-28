// Map initialization and interaction using Leaflet.js

let map;
let marker;

// Initialize the map
function initMap() {
    // Create map centered on a default location (can be changed)
    map = L.map('map').setView([20.0, 0.0], 2);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // Add click event listener
    map.on('click', onMapClick);

    // Try to get user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                map.setView([lat, lon], 10);
                addMarker(lat, lon);
            },
            function (error) {
                console.log('Geolocation error:', error);
            }
        );
    }
}

// Handle map click
function onMapClick(e) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;

    addMarker(lat, lon);
}

// Add or update marker on the map
function addMarker(lat, lon) {
    // Remove existing marker if any
    if (marker) {
        map.removeLayer(marker);
    }

    // Add new marker
    marker = L.marker([lat, lon]).addTo(map);

    // Update form fields
    document.getElementById('latitude').value = lat.toFixed(4);
    document.getElementById('longitude').value = lon.toFixed(4);

    // Add popup
    marker.bindPopup(`<b>Selected Location</b><br>Lat: ${lat.toFixed(4)}<br>Lon: ${lon.toFixed(4)}`).openPopup();
}

// Allow manual coordinate entry to update map
function setupCoordinateInputs() {
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');

    function updateMapFromInputs() {
        const lat = parseFloat(latInput.value);
        const lon = parseFloat(lonInput.value);

        if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
            map.setView([lat, lon], 10);
            addMarker(lat, lon);
        }
    }

    latInput.addEventListener('change', updateMapFromInputs);
    lonInput.addEventListener('change', updateMapFromInputs);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        initMap();
        setupCoordinateInputs();
    });
} else {
    initMap();
    setupCoordinateInputs();
}
