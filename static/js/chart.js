// Chart visualization using Chart.js

let riskChart = null;

// Create risk probability chart
function createRiskChart(riskData) {
    try {
        console.log('createRiskChart called with:', riskData);

        const canvas = document.getElementById('risk-chart');
        if (!canvas) {
            throw new Error('Canvas element "risk-chart" not found');
        }

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            throw new Error('Could not get 2D context from canvas');
        }

        // Destroy existing chart if any
        if (riskChart) {
            riskChart.destroy();
        }

        // Prepare data
        const labels = riskData.map(d => `Day ${d.day}`);
        const probabilities = riskData.map(d => d.probability);
        const colors = riskData.map(d => {
            if (d.alert === 'low') return 'rgba(39, 174, 96, 0.7)';
            if (d.alert === 'medium') return 'rgba(243, 156, 18, 0.7)';
            return 'rgba(231, 76, 60, 0.7)';
        });
        const borderColors = riskData.map(d => {
            if (d.alert === 'low') return 'rgba(39, 174, 96, 1)';
            if (d.alert === 'medium') return 'rgba(243, 156, 18, 1)';
            return 'rgba(231, 76, 60, 1)';
        });

        // Create chart
        riskChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Outbreak Probability',
                    data: probabilities,
                    backgroundColor: colors,
                    borderColor: borderColors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const index = context.dataIndex;
                                const alert = riskData[index].alert;
                                return [
                                    `Probability: ${(context.parsed.y * 100).toFixed(1)}%`,
                                    `Risk Level: ${alert.toUpperCase()}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function (value) {
                                return (value * 100).toFixed(0) + '%';
                            }
                        },
                        title: {
                            display: true,
                            text: 'Outbreak Probability'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Forecast Day'
                        }
                    }
                }
            }
        });

        console.log('Chart created successfully');
    } catch (error) {
        console.error('Error creating chart:', error);
        throw error;
    }
}

// Create line chart for weather trends (optional enhancement)
function createWeatherTrendChart(weatherData) {
    // This can be implemented for showing weather trends
    // Left as an enhancement for future development
}

// Update chart with new data
function updateRiskChart(riskData) {
    createRiskChart(riskData);
}
