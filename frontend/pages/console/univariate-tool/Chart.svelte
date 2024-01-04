<script>
  import { onMount } from "svelte";
  import * as echarts from "echarts";

  let chartContainer;

  // 예시 시계열 데이터
  const seriesData = {
    values: [20, 30, 40, 50, 60],
    times: [
      "2024-01-01T00:00:00Z",
      "2024-01-02T00:00:00Z",
      "2024-01-03T00:00:00Z",
      "2024-01-04T00:00:00Z",
      "2024-01-05T00:00:00Z",
    ],
  };

  onMount(() => {
    const chart = echarts.init(chartContainer);
    chart.setOption({
      xAxis: {
        type: "category",
        data: seriesData.times,
      },
      yAxis: {
        type: "value",
      },
      series: [
        {
          data: seriesData.values,
          type: "line",
        },
      ],
    });
  });
</script>

<div bind:this={chartContainer} style="width: 100%; height: 400px;"></div>
