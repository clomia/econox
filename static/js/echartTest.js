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

async function renderEchart(symbols) {
    const url = `${host}/echart/data?elements=${symbols}`
    const [sym1, sym2, sym3, sym4] = await fetchData(url);

    const chartDom = document.getElementById('echart-test');
    const myChart = echarts.init(chartDom);

    const option = {
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: [sym1.name, sym2.name, sym3.name, sym4.name]
        },
        xAxis: {
            type: 'category',
            data: sym1.t
        },
        yAxis: {
            type: 'value'
        },
        series: [
            {
                name: sym1.name,
                type: 'line',
                data: sym1.values
            },
            {
                name: sym2.name,
                type: 'line',
                data: sym2.values
            },
            {
                name: sym3.name,
                type: 'line',
                data: sym3.values
            },
            {
                name: sym4.name,
                type: 'line',
                data: sym4.values
            }
        ]
    };

    myChart.setOption(option);
}

const btn = document.getElementById("symbolInputBtn");

const input1 = document.getElementById("symbolInput1");
const input2 = document.getElementById("symbolInput2");
const input3 = document.getElementById("symbolInput3");
const input4 = document.getElementById("symbolInput4");

btn.addEventListener("click", function (event) {
    renderEchart(`${input1.value},${input2.value},${input3.value},${input4.value}`);
});




