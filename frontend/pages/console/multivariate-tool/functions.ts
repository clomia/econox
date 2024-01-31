import { api } from "../../../modules/request";
import { FeatureGroups } from "../../../modules/state";

export const loadGroups = async () => {
  const resp = await api.member.get("/feature/groups");
  FeatureGroups.set(resp.data);
};
