const chartMap = {
    line: 'line',
    scatter: 'scatter',
    boxplot: 'boxplot',
    heatmap: 'matrix',
    bar:'bar'
};

const violet = 'rgba(139, 92, 246, 0.8)';
const violetLight = 'rgba(139, 92, 246, 0.3)';

const responses = {{ openai_response | tojson }};

responses.forEach((res, index) => {
    const ctx = document.getElementById(`chart_${index + 1}`).getContext('2d');

    // Safely get first result metric dynamically
    const metricKey = Object.keys(res.result)[0];
    const dataObj = res.result[metricKey];

    const chartType = chartMap[res.chart_type.toLowerCase()] || 'line';

    // Decide chart renderer
    if (chartType === 'matrix' && Chart.registry.controllers.get('matrix')) {
        renderHeatmap(ctx, dataObj);
    } else if (chartType === 'boxplot' && Chart.registry.controllers.get('boxplot')) {
        renderBoxplot(ctx, dataObj);
    } else if (chartType === 'scatter') {
        renderScatter(ctx, dataObj, metricKey);
    } else if (chartType === 'bar') {
        renderBar(ctx, dataObj, metricKey);
    } else {
        renderLine(ctx, dataObj, metricKey);
    }
});


// -------------------- RENDER FUNCTIONS --------------------

function renderLine(ctx, dataObj, metricKey) {
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.keys(dataObj),
            datasets: [{
                label: metricKey,
                data: Object.values(dataObj),
                backgroundColor: violet,
                borderColor: violet,
                borderWidth: 2,
                fill: false,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderBoxplot(ctx, dataObj) {
    const labels = Object.keys(dataObj);
    const datasets = [{
        label: 'Boxplot',
        data: Object.values(dataObj), // should be array of arrays
        backgroundColor: violet
    }];
    new Chart(ctx, { type: 'boxplot', data: { labels, datasets }, options: { responsive: true } });
}


function renderScatter(ctx, dataObj, metricKey) {
        let flatData = [];
        let i = 0; // numeric x-axis index

        Object.entries(dataObj).forEach(([x, y]) => {
            if (typeof y === 'object' && y !== null) {
                Object.entries(y).forEach(([innerX, innerY]) => {
                    const yVal = Number(innerY);
                    if (!isNaN(yVal)) {
                        flatData.push({ x: i++, y: yVal, label: innerX });
                    }
                });
            } else {
                const yVal = Number(y);
                if (!isNaN(yVal)) {
                    flatData.push({ x: i++, y: yVal, label: x });
                }
            }
        });

        new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: metricKey,
                    data: flatData,
                    backgroundColor: 'rgba(139, 92, 246, 0.8)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.raw.label}: ${context.raw.y}`;
                            }
                        }
                    }
                },
                scales: {
                    x: { type: 'linear', title: { display: true, text: 'Index' } },
                    y: { beginAtZero: true }
                }
            }
        });
    }

function renderHeatmap(ctx, dataObj) {
    const labels = Object.keys(dataObj);
    const values = Object.values(dataObj);
    const matrixData = labels.map((label, i) => ({ x: label, y: 'Metric', v: values[i] }));

    new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                label: 'Heatmap',
                data: matrixData,
                backgroundColor: ctx => `rgba(139, 92, 246, ${ctx.raw.v / 100})`,
                width: 40,
                height: 40,
                borderWidth: 1,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: { type: 'category', offset: true },
                y: { type: 'category', offset: true }
            },
            plugins: { legend: { display: false } }
        }
    });
}
function renderBar(ctx, dataObj, metricKey) {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(dataObj),
                datasets: [{
                    label: metricKey,
                    data: Object.values(dataObj),
                    backgroundColor: violet,
                    borderColor: violet,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: true } },
                scales: { y: { beginAtZero: true } }
            }
        });
}