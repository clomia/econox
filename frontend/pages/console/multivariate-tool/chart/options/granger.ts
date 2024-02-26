export const generateOption = (
  node: string[],
  causality: any[],
  colorMap: any
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
  return {
    toolbox: {
      left: 38,
      feature: { restore: {} },
    },
    series: {
      type: "graph",
      layout: "force",
      force: {
        repulsion: 3500,
        gravity: 0.35,
        edgeLength: 50,
        friction: 0.2,
      },
      draggable: true,
      edgeSymbol: ["none", "arrow"],
      nodes: node.map((feature) => ({
        name: feature,
        itemStyle: { color: colorMap[feature] },
        symbolSize: Math.max(relCount[feature] * 12, 26),
      })),
      links: causality.map((ele) => ({
        source: ele[0],
        target: ele[1],
        value: ele[2],
        lineStyle: { color: `rgba(255,255,255,${ele[2]})`, width: 1 },
        label: {
          show: true,
          formatter: (item: any) => (item.value * 100).toFixed(0) + "%",
          fontSize: 16,
          color: `rgba(255,255,255,${Math.max(ele[2] * 2, 0.5)})`,
          textBorderWidth: 0,
        },
      })),
      lineStyle: { opacity: 1 },
      autoCurveness: 0.4,
      emphasis: { label: { show: false } },
      roam: true,
      scaleLimit: { min: 0.5, max: 2 },
    },
  };
};
