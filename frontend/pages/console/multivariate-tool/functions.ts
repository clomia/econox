import { get } from "svelte/store";
import { api } from "../../../modules/request";
import {
  Lang,
  Text,
  FeatureGroups,
  FeatureGroupsLoaded,
  FeatureGroupSelected,
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
