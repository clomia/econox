import {
  scatterIcon,
  lineIcon,
  areaIcon,
  barIcon,
} from "../../../../assets/echarts";
import * as echarts from "echarts";

export const option: echarts.EChartsOption = {
  xAxis: {
    type: "time",
    axisLine: { onZero: false, lineStyle: { color: "rgba(255,255,255,0.5)" } },
    axisLabel: {
      hideOverlap: true,
      formatter: {
        year: "{year|{yyyy}}",
        month: "{month|{M}}",
        day: "{day|{M}.{d}}",
        hour: "",
        minute: "",
        second: "",
        millisecond: "",
      },
      rich: {
        year: { color: "rgb(211, 208, 208)" },
        month: { color: "rgb(255, 177, 177)" },
        day: { color: "rgba(211, 208, 208, 0.4)" },
      },
    },
  },
  yAxis: {
    splitLine: { show: false },
    axisLine: { lineStyle: { color: "rgb(211, 208, 208)" } },
  },
  dataZoom: [
    { orient: "horizontal", type: "inside" },
    {
      orient: "horizontal",
      type: "slider",
      borderRadius: 0,
      borderColor: "rgba(255,255,255,0.5)",
      backgroundColor: "rgba(0,0,0,0)",
      fillerColor: "rgba(0,0,0,0)",
      dataBackground: {
        areaStyle: { color: "white", opacity: 0.15 },
        lineStyle: { color: "white", opacity: 0.5 },
      },
      selectedDataBackground: {
        areaStyle: { color: "white", opacity: 0.3 },
        lineStyle: { color: "white", opacity: 0.5 },
      },
      moveHandleStyle: {
        color: "white",
        opacity: 0.4,
        borderColor: "rgba(0,0,0,0)",
      },
      emphasis: {
        moveHandleStyle: { color: "white", opacity: 0.5, borderColor: "white" },
      },
      handleStyle: { borderWidth: 0, color: "rgb(215, 215, 215)" },
      textStyle: { color: "rgba(255,255,255,0.7)" },
      labelFormatter: (value) => {
        // 최대 해상도를 일로 고정
        const date = new Date(value);
        return (
          date.getFullYear() +
          "." +
          (date.getMonth() + 1) +
          "." +
          date.getDate()
        );
      },
    },
    {
      // 이상치 제거용
      orient: "vertical",
      type: "slider",
      filterMode: "empty",
      borderRadius: 0,
      borderColor: "rgba(255,255,255,0.5)",
      backgroundColor: "rgba(0,0,0,0)",
      fillerColor: "rgba(0,0,0,0)",
      dataBackground: {
        areaStyle: { color: "white", opacity: 0.1 },
        lineStyle: { color: "white", opacity: 0.3 },
      },
      selectedDataBackground: {
        areaStyle: { color: "white", opacity: 0.2 },
        lineStyle: { color: "white", opacity: 0.3 },
      },
      moveHandleSize: 0,
      handleStyle: { borderWidth: 0, color: "rgb(215, 215, 215)" },
      textStyle: { color: "rgba(255,255,255,0.7)" },
    },
  ],
  series: [
    {
      zlevel: 2,
      name: "scatter",
      type: "scatter",
      color: "white",
      symbolSize: 5,
      large: true,
    },
    {
      zlevel: 1,
      name: "line",
      type: "line",
      symbol: "none",
      lineStyle: { color: "white", opacity: 1, width: 1.5 },
      areaStyle: { opacity: 0 },
      connectNulls: true,
      emphasis: { disabled: true },
    },
    {
      zlevel: 1,
      name: "area",
      type: "line",
      symbol: "none",
      lineStyle: { opacity: 0, width: 0 },
      areaStyle: { color: "white", opacity: 0.3 },
      connectNulls: true,
      emphasis: { disabled: true },
    },
    {
      zlevel: 3,
      name: "bar",
      type: "bar",
      itemStyle: { color: "white" },
      emphasis: { focus: "self", blurScope: "series" },
      large: true,
    },
  ],
  legend: {
    data: [
      {
        name: "scatter",
        icon: scatterIcon,
        inactiveColor: "rgba(255,255,255,0.3)",
        itemStyle: { color: "white", opacity: 1 },
        textStyle: { color: "white" },
      },
      {
        name: "line",
        icon: lineIcon,
        inactiveColor: "rgba(255,255,255,0.3)",
        itemStyle: { color: "white", opacity: 1 },
        textStyle: { color: "white" },
      },
      {
        name: "area",
        icon: areaIcon,
        inactiveColor: "rgba(255,255,255,0.3)",
        itemStyle: { color: "white", opacity: 1 },
        textStyle: { color: "white" },
      },
      {
        name: "bar",
        icon: barIcon,
        inactiveColor: "rgba(255,255,255,0.3)",
        itemStyle: { color: "white", opacity: 1 },
        textStyle: { color: "white" },
      },
    ],
    selected: { scatter: true, line: false, area: false, bar: false },
    backgroundColor: "rgb(48, 46, 62)",
    padding: [8, 15],
    borderColor: "rgba(255,255,255,0.5)",
    borderRadius: 0,
    borderWidth: 1,
  },
  tooltip: {
    formatter: (params: any) => {
      const value = params.data[1];
      const formattedValue = Number.isInteger(value) ? value : value.toFixed(2);
      return `${params.data[0]}: ${formattedValue}`;
    },
    backgroundColor: "rgb(44, 57, 75)",
    borderColor: "rgba(255,255,255,0.6)",
    padding: [3, 7],
    textStyle: { color: "white" },
    extraCssText: "border-radius: 1.5px;",
  },
  toolbox: {
    feature: {
      restore: {
        iconStyle: { borderColor: "rgba(255,255,255,0.5)" },
        emphasis: { iconStyle: { borderColor: "white" } },
      },
    },
  },
};
