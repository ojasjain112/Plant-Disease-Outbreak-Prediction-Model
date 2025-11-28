// Main application logic

// Handle form submission
document.getElementById('prediction-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    // Get form data
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const disease = document.getElementById('disease').value;

    // Get selected lead days
    const leadDaysCheckboxes = document.querySelectorAll('input[name="lead_days"]:checked');
    const leadDays = Array.from(leadDaysCheckboxes).map(cb => parseInt(cb.value));

    // Validate
    if (isNaN(latitude) || isNaN(longitude)) {
        showError('Please select a valid location on the map.');
        return;
    }

    if (leadDays.length === 0) {
        showError('Please select at least one forecast day.');
        return;
    }

    // Show loading
    showLoading();

    // Prepare request payload
    const payload = {
        latitude: latitude,
        longitude: longitude,
        lead_days: leadDays,
        disease: disease
    };

    console.log('Sending payload:', payload);

    try {
        // Make API request
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        console.log('Response status:', response.status);

        const data = await response.json();
        console.log('Response data:', data);

        if (response.ok && data.status === 'ok') {
            displayResults(data);
        } else {
            showError(data.message || 'Prediction failed. Please try again.');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Network error. Please check your connection and try again.');
    }
});

// Show loading state
function showLoading() {
    document.querySelector('.dashboard-grid').style.display = 'none';
    document.getElementById('loading-section').classList.remove('hidden');
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('error-section').classList.add('hidden');

    // Animate loading steps
    animateLoadingSteps();
}

