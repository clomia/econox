<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";

  export let height: string;
  export let width: string;

  let chartContainer: HTMLElement;

  const randomColor = () => {
    const r = Math.floor(Math.random() * 256); // Red 값 0~255
    const g = Math.floor(Math.random() * 256); // Green 값 0~255
    const b = Math.floor(Math.random() * 256); // Blue 값 0~255
    return `rgba(${r},${g},${b}, 1)`;
  };

  const removeRandomElements = (arr: any[], num: number) => {
    let _arr = [...arr];
    for (let i = 0; i < num; i++) {
      let indexToRemove = Math.floor(Math.random() * _arr.length);
      _arr.splice(indexToRemove, 1);
    }
    return _arr;
  };

  const seriesOption = {
    type: "graph",
    layout: "force",
    center: ["50%", "50%"],
    force: {
      repulsion: 3500,
      gravity: 0.5,
      edgeLength: 100,
      friction: 0.2,
    },
    edgeSymbol: ["none", "arrow"],
    lineStyle: { opacity: 1, width: 0.5 },
    emphasis: {
      label: { show: false },
      scale: false,
      itemStyle: { shadowColor: "rgba(255,255,255,0.4)", shadowBlur: 10 },
    },
    scaleLimit: { min: 0.5, max: 2 },
    edgeSymbolSize: 7,
  };

  const render = (
    chart: echarts.ECharts,
    node: string[],
    causality: any[],
    colormap: any,
    interaction = false
  ) => {
    const relCount = {};
    causality.forEach(([elementA, elementB]) => {
      [elementA, elementB].forEach((element) => {
        if (relCount[element]) {
          relCount[element] += 1;
        } else {
          relCount[element] = 1;
        }
      });
    });
    const option: any = {
      series: {
        ...seriesOption,
        nodes: node.map((feature, idx) => ({
          name: feature,
          itemStyle: { color: colormap[feature] },
          symbolSize: Math.min(8 + (relCount[feature] * 3 || 0), 25),
          category: idx,
        })),
        links: causality.map((ele) => ({
          source: ele[0],
          target: ele[1],
          value: ele[2],
          lineStyle: {
            color: `rgba(255,255,255,${Math.min(Math.max(ele[2], 0.1), 0.6)})`,
            width: 1,
            curveness: 0,
          },
        })),
      },
    };
    if (interaction) {
      option.series.draggable = true;
    }
    chart.setOption(option);
  };

  const init = () => {
    const chart = echarts.init(chartContainer);
    window.addEventListener("resize", () => chart.resize());

    let node = ["0"];
    const colormap = { "0": randomColor() };
    const causality = [];
    const LIMIT = 50; // 최대 노드 갯수
    const REPEAT = 5; // 최대 노드 갯수 하에서 제거, 생성을 반복
    let removed: number | null = null;
    setInterval(() => {
      if (node.length > LIMIT) {
        node = removeRandomElements(node, 1);
        removed = 1;
        render(chart, node, causality, colormap);
        return;
      } else if (typeof removed === "number") {
        node = removeRandomElements(node, 1);
        removed += 1;
        if (removed >= REPEAT) {
          removed = null;
        }
        render(chart, node, causality, colormap);
        return;
      }

      const remain = [...node];
      const newNode = (parseInt(node[node.length - 1]) + 1).toString();
      node.push(newNode);
      colormap[newNode] = randomColor();
      // 새로운 노드는 최소 0, 최대 3개의 연결을 만듬
      const relCount = Math.floor(Math.random() * 4); // 3개가 딱 삼각형이라 가장 이쁨
      for (let i = 0; i < relCount; i++) {
        const target = remain[Math.floor(Math.random() * remain.length)];
        const direction = Math.random() < 0.5;
        const causalityValue = Math.random();
        causality.push(
          direction
            ? [newNode, target, causalityValue]
            : [target, newNode, causalityValue]
        );
      }
      render(chart, node, causality, colormap);
    }, 500);
  };
  onMount(init);
</script>

<div
  class="chart"
  style="height: {height}; width: {width};"
  bind:this={chartContainer}
></div>
