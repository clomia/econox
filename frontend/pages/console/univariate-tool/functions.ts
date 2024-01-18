import Swal from "sweetalert2";
import { get } from "svelte/store";

import { api } from "../../../modules/request";
import { Lang, Text } from "../../../modules/state";
import {
  UnivariateElements,
  UnivariateElementsLoaded,
  UnivariateElementSelected,
  UnivariateFactors,
  UnivariateFactorsProgress,
  UnivariateFactorSelected,
  UnivariateChartSource,
} from "../../../modules/state";
import {
  isSame,
  format,
  querySort,
  defaultSwalStyle,
} from "../../../modules/functions";
import type { ElementType, FactorType } from "../../../modules/state";

/**
 * 요소를 제거합니다.
 * UnivariateElements 배열에서 제거한 후 백엔드에 삭제 요청을 보냅니다.
 * 백엔드가 삭제에 실패한 경우 해당 요소를 다시 삽입하여 동기화 한 후 에러를 던집니다.
 */
export const deleteElement = async (code: string, section: string) => {
  const univariateElements = get(UnivariateElements);
  const univariateElementSelected = get(UnivariateElementSelected);

  const target = univariateElements.find((ele) =>
    isSame(ele, { code, section })
  );
  if (!target) {
    throw new Error("Element does not exists");
  }
  const elementArr = univariateElements.filter((ele) => !isSame(ele, target));
  UnivariateElements.set(elementArr); // 배열에서 요소 제거
  UnivariateFactorSelected.set(null); // 선택된 펙터 초기화
  if (univariateElementSelected && isSame(target, univariateElementSelected)) {
    UnivariateElementSelected.set(null); // 선택된 경우 선택 해제
  }
  try {
    await api.member.delete("/feature/user/element", {
      params: { code, section },
    });
  } catch (error) {
    univariateElements.push(target);
    univariateElements.sort(
      // 실패시 다시 삽입 후 올바르게 정렬
      (e1, e2) =>
        new Date(e2.update_time as string).getTime() -
        new Date(e1.update_time as string).getTime()
    );
    UnivariateElements.set(univariateElements);
    throw error;
  }
};

/**
 * UnivariateElements를 세팅합니다. 이미 세팅된 경우 아무런 동작을 하지 않습니다.
 * 이 함수가 실행된 이후 UnivariateElements를 통해 데이터에 접근 가능해집니다.
 */
export const setElements = async () => {
  const lang = get(Lang);
  const univariateElementsLoaded = get(UnivariateElementsLoaded);

  if (!univariateElementsLoaded) {
    const resp = await api.member.get("/feature/user/elements", {
      params: { lang },
    });
    UnivariateElements.set(resp.data);
    UnivariateElementsLoaded.set(true);
  }
};

/**
 * Element에 대한 Factor를 UnivariateFactors를 세팅합니다. 이미 세팅된 경우 아무런 동작을 하지 않습니다.
 * 이 함수가 실행된 이후 UnivariateFactors를 통해 Element에 대한 Factor들에 접근할 수 있습니다.
 * @param ele Factor를 가져올 Element
 */
export const setFactors = async (ele: ElementType) => {
  const lang = get(Lang);

  const elementKey = `${ele.section}-${ele.code}`;
  if (elementKey in get(UnivariateFactors)) {
    return; // 이미 세팅이 된 경우 아무런 동작 안함
  }
  UnivariateFactorsProgress.set({
    ...get(UnivariateFactorsProgress),
    [elementKey]: 0, // 로딩이 시작되었다는 표시
  });

  let page = 0;
  const accumulated: FactorType[] = [];
  while (true) {
    const resp = await api.member.get("/feature/element/factors", {
      params: {
        element_code: ele.code,
        element_section: ele.section,
        lang: lang,
        page: ++page, // 현재 페이지를 알아야 하므로 전위 연산 사용
      },
    });
    const factors: FactorType[] = resp.data["factors"];
    const totalPages: number = resp.data["pages"];

    accumulated.push(...factors);
    // UnivariateFactors, UnivariateFactorsProgress는 실시간성을 띄므로 최신의 상태를 참조하도록 해야 한다.
    UnivariateFactors.set({
      ...get(UnivariateFactors),
      [elementKey]: accumulated,
    });
    let currentProgress = page / totalPages;
    const beforeProgress = get(UnivariateFactorsProgress)[elementKey];
    if (currentProgress < beforeProgress) {
      // 가끔 진행률이 줄어드는 현상에 대한 대처
      currentProgress = beforeProgress; // 이 문제는 로직은 잘 작동하나 병렬 처리에 따른 안정성 이슈라고 생각됨
    } // 스토어를 Factor마다 나눠보기도 했는데 고쳐지지 않았음, 더 복잡해지기만 함
    UnivariateFactorsProgress.set({
      ...get(UnivariateFactorsProgress),
      [elementKey]: currentProgress,
    });

    if (totalPages === page) {
      // 현재 페이지가 마지막이면 종료
      break;
    }
    if (!get(UnivariateElements).some((_e) => isSame(_e, ele))) {
      // Element가 리스트에서 제거된 경우 종료
      break;
    }
  }
};

