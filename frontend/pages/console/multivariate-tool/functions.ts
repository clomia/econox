import { get } from "svelte/store";
import { api } from "../../../modules/request";
import {
  Lang,
  FeatureGroups,
  FeatureGroupsLoaded,
} from "../../../modules/state";

export const loadGroups = async () => {
  if (get(FeatureGroupsLoaded)) {
    return; // 이미 로딩되어 있다면 아무런 동작 안함
  }
  const resp = await api.member.get("/feature/groups", {
    params: { lang: get(Lang) },
  });
  FeatureGroups.set(resp.data);
  FeatureGroupsLoaded.set(true);
};
