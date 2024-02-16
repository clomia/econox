import { get } from "svelte/store";
import { api } from "../../../modules/request";
import {
  Lang,
  FeatureGroups,
  FeatureGroupsLoaded,
  FeatureGroupSelected,
  FeatureGroupsSrc,
} from "../../../modules/state";

/**
 * 기본적으로 동작 반복을 방지하나, must 매개변수로 true를 주면
 * 무조건 동작을 수행합니다. 예외적인 함수 호출에서 must을 true로 하세요
 */
export const loadGroups = async (must = false) => {
  if (!must && get(FeatureGroupsLoaded)) {
    return; // 이미 로딩되어 있다면 아무런 동작 안함
  } // must 이 True인 경우 무조건 동작합니다.
  const resp = await api.member.get("/feature/groups", {
    params: { lang: get(Lang) },
  });
  FeatureGroups.set(resp.data);
  FeatureGroupsLoaded.set(true);
};

/**
 * FeatureGroupSelected 상태를 업데이트합니다.
 * @id 선택할 그룹 아이디
 */
export const selectGroup = (id: number) => {
  const target = get(FeatureGroups).find((group) => group.id === id);
  if (target) FeatureGroupSelected.set(target);
};

/**
 * rgb 문자열을 rgba문자열 형식으로 변환합니다.
 * 투명도를 추가할 때 사용하세요
 */
export const convertRGBtoRGBA = (rgbString: string, alpha = 0.2) => {
  // rgb 문자열에서 숫자를 추출하기 위한 정규 표현식
  const regex = /rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)/;

  // 정규 표현식을 사용하여 rgb 값 추출
  const matches = rgbString.match(regex);

  // 추출된 rgb 값을 rgba 문자열로 변환
  if (matches) {
    const r = matches[1];
    const g = matches[2];
    const b = matches[3];
    return `rgba(${r},${g},${b},${alpha})`;
  } else {
    // 입력된 문자열이 올바른 rgb 포맷이 아닌 경우, 오류 메시지 반환
    console.log(`[convertRGBtoRGBA] 문자열 ${rgbString}은 RGB형식이 아닙니다!`);
    return "rgba(255,255,255,0.2)";
  }
};

/**
 * 해당 그룹의 색상 정보를 피쳐이름과 매핑하여 객체로 반환합니다.
 * 피쳐 이름은 `{element.section}-{element.code}_{factor.section}-{factor.code}`입니다.
 */
export const getColorMap = (groupId: number) => {
  const group = get(FeatureGroups).find((group) => group.id === groupId);
  if (group) {
    return group.features.reduce<{ [key: string]: string }>((acc, curr) => {
      const key = `${curr.element.section}-${curr.element.code}_${curr.factor.section}-${curr.factor.code}`;
      acc[key] = curr.color;
      return acc;
    }, {});
  } else {
    return {};
  }
};

/**
 * GET /api/data/features 기반 API로 데이터를 불러와 Echarts Dataset source 형식으로 제공합니다.
 */
class DataAPIProxy {
  static avliableDataTypes = [
    "original",
    "scaled",
    "ratio",
    "grangercausality",
    "cointegration",
  ];
  groupId: number;

  constructor(groupId: number) {
    this.groupId = groupId;
  }

  /**
   * @param dataType GET /data/features API가 지원하는 original,scaled,ratio 만 혀용됩니다.
   * @returns API로 데이터를 받은 후 Echarts에 바로 적용 가능하도록 2차원 배열로 변환해서 반환합니다.
   */
  private async getTimeSeries(dataType: string) {
    const resp = await api.member.get("/data/features", {
      params: { group_id: this.groupId },
    });
    const headersMap = new Map([["t", 0]]);
    const headers = ["t"];
    const rows = resp.data.t.map((date: string) => [date]);
    resp.data.v.forEach((fe: any) => {
      const key = `${fe.element.section}-${fe.element.code}_${fe.factor.section}-${fe.factor.code}`;
      if (!headersMap.has(key)) {
        headersMap.set(key, headers.length);
        headers.push(key);
      }
      const columnIndex = headersMap.get(key) as number;
      fe[dataType].forEach((value: any, rowIndex: any) => {
        // 각 행에 대해 columnIndex 위치에 값을 할당
        rows[rowIndex][columnIndex] = value;
      });
    });
    rows.unshift(headers); // 최상단에 헤더 행 추가
    return rows;
  }

  async original() {
    return await this.getTimeSeries("original");
  }
  async scaled() {
    return await this.getTimeSeries("scaled");
  }
  async ratio() {
    return await this.getTimeSeries("ratio");
  }
  async grangercausality() {
    return {};
  }
  async cointegration() {
    return {};
  }
}

/**
 * GET /api/data/features API 응답을 Echarts dataset source 형식으로 반환합니다.
 * 이미 수집된 데이터는 state.ts에 의해 캐싱되어 바로 응답됩니다.
 * @param groupId 데이터 그룹의 ID
 * @param dataType Echart 차트 타입
 */
export const getSrc = async (groupId: number, dataType: string) => {
  if (!DataAPIProxy.avliableDataTypes.includes(dataType)) {
    throw Error(
      `${dataType}은 유효한 타입이 아닙니다. 사용 가능한 타입: ${DataAPIProxy.avliableDataTypes}`
    );
  }
  const src = get(FeatureGroupsSrc).find((group) => group.id === groupId);
  if (src?.[dataType]) {
    return src[dataType];
  }
  const dataProxy = new DataAPIProxy(groupId);
  const data = await dataProxy[dataType]();
  const initObject = {
    id: groupId,
    original: null,
    scaled: null,
    ratio: null,
    grangercausality: null,
    cointegration: null,
  };
  initObject[dataType] = data;
  FeatureGroupsSrc.set([initObject, ...get(FeatureGroupsSrc)]);
  return data;
};
