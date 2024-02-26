import { get } from "svelte/store";
import { getColorMap } from "../../functions";
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
      links: causality.map((ele: any[]) => ({
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
