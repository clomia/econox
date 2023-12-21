import { get } from "svelte/store";

import { api } from "../../../modules/request";
import { Lang } from "../../../modules/state";
import {
  UnivariateNote,
  UnivariateElements,
  UnivariateElementsLoaded,
  UnivariateFactors,
  UnivariateFactorsProgress,
  UnivariateElementSelected,
} from "../../../modules/state";
import { isSame, querySort, simpleQuerySort } from "../../../modules/functions";
import type { ElementType, FactorType } from "../../../modules/state";

/**
 * 요소를 제거합니다.
 * UnivariateElements 배열에서 제거한 후 백엔드에 삭제 요청을 보냅니다.
 * 백엔드가 삭제에 실패한 경우 해당 요소를 다시 삽입하여 동기화 한 후 에러를 던집니다.
 */
export const deleteElement = async (code: string, section: string) => {
  const univariateNote = get(UnivariateNote);
  const univariateElements = get(UnivariateElements);
  const univariateElementSelected = get(UnivariateElementSelected);

  const target = univariateElements.find(
    (ele) => ele.code === code && ele.section === section
  );
  if (!target) {
    throw new Error("Element does not exists");
  }
  if (univariateElementSelected && isSame(target, univariateElementSelected)) {
    UnivariateElementSelected.set(null); // 선택된 경우 선택 해제
  }
  if (target.note === univariateNote) {
    UnivariateNote.set(""); // 노트 대상자인 경우 노트 지우기
  }
  UnivariateElements.set(univariateElements.filter((ele) => ele !== target)); // 배열에서 요소 제거
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
    const resp = await api.member.get("/feature/factors", {
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

interface FeatureType {
  section: string;
  name: string;
  [key: string]: any;
}

export const sortBySectionName = (
  features: FeatureType[],
  query: string
): FeatureType[] => {
  // 먼저 section을 기준으로 simpleQuerySort를 사용하여 임시 정렬
  const sectionsSorted = simpleQuerySort(
    features.map((f) => f.section),
    query
  );

  // 정렬된 section을 기반으로 원본 features 배열 재구성
  const featuresSortedBySection = sectionsSorted.map(
    (sortedSection) => features.find((f) => f.section === sortedSection)!
  );

  let lastSection = "";
  let tempFeatures: FeatureType[] = [];
  const sortedFeatures: FeatureType[] = [];

  // 정렬된 features 배열을 순회하면서 동일 section의 요소들을 모음
  featuresSortedBySection.forEach((feature) => {
    if (feature.section !== lastSection && tempFeatures.length > 0) {
      // 동일 section의 요소들에 대해 name 기준으로 querySort 수행
      sortedFeatures.push(
        ...querySort(
          tempFeatures.map((f) => f.name),
          query
        ).map((sortedName) => tempFeatures.find((f) => f.name === sortedName)!)
      );
      tempFeatures = [];
    }

    tempFeatures.push(feature);
    lastSection = feature.section;
  });

  // 마지막 section에 대한 처리
  if (tempFeatures.length > 0) {
    sortedFeatures.push(
      ...querySort(
        tempFeatures.map((f) => f.name),
        query
      ).map((sortedName) => tempFeatures.find((f) => f.name === sortedName)!)
    );
  }

  return sortedFeatures;
};
