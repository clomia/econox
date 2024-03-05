import { convertRGBtoRGBA } from "../../../console/multivariate-tool/functions";
import { extractTimeSeries } from "../../function";
import type { PublicFgRespType } from "../../function";

const _generateOption = (apiResponse: PublicFgRespType, data: string) => {
  const datasets = extractTimeSeries(apiResponse);
  const datasetSource: any = datasets[data];
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

          if (absValue >= 1e12) {
            // 1조 이상인 경우, T로 표시
            return sign + formatter.format(absValue / 1e12) + "T";
          } else if (absValue >= 1e9) {
            // 10억 이상 1조 미만인 경우, B로 표시
            return sign + formatter.format(absValue / 1e9) + "B";
          } else if (absValue >= 1e6) {
            // 100만 이상 10억 미만인 경우, M으로 표시
            return sign + formatter.format(absValue / 1e6) + "M";
          } else if (absValue >= 1e3) {
            // 1000 이상 100만 미만인 경우, K로 표시
            return sign + formatter.format(absValue / 1e3) + "K";
          }
          return sign + formatter.format(absValue); // 1000 미만인 경우, 그대로 표시
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
    ],
    series: datasetSource[0].slice(1).map((feature: string) => {
      return {
        name: feature,
        type: "line",
        symbol: "none",
        emphasis: { disabled: true },
        connectNulls: true,
        lineStyle: {
          color: apiResponse.colormap[feature],
          opacity: 1,
          width: 2,
        },
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
          marker.style.backgroundColor = apiResponse.colormap[item.seriesName];
          const markerString = serializer.serializeToString(marker);
          if (value) {
            result += markerString + value.toFixed(3) + "<br/>"; // 색상 원과 함께 값을 포맷하여 추가
          }
        });
        return result;
      },
    },
    legend: {
      right: 63,
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
          inactiveColor: convertRGBtoRGBA(apiResponse.colormap[feature], 0.2),
          itemStyle: { color: apiResponse.colormap[feature], opacity: 1 },
        };
      }),
    },
  };
};

export const original = (apiResponse: PublicFgRespType) => {
  return _generateOption(apiResponse, "original");
};
export const scaled = (apiResponse: PublicFgRespType) => {
  return _generateOption(apiResponse, "scaled");
};
