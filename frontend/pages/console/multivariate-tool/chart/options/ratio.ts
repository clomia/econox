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
      min: 0,
      max: 100,
      splitLine: { show: false },
      axisLine: { lineStyle: { color: "rgb(211, 208, 208)" } },
      axisLabel: {
        // 축 레이블 포맷터 함수
        formatter: (value: number) => value.toString() + "%",
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
    ],
    series: datasetSource[0].slice(1).map((feature: string) => {
      return {
        name: feature,
        type: "line",
        symbol: "none",
        emphasis: { disabled: true }, // emphasis 기능은 불안정하다.
        connectNulls: true,
        lineStyle: { color: colorMap[feature], opacity: 1, width: 2 },
        encode: {
          x: "t",
          y: feature,
        },
        areaStyle: {
          color: colorMap[feature],
          opacity: 1,
        },
        stack: "Total",
      };
    }),
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "rgb(44, 57, 75)",
          formatter: (item: any) => {
            if (item.axisDimension === "x") {
              // 날짜
              return item.seriesData[0].data[0];
            } else {
              // 값
              const value = item.value;
              const formatter = new Intl.NumberFormat(undefined, {
                maximumFractionDigits: 1,
              });
              return formatter.format(value).toString() + "%";
            }
          },
        },
      },
      backgroundColor: "rgb(44, 57, 75)",
      borderColor: "rgba(255,255,255,0.6)",
      textStyle: { color: "white" },
      extraCssText: "border-radius: 1.5px;",
      formatter: (params: any) => {
        // 날짜를 첫 줄에 추가
        let result = params[0].value[0] + "<br/>";

        params.reverse(); // 차트에 쌓인 순서는 역순임

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
          if (value) {
            const formatter = new Intl.NumberFormat(undefined, {
              maximumFractionDigits: 1,
            });
            const valueString = formatter.format(value).toString() + "%";
            result += markerString + valueString + "<br/>"; // 색상 원과 함께 값을 포맷하여 추가
          }
        });
        return result;
      },
    },
    legend: {
      left: 4,
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
      data: datasetSource[0].slice(1).map((feature: any) => {
        return {
          name: feature,
          inactiveColor: convertRGBtoRGBA(colorMap[feature], 0.2),
          itemStyle: { color: colorMap[feature], opacity: 1 },
        };
      }),
    },
  };
};
