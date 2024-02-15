import { get } from "svelte/store";
import { api } from "../../../modules/request";
import {
  Lang,
  FeatureGroups,
  FeatureGroupsLoaded,
  FeatureGroupSelected,
} from "../../../modules/state";
import type { FeatureType } from "../../../modules/state";

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
 * /api/data/features 응답 데이터를 Echarts에 넣을 수 있게 변환합니다.
 * @param data: GET /api/data/features API의 응답 데이터(data객체)
 * @param typeKey: Echarts로 렌더링할 버전 키 (original, normalized, ratio)
 */
export const featuresDataEncode = (data: any, typeKey = "original") => {
  const headersMap = new Map([["t", 0]]);
  const headers = ["t"];
  const rows = data.t.map((date: any) => [date]);

  data.v.forEach((entry: any) => {
    const key = `${entry.element.section}-${entry.element.code}_${entry.factor.section}-${entry.factor.code}`;
    if (!headersMap.has(key)) {
      headersMap.set(key, headers.length);
      headers.push(key);
    }
    const columnIndex = headersMap.get(key) as number;
    entry[typeKey].forEach((value, rowIndex) => {
      // 각 행에 대해 columnIndex 위치에 값을 할당
      rows[rowIndex][columnIndex] = value;
    });
  });

  rows.unshift(headers); // 최상단에 헤더 행 추가
  return rows;
};

/**
 * FeatureType 객체로 구성된 배열을 받아서 Echarts 범례가 매핑 가능한 컬러맵 오브젝트를 반환합니다.
 */
const featuresColorMap = (
  features: FeatureType[]
): { [key: string]: string } => {
  return features.reduce<{ [key: string]: string }>((acc, curr) => {
    const key = `symbol-${curr.element.code}_${curr.factor.section}-${curr.factor.code}`;
    acc[key] = curr.color;
    return acc;
  }, {});
};
