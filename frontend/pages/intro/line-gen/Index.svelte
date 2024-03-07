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
    const option = {
      animationDuration: 3000,
      dataset: [{ source: dataSource }],
      xAxis: {
        type: "time",
        show: false,
      },
      yAxis: { show: false },
      series: dataSource[0].slice(1).map((feature: string) => {
        return {
          emphasis: { disabled: true },
          name: feature,
          type: "line",
          symbol: "none",
          connectNulls: true,
          lineStyle: { color: colormap[feature], opacity: 1, width: 1 },
          encode: {
            x: "t",
            y: feature,
          },
        };
      }),
    };
    chart.setOption(option);
  };

  const init = () => {
    const chart = echarts.init(chartContainer);
    window.onresize = chart.resize;
    render(chart, data);
  };

  onMount(init);
</script>

<div
  class="chart"
  style="height: {height}; width: {width};"
  bind:this={chartContainer}
></div>
