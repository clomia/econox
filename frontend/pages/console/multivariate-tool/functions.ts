import { get } from "svelte/store";
import { api } from "../../../modules/request";
import {
  Lang,
  FeatureGroups,
  FeatureGroupsLoaded,
  FeatureGroupSelected,
  FgDefaultChartType,
  FgTsOrigin,
  FgTsRatio,
  FgTsScaled,
  FgGranger,
  FgCoint,
  FgDataState,
} from "../../../modules/state";
import type {
  FeatureGroupType,
  TsType,
  FgTsType,
  GraphType,
} from "../../../modules/state";
import type { Writable } from "svelte/store";

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
  const data: FeatureGroupType[] = resp.data;
  FeatureGroups.set(data);
  FeatureGroupsLoaded.set(true);

  const defaultChartType = {};
  data.forEach((g) => (defaultChartType[g.id] = g.chart_type));
  FgDefaultChartType.set(defaultChartType);

  const selected = get(FeatureGroupSelected);
  const updated = data.find((group) => group.id === selected?.id);
  // 만약 FeatureGroupSelected에 변경사항이 있는 경우 해당 상태도 업데이트
  if (selected?.features.length !== updated?.features.length) {
    FeatureGroupSelected.set(updated as FeatureGroupType);
  }
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
export const convertRGBtoRGBA = (rgbString: string, alpha = 1) => {
  const errorDefault = "rgba(255,255,255)";
  if (!rgbString) {
    console.log(
      `[convertRGBtoRGBA] ${rgbString}은 올바른 RGB 형식이 아닙니다!`
    );
    return errorDefault;
  }

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
    return errorDefault;
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
  groupId: number;

  constructor(groupId: number) {
    this.groupId = groupId;
  }

  async getTimeSeries(): Promise<{ [key: string]: TsType }> {
    const resp = await api.member.get("/data/features", {
      params: { group_id: this.groupId },
    });

    const results: { [key: string]: any[] } = {
      original: [],
      scaled: [],
      ratio: [],
    };

    Object.keys(results).forEach((dataType) => {
      // 헤더 맵과 기본 헤더는 여기에서 초기화
      const headersMap = new Map([["t", 0]]);
      const headers = ["t"]; // dataType별로 헤더 배열을 초기화
      const baseRows = resp.data.t.map((date: string) => [date]); // dataType별 기본 행 구성
      const rows = baseRows.slice(); // 얕은 복사를 사용하여 기본 행 구성

      resp.data.v.forEach((fe: any) => {
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
  }

  async getGrangercausality() {
    const resp = await api.member.get(
      "/data/features/analysis/grangercausality",
      { params: { group_id: this.groupId } }
    );
    return resp.data as GraphType;
  }

  async getCointegration() {
    const resp = await api.member.get("/data/features/analysis/cointegration", {
      params: { group_id: this.groupId },
    });
    return resp.data as GraphType;
  }
}

const initDataState = {
  TimeSeries: "before",
  Grangercausality: "before",
  Cointegration: "before",
};
export const chartDataMap = {
  line: "TimeSeries",
  ratio: "TimeSeries",
  granger: "Grangercausality",
  coint: "Cointegration",
};
/**
 * FgDataState의 초기 상태를 설정함
 * 다변량 툴 로드 시 실행되어야 하는 함수
 */
export const initFgDataState = () => {
  if (Object.keys(get(FgDataState)).length !== 0) {
    // FgDataState 객체가 텅 비어있지 않으면 실행 X
    return;
  }
  const state = {};
  get(FeatureGroups).forEach((group) => {
    state[group.id] = initDataState;
  });
  FgDataState.set(state);
};

const dataStateUpdate = (groupId: number, dataType: string, state: string) => {
  FgDataState.update((st) => {
    return {
      ...st,
      [groupId]: { ...st[groupId], [dataType]: state },
    };
  });
};

/**
 * 차트가 선택, 변경될 때 트리거 되야 하는 함수
 * 차트 타입이 변경되거나 차트가 표시하는 데이터 그룹이 변경될 때 트리거 되야 함
 */
export const chartSelectedHandler = async (nowSelected: FeatureGroupType) => {
  const state = get(FgDataState);
  const targetData = chartDataMap[nowSelected.chart_type];
  const targetState = state[nowSelected.id][targetData];
  if (targetState !== "before") {
    return;
  }

  // during 상태는 중복 실행 방지 & 로딩 상태로 사용됨
  dataStateUpdate(nowSelected.id, targetData, "during");

  const request = new DataAPIProxy(nowSelected.id);

  // targetData에 맞게 데이터 가져와서 스토어 업데이트
  let data: any;
  switch (targetData) {
    case "TimeSeries":
      data = await request.getTimeSeries();
      [
        [FgTsOrigin, "original"],
        [FgTsScaled, "scaled"],
        [FgTsRatio, "ratio"],
      ].forEach(([store, name]) => {
        let _store = store as Writable<FgTsType>;
        let _name = name as string;
        _store.update((current) => {
          const _new = { ...current };
          _new[nowSelected.id] = data[_name];
          return _new;
        });
      });
      break;
    case "Grangercausality":
      data = await request.getGrangercausality();
      FgGranger.update((currentState) => {
        const newState = { ...currentState };
        newState[nowSelected.id] = data;
        return newState;
      });
      break;
    case "Cointegration":
      data = await request.getCointegration();
      FgCoint.update((currentState) => {
        const newState = { ...currentState };
        newState[nowSelected.id] = data;
        return newState;
      });
      break;
  }
  dataStateUpdate(nowSelected.id, targetData, "after");
};

/**
 * 피쳐 그룹에 피쳐가 추가, 삭제될 때 트리거 되야 하는 함수
 */
export const featureAddDeleteHandler = (groupId: number) => {
  FgDataState.update((state) => {
    return { ...state, [groupId]: initDataState };
  });
  const nowSelected = get(FeatureGroupSelected);
  if (groupId === nowSelected?.id) {
    chartSelectedHandler(nowSelected);
  }
};

interface RequestFormat {
  fileFormat: "csv" | "xlsx";
  groupId: number;
  lang: string;
  minmaxScaling: boolean;
}

export const downloadFile = async (name: string, request: RequestFormat) => {
  const resp = await api.member.get("/data/features/file", {
    params: {
      file_format: request.fileFormat,
      group_id: request.groupId,
      lang: request.lang,
      minmax_scaling: request.minmaxScaling,
    },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(resp.data);
  const link = document.createElement("a");
  link.href = url;

  let filename = name;
  if (request.minmaxScaling) {
    filename += "_Min-Max-Scaled";
  }
  filename += "." + request.fileFormat;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
