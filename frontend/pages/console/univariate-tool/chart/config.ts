import {
  scatterIcon,
  lineIcon,
  areaIcon,
  barIcon,
} from "../../../../assets/echarts";
import * as echarts from "echarts";

export const option = (
  defaultLegend = { bar: true, scatter: false, line: false, area: false }
): echarts.EChartsOption => {
  return {
    xAxis: {
      type: "time",
      axisLine: {
        onZero: false,
        lineStyle: { color: "rgba(255,255,255,0.5)" },
      },
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
      axisLabel: {
        // 축 레이블 포맷터 함수
        formatter: (value: number) => {
          const formatter = new Intl.NumberFormat(undefined, {
            maximumFractionDigits: 1,
          });
          const sign = value < 0 ? "-" : "";
          const absValue = Math.abs(value);

          if (absValue >= 1000000000) {
            return sign + formatter.format(absValue / 1000000000) + "B";
          } else if (absValue >= 1000000) {
            return sign + formatter.format(absValue / 1000000) + "M";
          } else if (absValue >= 1000) {
            return sign + formatter.format(absValue / 1000) + "K";
          }
          return sign + formatter.format(absValue);
        },
      },
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
          moveHandleStyle: {
            color: "white",
            opacity: 0.5,
            borderColor: "white",
          },
        },
        handleStyle: { borderWidth: 0, color: "rgb(215, 215, 215)" },
        textStyle: { color: "rgba(0,0,0,0)" },
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
        symbolSize: 10,
        itemStyle: { color: "white", opacity: 0.8 },
        emphasis: { focus: "self", blurScope: "series" },
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
        itemStyle: { color: "rgb(211, 200, 208)" },
        emphasis: { focus: "self", blurScope: "series" },
        large: true,
      },
    ],
    legend: {
      data: [
        {
          name: "bar",
          icon: barIcon,
          inactiveColor: "rgba(255,255,255,0.3)",
          itemStyle: { color: "white", opacity: 1 },
          textStyle: { color: "white" },
        },
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
      ],
      selected: defaultLegend,
      backgroundColor: "rgba(255,255,255,0)",
      padding: [8, 15],
      borderColor: "rgba(255,255,255,0)",
      borderRadius: 0,
      borderWidth: 1,
    },
    tooltip: {
      formatter: (params: any) => {
        const data = params instanceof Array ? params[0].data : params.data;
        const formatter = new Intl.NumberFormat(undefined, {
          maximumFractionDigits: 2,
          useGrouping: true,
        });
        return `${data[0]} ${formatter.format(data[1])}`;
      },
      backgroundColor: "rgb(44, 57, 75)",
      borderColor: "rgba(255,255,255,0.6)",
      padding: [3, 7],
      textStyle: { color: "white" },
      extraCssText: "border-radius: 1.5px;",
    },
    axisPointer: {
      show: true,
      snap: true,
      triggerEmphasis: false, // 강조 표시 버그 해결
      label: { show: false }, // 미관상 방해되서 없앰
    },
    toolbox: {
      left: 38,
      feature: {
        restore: {},
      },
    },
  };
};
