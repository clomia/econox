import { get } from "svelte/store";
import { api } from "../../modules/request";
import { Lang } from "../../modules/state";

export interface publicGroupType {
  user: string;
  // todo 마저 써야 함
  data: any;
}

/**
 * GET /api/data/features/public
 * @param groupId 피쳐 그룹 ID
 * @returns
 * - 404, 423 에러 응답을 받으면 해당하는 숫자를 반환합니다.
 * - 성공 응답을 수신하면 본문 데이터를 반환합니다.
 */
export const requestData = async (groupId: number) => {
  try {
    const response = await api.public.get("/data/features/public", {
      params: { group_id: groupId, lang: get(Lang) },
    });
    return response.data;
  } catch (error) {
    switch (error?.response?.status) {
      case 404: // 그룹이 비어있음
        return 404;
      case 423: // 그룹이 비공개 상태임
        return 423;
      // 나머지 경우는 모두 예상치 못한 에러
    }
  }
};
