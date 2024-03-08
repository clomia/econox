<script lang="ts">
  import * as echarts from "echarts";
  import "echarts-gl";
  import { onMount } from "svelte";

  export let height: string;
  export let width: string;
  export let distance: number = 400;

  let chartContainer: HTMLElement;

  const option = {
    globe: {
      displacementQuality: "ultra",
      baseTexture: "/static/img/earth-texture.jpg",
      heightTexture: "/static/img/earth-texture.jpg",
      displacementScale: 0.04,
      shading: "realistic",
      realisticMaterial: {
        roughness: 0.9,
      },
      postEffect: {
        enable: true,
      },
      viewControl: {
        autoRotate: true,
        autoRotateDirection: "ccw",
        autoRotateSpeed: 50,
        autoRotateAfterStill: 0.1,
        rotateSensitivity: 1.3,
        maxDistance: distance,
        distance: distance,
        minDistance: distance,
        targetCoord: [170, 20],
      },
    },
  };

  const init = () => {
    const chart = echarts.init(chartContainer);
    window.onresize = chart.resize;
    chart.setOption(option);
  };

  onMount(init);
</script>

<div
  class="chart"
  style="height: {height}; width: {width}; position: relative;"
  bind:this={chartContainer}
/>
