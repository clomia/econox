import { convertRGBtoRGBA, getColorMap } from "../../functions";

export const generateOption = (datasetSource: any, groupId: number) => {
  const colorMap = getColorMap(groupId);
  return {
    dataset: [{ source: datasetSource }],
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
        textStyle: { color: "rgba(255,255,255,0.7)" },
        labelFormatter: (value: string) => {
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
    series: datasetSource[0].slice(1).map((feature: string) => {
      return {
        name: feature,
        type: "line",
        symbol: "none",
        emphasis: { disabled: true },
        lineStyle: { color: colorMap[feature], opacity: 1, width: 1.5 },
        encode: {
          x: "t",
          y: feature,
        },
      };
    }),
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "rgb(44, 57, 75)",
        },
      },
      backgroundColor: "rgb(44, 57, 75)",
      borderColor: "rgba(255,255,255,0.6)",
      textStyle: { color: "white" },
      extraCssText: "border-radius: 1.5px;",
      formatter: (params: any) => {
        // 날짜를 첫 줄에 추가
        let result = params[0].value[0] + "<br/>";

        // 각 시리즈의 값을 기준으로 params 배열 정렬
        // 가장 큰 값을 가진 시리즈가 배열의 앞쪽에 오도록 정렬
        params.sort((a: any, b: any) => {
          let aValueIndex = a.seriesIndex + 1; // seriesIndex는 0부터 시작하므로 값 배열에서 해당 값을 찾기 위해 +1
          let bValueIndex = b.seriesIndex + 1;
          return b.value[bValueIndex] - a.value[aValueIndex]; // 내림차순 정렬
        });

        const parser = new DOMParser();
        const serializer = new XMLSerializer();
        // 정렬된 순서대로 툴팁 내용 구성
        params.forEach((item: any) => {
          let seriesIndex = item.seriesIndex + 1;
          let value = item.value[seriesIndex]; // seriesIndex에 해당하는 값

          // 피쳐에 대한 색상 원 HTML 문자열 생성
          const markerDom = parser.parseFromString(item.marker, "text/html");
          const marker = markerDom.querySelector("span") as HTMLSpanElement;
          marker.style.backgroundColor = colorMap[item.seriesName];
          const markerString = serializer.serializeToString(marker);

          result += markerString + value.toFixed(3) + "<br/>"; // 색상 원과 함께 값을 포맷하여 추가
        });
        return result;
      },
    },
    legend: {
      left: 0,
      padding: [5, 5, 5, 40],
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
      data: datasetSource[0].slice(1).map((feature: any) => {
        return {
          name: feature,
          inactiveColor: convertRGBtoRGBA(colorMap[feature]),
          itemStyle: { color: colorMap[feature], opacity: 1 },
        };
      }),
    },
  };
};
