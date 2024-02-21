import { get } from "svelte/store";
import { Lang } from "./state";

/**
 * 위키 서비스는 oopy를 통해 https://www.econox.wiki 로 호스팅되고 있습니다.
 * wikiUrl객체에 명시된 모든 페이지가 oopy의 클린 URL로 등록되어 있어야 합니다.
 * 각 페이지는 UiText.yaml에서 지원되는 모든 언어를 지원해야 합니다.
 * 예를 들어서 normalize에 대한 영어 문서는 https://www.econox.wiki/en/normalize 에 위치해야 합니다.
 */

export const wikiHost = "https://www.econox.wiki";
export const wikiUrl = {
  scaling: () => `${wikiHost}/${get(Lang)}/scaling`,
  // todo 검색창 활용법 (코드 입력 방법)
  // todo 다변량 툴에서도 위키 많이 필요할듯
};
