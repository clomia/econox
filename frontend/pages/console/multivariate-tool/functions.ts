import { get } from "svelte/store";
import { api } from "../../../modules/request";
import {
  Lang,
  FgStoreState,
  FeatureGroups,
  FeatureGroupsLoaded,
  FeatureGroupSelected,
  FgDefaultChartType,
  FgTsOrigin,
  FgTsRatio,
  FgTsScaled,
  FgGranger,
  FgCoint,
} from "../../../modules/state";
import type {
  FeatureGroupType,
  TsType,
  FgTsType,
  GraphType,
  StoreStateType,
  FgStoreStateType,
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
  const data: FeatureGroupType[] = resp.data.map((group: any) => {
    group.confirm = true;
    return group;
  });
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

/**
 * 두 FgStoreStateType 객체가 같은지 비교합니다.
 * fgDataStateTracker가 불필요한 반응성 트리거를 막기 위해 사용합니다.
 */
const fgStoreStateIsSame = (
  obj1: FgStoreStateType,
  obj2: FgStoreStateType
): boolean => {
  // 두 객체의 키 집합을 확인하여 길이가 다르면 바로 false 반환
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  if (keys1.length !== keys2.length) return true;

  for (const key of keys1) {
    if (!obj2.hasOwnProperty(key)) {
      return true;
    }

    const state1 = obj1[key];
    const state2 = obj2[key];
    const subKeys1 = Object.keys(state1);
    const subKeys2 = Object.keys(state2);

    // 하위 객체의 키 집합 길이 비교
    if (subKeys1.length !== subKeys2.length) return true;

    for (const subKey of subKeys1) {
      if (state1[subKey] !== state2[subKey]) {
        return true;
      }
    }
  }

  // 모든 조건을 통과했다면 두 객체는 동일함
  return false;
};

/**
 * FeatureGroups 상태의 변경사항을 추적하기 위한 함수입니다.
 * 변경전, 변경후 객체를 받아서 FgStoreState 상태를 업데이트합니다.
 */
export const fgDataStateTracker = (
  before: FeatureGroupType[],
  after: FeatureGroupType[]
) => {
  const state = get(FgStoreState);

  // 1. 그룹 자체가 배열에 추가되거나 삭제된 부분을 상태에 반영합니다.
  const stateInitObj: StoreStateType = {
    FgTsOrigin: "before",
    FgTsScaled: "before",
    FgTsRatio: "before",
    FgGranger: "before",
    FgCoint: "before",
  };
  const managedGroups = Object.keys(state);
  const groups = after.map((group) => group.id.toString());
  // groups에는 있지만 managedGroups에는 없는 요소들
  const added = groups.filter((item) => !managedGroups.includes(item));
  // 추가된 그룹을 상태 관리에 추가
  added.forEach((groupId) => (state[groupId] = stateInitObj));
  // managedGroups에는 있지만 groups에는 없는 요소들
  const removed = managedGroups.filter((item) => !groups.includes(item));
  // 삭제된 그룹을 상태 관리에서 제거
  removed.forEach((groupId) => {
    delete state[groupId];
  });

  // 2. 그룹 내부의 features가 추가되거나 삭제된 부분을 상태에 반영합니다.

  // Map을 사용하여 before와 after 배열의 id를 키로 하는 객체로 변환합니다.
  const beforeMap = new Map(
    before.map((item) => [item.id, item.features.length])
  );
  const afterMap = new Map(
    after.map((item) => [item.id, item.features.length])
  );

  const changedFeatureGroupIds = new Set<number>();
  // features 배열 길이가 변경된 그룹 ID로 구성된 집합(set) 생성
  before.forEach(({ id }) => {
    if (beforeMap.get(id) !== afterMap.get(id)) {
      changedFeatureGroupIds.add(id);
    }
  });

  for (const groupId of changedFeatureGroupIds) {
    // 데이터가 바뀐 그룹에 대해서
    for (const key in state[groupId]) {
      // 모든 데이터 스토어를 "업데이트 반영 전" 상태로 바꾼다.
      if (state[groupId].hasOwnProperty(key)) {
        state[groupId][key] = "before";
      }
    }
  }
  if (fgStoreStateIsSame(state, get(FgStoreState))) {
    // 반영된 내용이 기존 객체와 다른 경우 스토어를 업데이트합니다.
    FgStoreState.set(state);
  }
};

// fgDataStateSynchronizer와 fgDataStateTracker는 chart/Index.svelte에 의해 긴밀하게 엮여있습니다.
// 따라서 두 로직을 함께 읽어야 동작을 파악할 수 있습니다. 두 함수는 상호 의존적입니다.

/**
 * Fg 데이터 스토어에서 현재 필요한 부분만 업데이트합니다.
 * 현재의 groupSelected를 매개변수로 받습니다.
 */
export const fgDataStateSynchronizer = async (group: FeatureGroupType) => {
  const state = { ...get(FgStoreState) };
  const api = new DataAPIProxy(group.id);

  let isUpdate: string;
  switch (group.chart_type) {
    case "line":
    case "ratio":
      isUpdate = state[group.id].FgTsOrigin;
      if (isUpdate !== "before") {
        // 데이터 업데이트 상태가 before 이어야만 통과 가능
        // 만약 confirm을 하는 업데이트라면 before가 아니더라도 통과 가능
        return;
      }
      // 상태를 during으로 업데이트
      FgStoreState.update((currentState) => {
        const updatedState = { ...currentState };
        updatedState[group.id] = {
          ...updatedState[group.id],
          FgTsOrigin: "during",
          FgTsRatio: "during",
          FgTsScaled: "during",
        };
        return updatedState;
      });
      if (!group.confirm) {
        // confirm되지 않은 경우 여기에서 스탑
        return;
      }
      const ts = await api.getTimeSeries();
      [
        [FgTsOrigin, "original"],
        [FgTsScaled, "scaled"],
        [FgTsRatio, "ratio"],
      ].forEach(([store, name]) => {
        let _store = store as Writable<FgTsType>;
        let _name = name as string;
        _store.update((currentState) => {
          const newState = { ...currentState };
          newState[group.id] = ts[_name];
          return newState;
        });
      });

      // 상태를 after로 업데이트
      FgStoreState.update((currentState) => {
        const updatedState = { ...currentState };
        updatedState[group.id] = {
          ...updatedState[group.id],
          FgTsOrigin: "after",
          FgTsRatio: "after",
          FgTsScaled: "after",
        };
        return updatedState;
      });
      break;
    case "granger":
      isUpdate = state[group.id].FgGranger;
      if (isUpdate !== "before") {
        return;
      }
      FgStoreState.update((currentState) => {
        const updatedState = { ...currentState };
        updatedState[group.id] = {
          ...updatedState[group.id],
          FgGranger: "during", // 상태를 during으로 업데이트
        };
        return updatedState;
      });
      if (!group.confirm) {
        return;
      }
      const granger = await api.getGrangercausality(); // API 호출
      FgGranger.update((currentState) => {
        const newState = { ...currentState };
        newState[group.id] = granger;
        return newState;
      });
      FgStoreState.update((currentState) => {
        const updatedState = { ...currentState };
        updatedState[group.id] = {
          ...updatedState[group.id],
          FgGranger: "after", // 상태를 after로 업데이트
        };
        return updatedState;
      });
      break;
    case "coint":
      isUpdate = state[group.id].FgCoint;
      if (isUpdate !== "before") {
        return;
      }
      FgStoreState.update((currentState) => {
        const updatedState = { ...currentState };
        updatedState[group.id] = {
          ...updatedState[group.id],
          FgCoint: "during", // 상태를 during으로 업데이트
        };
        return updatedState;
      });
      if (!group.confirm) {
        return;
      }
      const coint = await api.getCointegration(); // API 호출
      FgCoint.update((currentState) => {
        const newState = { ...currentState };
        newState[group.id] = coint;
        return newState;
      });
      FgStoreState.update((currentState) => {
        const updatedState = { ...currentState };
        updatedState[group.id] = {
          ...updatedState[group.id],
          FgCoint: "after", // 상태를 after로 업데이트
        };
        return updatedState;
      });
      break;
  }
};
