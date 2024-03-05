import { get } from "svelte/store";
import { api } from "../../modules/request";
import { Lang } from "../../modules/state";
import type { TsType } from "../../modules/state";

export interface PublicFgRespType {
  user: string;
  feature_group: {
    name: string;
    description: string;
    chart_type: string;
  };
  features: {
    added: string;
    color: string;
    element: {
      code: string;
      name: string;
    };
    factor: {
      name: string;
      section: string;
    };
  }[];
  colormap: { [key: string]: string };
  data: any;
}

/**
 * GET /api/data/features/public
 * @param groupId 피쳐 그룹 ID
 * @returns
 * - 404, 423 에러 응답을 받으면 해당하는 숫자를 반환합니다.
 * - 성공 응답을 수신하면 본문 데이터를 반환합니다.
 */
export const requestData = async (
  groupId: number
): Promise<number | PublicFgRespType> => {
  try {
    const response = await api.public.get("/data/features/public", {
      params: { group_id: groupId, lang: get(Lang) },
    });
    return response.data as PublicFgRespType;
  } catch (error) {
    switch (error?.response?.status) {
      case 404: // 그룹이 비어있음
        return 404;
      case 423: // 그룹이 비공개 상태임
        return 423;
      // 나머지 경우는 모두 예상치 못한 에러
    }
    throw error;
  }
};

/**
 * apiResponse의 data가 시계열 데이터를 가진 경우 해당 시계열 데이터를
 * Echarts 형식으로 변환합니다.
 */
export const extractTimeSeries = (
  apiResponse: PublicFgRespType
): { [key: string]: TsType } => {
  const results: { [key: string]: any[] } = {
    original: [],
    scaled: [],
    ratio: [],
  };

  Object.keys(results).forEach((dataType) => {
    // 헤더 맵과 기본 헤더는 여기에서 초기화
    const headersMap = new Map([["t", 0]]);
    const headers = ["t"]; // dataType별로 헤더 배열을 초기화
    const baseRows = apiResponse.data.t.map((date: string) => [date]); // dataType별 기본 행 구성
    const rows = baseRows.slice(); // 얕은 복사를 사용하여 기본 행 구성

    apiResponse.data.v.forEach((fe: any) => {
      const key = `${fe.element.section}-${fe.element.code}_${fe.factor.section}-${fe.factor.code}`;
      if (!headersMap.has(key)) {
        headersMap.set(key, headers.length);
        headers.push(key);
      }
      const columnIndex = headersMap.get(key);

      // columnIndex가 유효한지 확인
      if (typeof columnIndex === "number") {
        fe[dataType].forEach((value: any, rowIndex: number) => {
          // TsType에 맞추어 적절한 값을 할당
          if (rows[rowIndex] && rows[rowIndex][columnIndex] === undefined) {
            rows[rowIndex][columnIndex] = value;
          }
        });
      }
    });

    rows.unshift(headers); // 최상단에 헤더 행 추가
    results[dataType] = rows;
  });

  return results as { [key: string]: TsType };
};
