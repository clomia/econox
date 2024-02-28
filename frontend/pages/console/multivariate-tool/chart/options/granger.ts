import { get } from "svelte/store";
import { getColorMap, convertRGBtoRGBA } from "../../functions";
import { FeatureGroups } from "../../../../../modules/state";
import type { FeatureGroupType } from "../../../../../modules/state";

export const generateOption = (apiResponse: any, groupId: number) => {
  const node = (
    get(FeatureGroups).find((group) => group.id === groupId) as FeatureGroupType
  ).features.map(
    (feature) =>
      `${feature.element.section}-${feature.element.code}_${feature.factor.section}-${feature.factor.code}`
  );
  const colorMap = getColorMap(groupId);
  const causality = apiResponse.map((item: any) => {
    const xtKey = `${item.xt.element_section}-${item.xt.element_code}_${item.xt.factor_section}-${item.xt.factor_code}`;
    const ytKey = `${item.yt.element_section}-${item.yt.element_code}_${item.yt.factor_section}-${item.yt.factor_code}`;
    return [xtKey, ytKey, item.value];
  });
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
    legend: {
      left: -40,
      padding: [5, 73, 5, 40],
      type: "scroll",
      pageTextStyle: {
        color: "rgba(255,255,255,0.8)",
      },
      pageIconColor: "white",
      pageIconInactiveColor: "rgba(255,255,255,0.4)",
      itemWidth: 25,
      itemHeight: 25,
      icon: "roundRect",
      formatter: () => "",
      data: node.map((feature) => {
        return {
          name: feature,
          inactiveColor: convertRGBtoRGBA(colorMap[feature], 0.2),
          itemStyle: { color: colorMap[feature], opacity: 1 },
        };
      }),
    },
    toolbox: {
      right: 0,
      bottom: 0,
      feature: { restore: {} },
    },
    series: {
      type: "graph",
      layout: "force",
      force: {
        repulsion: 3500,
        gravity: 0.5,
        edgeLength: 100,
        friction: 0.2,
      },
      draggable: true,
      edgeSymbol: ["none", "arrow"],
      nodes: node.map((feature, idx) => ({
        name: feature,
        itemStyle: { color: colorMap[feature] },
        symbolSize: 16 + (relCount[feature] * 6 || 0),
        category: idx,
      })),
      categories: node.map((s) => ({ name: s })),
      links: causality.map((ele: any[]) => ({
        source: ele[0],
        target: ele[1],
        value: ele[2],
        lineStyle: {
          color: `rgba(255,255,255,${Math.max(ele[2], 0.3)})`,
          width: 1,
          curveness: 0,
        },
      })),
      lineStyle: { opacity: 1 },
      emphasis: {
        label: { show: false },
        scale: false,
        itemStyle: { shadowColor: "rgba(255,255,255,0.4)", shadowBlur: 10 },
      },
      roam: true,
      scaleLimit: { min: 0.5, max: 2 },
    },
  };
};