/**
 * 객체의 특정 속성으로 배열을 정렬합니다.
 * @param arr 객체로 이루어진 배열
 * @param query 검색 쿼리 문자열
 * @param attrKey 검색 속성, 2단계 이상의 깊이는 배열을 통해 정의
 * @returns 정렬된 배열
 */
export const attrQuerySort = (
  arr: any[],
  query: string,
  attrKey: string | string[]
): any[] => {
  const _arr = [...arr];
  const result: any[] = [];

  const getAttr = (obj: any) => {
    if (typeof attrKey === "string") {
      return obj[attrKey];
    } else if (Array.isArray(attrKey)) {
      return attrKey.reduce((currentObj, key) => currentObj[key], obj);
    }
  };

  const sortedAttrs = querySort(_arr.map(getAttr), query);

  sortedAttrs.forEach((attr) => {
    const index = _arr.findIndex((feature) => getAttr(feature) === attr);
    if (index !== -1) {
      result.push(_arr[index]);
      _arr.splice(index, 1);
    }
  });
  return result;
};

/**
 * - 시계열 데이터를 불러와 Echarts에 호환되는 배열로 세팅합니다.
 * - UnivariateChartSource 전역 상태에 결과를 반영합니다.
 * - factorSection은 factor.section.code 입니다
 */
export const setChartSource = async (
  elementCode: string,
  elementSection: string,
  factorCode: string,
  factorSection: string
) => {
  const sourceKey = `${elementSection}-${elementCode}_${factorSection}-${factorCode}`;
  if (get(UnivariateChartSource)[sourceKey]) {
    return;
  } else {
    UnivariateChartSource.set({
      ...get(UnivariateChartSource),
      [sourceKey]: { original: [], normalized: [] },
      // 중복 호출 방지 & 로딩 시작이라는 의미
      // 만약 서버가 빈 배열을 응답한다고 해도 ["t", "v"] 때문에 로딩 전 후는 구분 가능
    });
  }

  try {
    const resp = await api.member.get("/data/feature", {
      params: {
        element_code: elementCode,
        element_section: elementSection,
        factor_code: factorCode,
        factor_section: factorSection,
      },
    });
    const encode = (data: any): [string, string | number][] => {
      const dataset = data.t.map((time: string, index: number) => [
        time,
        data.v[index],
      ]);
      return [["t", "v"], ...dataset];
    };
    UnivariateChartSource.set({
      ...get(UnivariateChartSource),
      [sourceKey]: {
        original: encode(resp.data.original),
        normalized: encode(resp.data.normalized),
      },
    });
  } catch (error: any) {
    if (error?.response?.status === 404) {
      const univariateChartSource = get(UnivariateChartSource);
      delete univariateChartSource[sourceKey];
      UnivariateChartSource.set(univariateChartSource);

      const univariateFactors = get(UnivariateFactors);
      const elementKey = `${elementSection}-${elementCode}`;
      const elementFactors = univariateFactors[elementKey]; // get
      const targetIndex = elementFactors.findIndex(
        (factor) =>
          factor.code === factorCode && factor.section.code === factorSection
      );
      const targetFactor = elementFactors.splice(targetIndex, 1)[0]; // delete
      univariateFactors[elementKey] = elementFactors; // update
      UnivariateFactors.set(univariateFactors); // reset

      const univariateFactorSelected = get(UnivariateFactorSelected);
      if (
        univariateFactorSelected?.code === factorCode &&
        univariateFactorSelected?.section.code === factorSection
      ) {
        UnivariateFactorSelected.set(null);

        // 스토어 업데이트 이벤트 발생용, Note 컴포넌트에서 이 이벤트를 사용해 내용을 초기화한다.
        UnivariateElementSelected.set(get(UnivariateElementSelected));
      }
      const text = get(Text);
      await Swal.fire({
        ...defaultSwalStyle,
        width: "33rem",
        icon: "info",
        showDenyButton: false,
        title: format(text.f_TheElementDoesNotContainThisFactor, {
          element: elementCode,
          factor: `${targetFactor.section.name}(${targetFactor.name})`,
        }),
        confirmButtonText: text.Ok,
      });
    }
  }
};

interface RequestFormat {
  fileFormat: "csv" | "xlsx";
  normalized: boolean;
  elementSection: string;
  elementCode: string;
  factorSection: string;
  factorCode: string;
}

/**
 * /api/data/feature/file API shortcut
 * @returns 다운로드 URL (브라우저 메모리를 가르키며 새로고침 시 사라짐)
 */
export const downloadFile = async (request: RequestFormat) => {
  const resp = await api.member.get("/api/data/feature/file", {
    params: {
      element_section: request.elementSection,
      element_code: request.elementCode,
      factor_section: request.factorSection,
      factor_code: request.factorCode,
      normalized: request.normalized,
      file_format: request.fileFormat,
    },
    responseType: "blob",
  });
  return window.URL.createObjectURL(resp.data);
};