// Animate loading steps
function animateLoadingSteps() {
    const steps = document.querySelectorAll('.step');
    let currentStep = 0;

    const interval = setInterval(() => {
        if (currentStep > 0) {
            steps[currentStep - 1].classList.remove('active');
        }
        if (currentStep < steps.length) {
            steps[currentStep].classList.add('active');
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

// Display results
function displayResults(data) {
    try {
        console.log('Displaying results with data:', data);

        // Hide loading
        document.getElementById('loading-section').classList.add('hidden');

        // Show results section
        const resultsSection = document.getElementById('results-section');
        resultsSection.classList.remove('hidden');

        // Update location info
        document.getElementById('result-coords').textContent =
            `${data.location.lat.toFixed(4)}, ${data.location.lon.toFixed(4)}`;
        document.getElementById('result-disease').textContent =
            formatDiseaseName(data.disease) || 'Not specified';

        // Create chart
        console.log('Creating chart...');
        createRiskChart(data.risk_by_day);

        // Populate table
        console.log('Populating table...');
        populateRiskTable(data.risk_by_day, data.top_features_by_day);

        // Display weather summary
        console.log('Displaying weather summary...');
        displayWeatherSummary(data.weather_summary);

        // Display detailed weather parameters
        console.log('Displaying weather parameters...');
        displayWeatherParameters(data.weather_parameters);

        // Display feature statistics
        console.log('Displaying feature statistics...');
        displayFeatureStatistics(data.feature_statistics);

        // Show success notification
        showSuccessNotification();

        // Scroll to results (with a small delay to ensure rendering is complete)
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // Additional scroll fallback
            const yOffset = resultsSection.getBoundingClientRect().top + window.pageYOffset - 20;
            window.scrollTo({ top: yOffset, behavior: 'smooth' });
        }, 100);

        console.log('Results displayed successfully!');
    } catch (error) {
        console.error('Error in displayResults:', error);
        showError('Failed to display results: ' + error.message);
    }
}

// Populate risk table
function populateRiskTable(riskData, topFeatures) {
    const tbody = document.getElementById('risk-table-body');
    tbody.innerHTML = '';

    riskData.forEach(day => {
        const row = document.createElement('tr');

        // Day
        const dayCell = document.createElement('td');
        dayCell.textContent = `Day ${day.day}`;
        row.appendChild(dayCell);

        // Probability
        const probCell = document.createElement('td');
        probCell.textContent = `${(day.probability * 100).toFixed(1)}%`;
        row.appendChild(probCell);

        // Risk level with badge
        const riskCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = `risk-badge risk-${day.alert}`;
        badge.textContent = day.alert.toUpperCase();
        riskCell.appendChild(badge);
        row.appendChild(riskCell);

        // Top features
        const featuresCell = document.createElement('td');
        const features = topFeatures[day.day.toString()] || day.top_features || [];
        const featureList = document.createElement('div');
        featureList.className = 'feature-list';

        features.slice(0, 3).forEach(feature => {
            const tag = document.createElement('span');
            tag.className = 'feature-tag';
            tag.textContent = formatFeatureName(feature);
            featureList.appendChild(tag);
        });

        featuresCell.appendChild(featureList);
        row.appendChild(featuresCell);

        tbody.appendChild(row);
    });
}

// Display weather summary
function displayWeatherSummary(summary) {
    const container = document.getElementById('weather-summary-content');
    container.innerHTML = '';

    if (!summary || Object.keys(summary).length === 0) {
        container.innerHTML = '<p style="text-align:center; color:var(--text-medium);">Weather summary not available.</p>';
        return;
    }

    // Temperature
    if (summary.temperature) {
        addWeatherStatCard(container, 'Temperature',
            `Avg: ${summary.temperature.mean}°C | Min: ${summary.temperature.min}°C | Max: ${summary.temperature.max}°C`,
            'thermometer-half');
    }

    // Humidity
    if (summary.humidity) {
        addWeatherStatCard(container, 'Humidity',
            `Average: ${summary.humidity.mean}%`,
            'tint');
    }

    // Precipitation
    if (summary.precipitation) {
        addWeatherStatCard(container, 'Precipitation',
            `Total: ${summary.precipitation.total} mm`,
            'cloud-rain');
    }

    // Wind Speed
    if (summary.wind_speed) {
        addWeatherStatCard(container, 'Wind Speed',
            `Avg: ${summary.wind_speed.mean} km/h | Max: ${summary.wind_speed.max} km/h`,
            'wind');
    }
}

// Add weather stat card
function addWeatherStatCard(container, label, value, icon) {
    const stat = document.createElement('div');
    stat.className = 'weather-stat';

    const iconElement = document.createElement('i');
    iconElement.className = `fas fa-${icon}`;
    iconElement.style.fontSize = '1.5rem';
    iconElement.style.color = 'var(--primary-color)';
    iconElement.style.marginBottom = '8px';

    const labelSpan = document.createElement('strong');
    labelSpan.textContent = label;

    const valueSpan = document.createElement('span');
    valueSpan.textContent = value;

    stat.appendChild(iconElement);
    stat.appendChild(labelSpan);
    stat.appendChild(valueSpan);
    container.appendChild(stat);
}

// Display detailed weather parameters
function displayWeatherParameters(parameters) {
    const container = document.getElementById('parameters-content');
    container.innerHTML = '';

    if (!parameters || Object.keys(parameters).length === 0) {
        container.innerHTML = '<p style="text-align:center; color:var(--text-medium); padding:20px;">Weather parameters not available.</p>';
        return;
    }

    const categoryInfo = {
        'temperature': { title: 'Temperature Variables', icon: 'thermometer-half', color: '#ef4444' },
        'humidity_moisture': { title: 'Humidity & Soil Moisture', icon: 'tint', color: '#3b82f6' },
        'precipitation': { title: 'Precipitation', icon: 'cloud-rain', color: '#06b6d4' },
        'wind': { title: 'Wind', icon: 'wind', color: '#8b5cf6' },
        'pressure': { title: 'Atmospheric Pressure', icon: 'compress-arrows-alt', color: '#f59e0b' },
        'cloud_radiation': { title: 'Cloud Cover & Radiation', icon: 'sun', color: '#fbbf24' },
        'evapotranspiration': { title: 'Evapotranspiration', icon: 'water', color: '#10b981' },
        'atmospheric': { title: 'Atmospheric Conditions', icon: 'cloud', color: '#6366f1' }
    };

    Object.entries(parameters).forEach(([category, params]) => {
        if (Object.keys(params).length === 0) return;

        const info = categoryInfo[category] || { title: category, icon: 'chart-line', color: '#667eea' };

        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'parameter-category';
        categoryDiv.style.borderLeftColor = info.color;

        const header = document.createElement('h4');
        header.innerHTML = `<i class="fas fa-${info.icon}" style="color: ${info.color}"></i> ${info.title}`;
        categoryDiv.appendChild(header);

        Object.entries(params).forEach(([paramName, stats]) => {
            if (!stats) return;

            const paramDiv = document.createElement('div');
            paramDiv.className = 'parameter-item';

            const name = document.createElement('div');
            name.className = 'param-name';
            name.innerHTML = `<i class="fas fa-circle" style="font-size: 6px; color: ${info.color}"></i> ${formatParameterName(paramName)}`;
            paramDiv.appendChild(name);

            const statsDiv = document.createElement('div');
            statsDiv.className = 'param-stats';

            if (stats.current !== undefined && stats.current !== null) {
                addStatItem(statsDiv, 'Current', formatValue(stats.current, paramName));
            }
            if (stats.mean !== undefined && stats.mean !== null) {
                addStatItem(statsDiv, 'Average', formatValue(stats.mean, paramName));
            }
            if (stats.min !== undefined && stats.min !== null) {
                addStatItem(statsDiv, 'Min', formatValue(stats.min, paramName));
            }
            if (stats.max !== undefined && stats.max !== null) {
                addStatItem(statsDiv, 'Max', formatValue(stats.max, paramName));
            }

            paramDiv.appendChild(statsDiv);
            categoryDiv.appendChild(paramDiv);
        });

        container.appendChild(categoryDiv);
    });
}

// Add stat item to parameter display
function addStatItem(container, label, value) {
    const item = document.createElement('div');
    item.className = 'stat-item';

    const labelSpan = document.createElement('span');
    labelSpan.className = 'stat-label';
    labelSpan.textContent = label + ':';

    const valueSpan = document.createElement('span');
    valueSpan.className = 'stat-value';
    valueSpan.textContent = value;

    item.appendChild(labelSpan);
    item.appendChild(valueSpan);
    container.appendChild(item);
}

// Format parameter name for display
function formatParameterName(name) {
    return name
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Format value with appropriate units
function formatValue(value, paramName) {
    if (value === null || value === undefined) return 'N/A';

    const name = paramName.toLowerCase();

    if (name.includes('temperature')) return `${value}°C`;
    if (name.includes('humidity') || name.includes('moisture') || name.includes('cloud_cover')) return `${value}%`;
    if (name.includes('precipitation') || name.includes('rain') || name.includes('snow')) return `${value} mm`;
    if (name.includes('wind_speed') || name.includes('wind_gust')) return `${value} km/h`;
    if (name.includes('wind_direction')) return `${value}°`;
    if (name.includes('pressure')) return `${value} hPa`;
    if (name.includes('radiation') || name.includes('irradiance')) return `${value} W/m²`;
    if (name.includes('evapotranspiration')) return `${value} mm`;
    if (name.includes('visibility')) return `${value} m`;
    if (name.includes('vpd') || name.includes('vapour_pressure')) return `${value} kPa`;
    if (name.includes('cape')) return `${value} J/kg`;
    if (name.includes('height')) return `${value} m`;
    if (name.includes('duration')) return `${value} s`;

    return value;
}

// Display feature statistics
function displayFeatureStatistics(stats) {
    const container = document.getElementById('features-content');
    container.innerHTML = '';

    if (!stats || !stats.total_features) {
        container.innerHTML = '<p style="text-align:center; color:var(--text-medium); padding:20px;">Feature statistics not available.</p>';
        return;
    }

    // Add summary statistics
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'stats-summary';
    summaryDiv.innerHTML = `
        <div class="stat-box">
            <div class="stat-box-value">${stats.total_features}</div>
            <div class="stat-box-label">Total Features</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.feature_types.rolling_window || 0}</div>
            <div class="stat-box-label">Rolling Window</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.feature_types.lag || 0}</div>
            <div class="stat-box-label">Lag Features</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.feature_types.delta || 0}</div>
            <div class="stat-box-label">Delta Features</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.feature_types.interaction || 0}</div>
            <div class="stat-box-label">Interactions</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.feature_types.disease_specific || 0}</div>
            <div class="stat-box-label">Disease-Specific</div>
        </div>
    `;
    container.appendChild(summaryDiv);

    // Add feature type categories
    const categoriesDiv = document.createElement('div');
    categoriesDiv.style.display = 'grid';
    categoriesDiv.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
    categoriesDiv.style.gap = '20px';
    categoriesDiv.style.marginTop = '20px';

    const featureTypeInfo = {
        'rolling': { title: 'Rolling Window Features', icon: 'chart-line', description: 'Statistical aggregations over time windows (3h, 6h, 12h, 24h, 48h, 72h)', color: '#3b82f6' },
        'lag': { title: 'Lag Features', icon: 'clock', description: 'Historical values from past time periods', color: '#8b5cf6' },
        'delta': { title: 'Delta Features', icon: 'exchange-alt', description: 'Rate of change calculations over time', color: '#10b981' },
        'interaction': { title: 'Interaction Features', icon: 'project-diagram', description: 'Combined effects of multiple variables', color: '#f59e0b' },
        'disease_specific': { title: 'Disease-Specific Features', icon: 'leaf', description: 'Calculated indices for plant disease risk (VPD, leaf wetness, etc.)', color: '#ef4444' }
    };

    Object.entries(stats.sample_features || {}).forEach(([type, features]) => {
        if (!features || features.length === 0) return;

        const info = featureTypeInfo[type] || { title: type, icon: 'cog', description: '', color: '#667eea' };

        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'feature-category';
        categoryDiv.style.borderLeftColor = info.color;

        const header = document.createElement('h4');
        header.innerHTML = `
            <i class="fas fa-${info.icon}" style="color: ${info.color}"></i>
            ${info.title}
            <span class="feature-count">${stats.feature_types[type === 'disease_specific' ? 'disease_specific' : type] || features.length}</span>
        `;
        categoryDiv.appendChild(header);

        const description = document.createElement('p');
        description.style.fontSize = '0.85rem';
        description.style.color = 'var(--text-medium)';
        description.style.marginBottom = '12px';
        description.textContent = info.description;
        categoryDiv.appendChild(description);

        const samplesDiv = document.createElement('div');
        samplesDiv.className = 'feature-samples';

        const samplesLabel = document.createElement('div');
        samplesLabel.style.fontSize = '0.8rem';
        samplesLabel.style.fontWeight = '600';
        samplesLabel.style.color = 'var(--text-dark)';
        samplesLabel.style.marginBottom = '8px';
        samplesLabel.textContent = 'Sample Features:';
        samplesDiv.appendChild(samplesLabel);

        features.forEach(feature => {
            const tag = document.createElement('span');
            tag.className = 'feature-tag-small';
            tag.textContent = feature.length > 40 ? feature.substring(0, 37) + '...' : feature;
            tag.title = feature;
            samplesDiv.appendChild(tag);
        });

        categoryDiv.appendChild(samplesDiv);
        categoriesDiv.appendChild(categoryDiv);
    });

    container.appendChild(categoriesDiv);
}

// Toggle buttons for parameters and features
document.addEventListener('DOMContentLoaded', function () {
    setupToggleButtons();
});

function setupToggleButtons() {
    const toggleParameters = document.getElementById('toggle-parameters');
    const toggleFeatures = document.getElementById('toggle-features');
    const parametersContent = document.getElementById('parameters-content');
    const featuresContent = document.getElementById('features-content');

    if (toggleParameters && parametersContent) {
        toggleParameters.addEventListener('click', function () {
            parametersContent.classList.toggle('hidden');
            this.classList.toggle('active');
            const textSpan = this.querySelector('span');
            if (parametersContent.classList.contains('hidden')) {
                textSpan.textContent = 'Show Details';
            } else {
                textSpan.textContent = 'Hide Details';
            }
        });
    }

    if (toggleFeatures && featuresContent) {
        toggleFeatures.addEventListener('click', function () {
            featuresContent.classList.toggle('hidden');
            this.classList.toggle('active');
            const textSpan = this.querySelector('span');
            if (featuresContent.classList.contains('hidden')) {
                textSpan.textContent = 'Show Details';
            } else {
                textSpan.textContent = 'Hide Details';
            }
        });
    }
}

// Add weather stat card
function addWeatherStatCard(container, label, value, icon) {
    const stat = document.createElement('div');
    stat.className = 'weather-stat';

    const iconElement = document.createElement('i');
    iconElement.className = `fas fa-${icon}`;
    iconElement.style.fontSize = '1.5rem';
    iconElement.style.color = 'var(--primary-color)';
    iconElement.style.marginBottom = '8px';

    const labelSpan = document.createElement('strong');
    labelSpan.textContent = label;

    const valueSpan = document.createElement('span');
    valueSpan.textContent = value;

    stat.appendChild(iconElement);
    stat.appendChild(labelSpan);
    stat.appendChild(valueSpan);
    container.appendChild(stat);
}

// Show success notification
function showSuccessNotification() {
    // Create notification banner
    const banner = document.createElement('div');
    banner.className = 'success-banner';
    banner.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>Prediction complete! Scroll down to view results.</span>
    `;

    document.body.appendChild(banner);

    // Remove after 4 seconds
    setTimeout(() => {
        banner.style.opacity = '0';
        banner.style.transition = 'opacity 0.5s ease';
        setTimeout(() => banner.remove(), 500);
    }, 4000);
}

// Format disease name for display
function formatDiseaseName(disease) {
    if (!disease) return '';
    // Replace underscores with spaces and capitalize each word
    return disease
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

// Format feature name for display
function formatFeatureName(feature) {
    // Remove underscores and capitalize
    return feature
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

// Show error message
function showError(message) {
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('results-section').classList.add('hidden');

    const errorSection = document.getElementById('error-section');
    errorSection.classList.remove('hidden');

    document.getElementById('error-message-text').textContent = message;

    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Reset button handlers
document.getElementById('reset-btn').addEventListener('click', resetForm);
document.getElementById('error-reset-btn').addEventListener('click', resetForm);

function resetForm() {
    // Hide results and error
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('error-section').classList.add('hidden');

    // Show dashboard grid
    document.querySelector('.dashboard-grid').style.display = 'grid';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Keyboard navigation support
document.addEventListener('keydown', function (e) {
    // Allow Escape key to reset
    if (e.key === 'Escape') {
        const resultsVisible = document.getElementById('results-section').style.display !== 'none';
        const errorVisible = document.getElementById('error-section').style.display !== 'none';

        if (resultsVisible || errorVisible) {
            resetForm();
        }
    }
});
