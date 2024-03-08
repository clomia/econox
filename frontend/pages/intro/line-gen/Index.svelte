<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { data } from "./data";

  export let height: string;
  export let width: string;

  let chartContainer: HTMLElement;

  const colormap = {
    a: "rgb(122,255,251)",
    b: "rgb(255,217,97)",
    c: "rgb(252,94,94)",
    d: "rgb(80,127,213)",
  };

  const render = (chart: echarts.ECharts, dataSource: any[]) => {
    const seriesSource = dataSource[0].slice(1);
    const option = {
      dataset: [{ source: dataSource }],
      xAxis: {
        type: "time",
        show: false,
      },
      yAxis: { show: false },
      series: seriesSource.map((feature: string) => {
        return {
          animation: false,
          silent: true,
          emphasis: { disabled: true },
          name: feature,
          type: "line",
          symbol: "none",
          lineStyle: { color: colormap[feature], opacity: 1, width: 1 },
          encode: { x: "t", y: feature },
        };
      }),
    };
    chart.setOption(option);
  };

  const cyclicWindow = (
    arr: any[],
    windowLength: number,
    startIndex: number
  ) => {
    const n = arr.length;
    startIndex = startIndex % n;
    const result = [];
    for (let i = 0; i < windowLength; i++) {
      const currentIndex = (startIndex + i) % n;
      result.push(arr[currentIndex]);
    }
    return result;
  };
  const replaceFirstColumn = (matrix: any[], newColumn: any[]) => {
    for (let i = 0; i < matrix.length; i++) {
      matrix[i][0] = newColumn[i];
    }
    return matrix;
  };

  const init = () => {
    const chart = echarts.init(chartContainer);
    window.onresize = chart.resize;

    const header = data.shift();
    const windowSize = Math.floor(data.length / 2); // header제외
    const defaultDate = cyclicWindow(data, windowSize, 0).map((row) => row[0]); // 고정 날짜정보 저장
    let cnt = 0;
    setInterval(() => {
      const _window = cyclicWindow(data, windowSize, cnt);
      const _arr = replaceFirstColumn(_window, defaultDate);
      _arr.unshift(header);
      render(chart, _arr);
      cnt += 1;
    }, 10);
  };

  onMount(init);
</script>

<div
  class="chart"
  style="height: {height}; width: {width};"
  bind:this={chartContainer}
></div>
