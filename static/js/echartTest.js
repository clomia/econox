const host = window.location.origin;

async function fetchData(url) {
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
}

async function renderEchart(symbol) {
    const url = `${host}/echart/data?element=${symbol}&factor=price.adj_close`;
    const data = await fetchData(url);

    const chartDom = document.getElementById('echart-test');
    const myChart = echarts.init(chartDom);

    const option = {
        title: {
            text: symbol
        },
        tooltip: {},
        legend: {
            data: ['price']
        },
        xAxis: {
            data: data.t
        },
        yAxis: {},
        series: [{
            name: 'price',
            type: 'line',
            data: data.values
        }]
    };

    myChart.setOption(option);
}

const input = document.getElementById("symbolInput");

input.addEventListener("keydown", function (event) {
    // 'Enter' 키가 눌렸는지 확인합니다.
    if (event.key === "Enter") {
        // 'Enter' 키가 눌렸을 때의 동작
        renderEchart(input.value);
    }
});




