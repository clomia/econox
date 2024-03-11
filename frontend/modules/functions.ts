import axios from "axios";
import Swal from "sweetalert2";
import { get } from "svelte/store";
import { api } from "./request";
import { Text, UserInfo, Lang, CountryCodeMap, FirstURL } from "./state";
import { loadUiText } from "./uiText";
import { settingObjectStore } from "./_storage";

export const defaultSwalStyle = {
  width: "25rem",
  color: "var(--white)",
  background: "var(--widget-background)",
  inputAttributes: {
    autocapitalize: "off",
  },
  showLoaderOnConfirm: true,
  showDenyButton: true,
  allowOutsideClick: false,
  confirmButtonColor: "rgba(255,255,255,0.05)",
  denyButtonColor: "rgba(255,255,255,0.05)",
  reverseButtons: true,
};

export const defaultToastStyle = {
  width: "31rem",
  toast: true,
  showConfirmButton: false,
  timer: 2000,
  timerProgressBar: true,
  position: "bottom-end",
  color: "var(--white)",
  background: "var(--widget-background)",
};

/**
 * 페이지가 처음 로드될 때 한번 작동되는 함수입니다.
 * 이 함수가 완료된 후, 컴포넌트가 실행됩니다.
 */
export const init = async () => {
  // ========== www 서브도메인을 붙이도록 강제합니다. ==========
  const currentUrl = new URL(window.location.href);
  const { hostname } = currentUrl;
  const localHosts = ["localhost", "127.0.0.1"];
  if (!hostname.startsWith("www.") && !localHosts.includes(hostname)) {
    currentUrl.hostname = "www." + hostname;
    window.location.href = currentUrl.toString(); // 리디렉션
  }
  FirstURL.set(currentUrl);

  // ========== UI 텍스트와 유저 데이터를 불러옵니다. ==========
  const [uiText, countryCodeMap, cognitoToken, cognitoRefreshToken] =
    await Promise.all([
      loadUiText(),
      axios
        .create({ baseURL: window.location.origin })
        .get("/static/countryCodeMap.json"),
      settingObjectStore.get("cognitoToken"), // 이 작업들은 매우 빠름
      settingObjectStore.get("cognitoRefreshToken"),
    ]);
  Text.set(uiText.text);
  Lang.set(uiText.lang);
  CountryCodeMap.set(countryCodeMap.data);

  if (cognitoToken && cognitoRefreshToken) {
    // 로그인된 경우 유저 데이터 세팅하기
    const userInfo = await api.private.get("/user");
    UserInfo.set(userInfo.data);
  }
};

/**
 * 토큰 삭제 후 로그인 페이지로 리로딩
 */
export const logout = async () => {
  await Promise.all([
    settingObjectStore.delete("cognitoToken"),
    settingObjectStore.delete("cognitoRefreshToken"),
  ]);
  return window.location.replace(window.location.origin + "/auth");
};

/**
 * 토큰 저장 후 콘솔로 리로팅
 */
export const login = async (
  cognitoToken: string,
  cognitoRefreshToken: string,
  reload: boolean = true
) => {
  await Promise.all([
    settingObjectStore.put("cognitoToken", cognitoToken),
    settingObjectStore.put("cognitoRefreshToken", cognitoRefreshToken),
  ]);
  if (reload) {
    window.location.replace(window.location.origin + "/console"); // 콘솔로 리로딩
  }
};

type VerificationFactors = {
  login?: boolean | null;
  membership?: "basic" | "professional" | null;
  billingOk?: boolean | null;
};

type VerificationArgs = {
  conds: VerificationFactors;
  failRedirect?: string;
};

/**
 * 모든 요소를 덮을 수 있는 커버 요소를 생성하여 리디렉션 중 노출되는 DOM이 없도록 가립니다.
 */
const domCover = () => {
  // 새로운 div 요소를 생성합니다.
  const overlay = document.createElement("div");

  // 생성된 div에 스타일을 적용하여 전체 화면을 덮도록 합니다.
  overlay.style.position = "fixed"; // 고정 위치
  overlay.style.top = "0"; // 상단에서 0
  overlay.style.left = "0"; // 왼쪽에서 0
  overlay.style.width = "100vw"; // 뷰포트의 100% 너비
  overlay.style.height = "100vh"; // 뷰포트의 100% 높이
  overlay.style.background =
    "linear-gradient(to top, #1f282c, #1f3036, #1f282c)"; // 반투명 검정색 배경
  overlay.style.zIndex = "1000"; // 다른 요소 위에 표시

  // 생성된 요소를 body의 자식 요소로 추가합니다.
  document.body.appendChild(overlay);
  document.body.style.overflow = "hidden"; // 스크롤 잠금
};

/**
 * 클라이언트 상태에 따라 페이지 접근을 제한합니다.
 * 파라미터로 허용 조건을 입력하고 허용되지 않을 경우의 리디렉션 경로를 failRedirect에 입력하세요.
 * 사용 예시: `verify({conds: {login: true}, failRedirect: "/auth"})`
 * [예외적 동작] 로그인이 안된 경우는 무조건 "/auth"로 리디렉션합니다.
 * @param conds 충족해야 하는 요구 조건
 * @param failRedirect 요구 조건을 충족하지 못할 때 리디렉션할 경로
 */
export const verify = async (
  {
    conds: { login = null, membership = null, billingOk = null },
    failRedirect = "/",
  }: VerificationArgs = { conds: {} }
) => {
  const userInfo = get(UserInfo);
  const isBillingOk = ["active", "deactive"].includes(userInfo.billing.status); // require 혹은 ''(기본값)인 경우는 billingOk가 아님
  const isLoggedIn = Boolean(userInfo.id);
  const failureConditions = [
    login !== null && login !== isLoggedIn,
    membership !== null && membership !== userInfo.membership,
    billingOk && !isBillingOk,
  ];

  const text = get(Text);

  if (failureConditions.some(Boolean)) {
    if ((login || billingOk) && !isLoggedIn) {
      // 로그인이 필요한데 로그인되어 있지 않은 경우
      // billingOk는 로그인이 필요하다는 의미도 포함함
      await Swal.fire({
        ...defaultSwalStyle,
        width: "25rem",
        icon: "info",
        showDenyButton: false,
        title: text.LoginRequired,
        confirmButtonText: text.Ok,
      });
      domCover();
      window.location.replace(window.location.origin + "/auth");
      return;
    } else if (billingOk && !isBillingOk) {
      // 로그인 되어있고, 유료 회원용 페이지에 접속했으나 결제 상태가 올바르지 않은 경우
      await Swal.fire({
        ...defaultSwalStyle,
        width: "33rem",
        icon: "info",
        showDenyButton: false,
        title: text.DeactivatedAccountBillingRequire,
        confirmButtonText: text.Ok,
      });
    }
    domCover();
    window.location.replace(window.location.origin + failRedirect);
  }
};

/**
 * 문자열 내부 중괄호를 매개변수로 채움, f_ 로 시작하는 UiText에 주로 사용
 */
export const format = (template: string, { ...kwargs }) => {
  return template.replace(/{(\w+)}/g, function (match, key) {
    return kwargs.hasOwnProperty(key) ? kwargs[key] : match;
  });
};

/**
 * 초단위 정수를 분:초 문자열로 반환
 */
export const secondToString = (time: number) => {
  const minutes = Math.floor(time / 60);
  const seconds = (time % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
};

export const isLoggedIn = async (): Promise<boolean> => {
  const [cognitoToken, cognitoRefreshToken] = await Promise.all([
    settingObjectStore.get("cognitoToken"),
    settingObjectStore.get("cognitoRefreshToken"),
  ]);
  return cognitoToken && cognitoRefreshToken;
};

/**
 * 2023-09-26T07:04:20.000Z 형식의 문자열을 받아 브라우저 시간대에 맞는 연.월.일 문자열 반환
 */
export const timeString = (str: string) => {
  const date = new Date(str);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const day = date.getDate().toString().padStart(2, "0");
  return `${year}.${month}.${day}`;
};
/**
 * 결제수단을 표현하는 문자열 반환
 */
export const paymentMethodString = (str: string): string => {
  if (/^[0-9*]+$/.test(str)) {
    return str.match(/.{1,4}/g)?.join(" ") || "";
  }
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export interface FeatureType {
  code: string;
  section: string | { code: string; name: string; note: string };
  [key: string]: any;
}

/**
 * 객체의 code 속성과 section이 일치하는지 여부를 반환합니다.
 * Element, Factor 객체를 비교할 때 쓰세요
 */
export const isSame = (a: FeatureType, b: FeatureType) => {
  if (typeof a.section !== "string" && typeof b.section !== "string") {
    return a.code === b.code && a.section.code === b.section.code;
  } else {
    return a.code === b.code && a.section === b.section;
  }
};

/**
 * 문자열에 쿼리가 포함된 비율
 */
export const calculateQueryRatio = (str: string, query: string) => {
  const matches =
    str.toLowerCase().match(new RegExp(query.toLowerCase(), "g")) || [];
  return (matches.length * query.length) / str.length;
};

/**
 * 문자열과 쿼리끼리 문자가 겹치는 횟수
 */
export const charOccur = (str: string, query: string) => {
  const lcQuery = query.toLowerCase();
  let count = 0;
  let tempStr = str.toLowerCase();
  lcQuery.split("").forEach((char) => {
    while (tempStr.includes(char)) {
      tempStr = tempStr.replace(char, "");
      count++;
    }
  });
  return count;
};

/**
 * 쿼리와 일치하는 요소가 앞에 오도록 배열을 정렬합니다.
 */
export const querySort = (arr: string[], query: string): string[] => {
  return arr.sort((a, b) => {
    const aRatio = calculateQueryRatio(a, query);
    const bRatio = calculateQueryRatio(b, query);
    const aOccur = charOccur(a, query);
    const bOccur = charOccur(b, query);

    // 먼저 calculateQueryRatio 결과가 둘 다 0인지 확인
    if (aRatio === 0 && bRatio === 0) {
      // 둘 다 0이라면 charOccur 결과에 따라 정렬
      return bOccur - aOccur;
    }

    // 그렇지 않으면 기존의 로직대로 ratio를 이용하여 정렬
    return bRatio - aRatio;
  });
};

/**
 * 객체의 특정 속성으로 배열을 정렬합니다.
 * @param arr 객체로 이루어진 배열
 * @param query 검색 쿼리 문자열
 * @param attrKey 검색 속성, 2단계 이상의 깊이는 배열을 통해 정의
 * @returns 정렬된 배열
 */
export const attrQuerySort = <T>(
  arr: T[],
  query: string,
  attrKey: string | string[]
): T[] => {
  const _arr = [...arr];
  const result: T[] = [];

  const getAttr = (obj: any) => {
    if (typeof attrKey === "string") {
      return obj[attrKey as keyof T];
    } else if (Array.isArray(attrKey)) {
      return attrKey.reduce(
        (currentObj, key) => currentObj[key as keyof T],
        obj
      );
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
 * 문자열 input 요소에 on:input 헨들러로 달아놓으면 공백 입력을 막아줍니다.
 */
export const inputStrip = (event: any) => {
  event.target.value = event.target.value.replace(/\s+/g, "");
};

/**
 * 문자열에서 공백을 정리합니다.
 */
export const strip = (inputString: string) => {
  return inputString.replace(/\s+/g, " ").trim();
};

/**
 * 문자열에 공백이 있는지 확인합니다.
 */
export const hasGap = (inputString: string): boolean => {
  const whitespaceRegex = /\s/;
  return whitespaceRegex.test(inputString);
};

/**
 * OK 버튼이 나오는 Swal 띄우기
 */
export const swal = async (
  message: string,
  width = "33rem",
  icon: any = "info"
) => {
  const text = get(Text);
  await Swal.fire({
    ...defaultSwalStyle,
    width,
    icon,
    showDenyButton: false,
    title: message,
    confirmButtonText: text.Ok,
  });
};

/**
 * 두 배열이 동일한지 검사합니다.
 * 1차원 배열이어야 합니다.
 */
export const isSameArray = (array1: any[], array2: any[]) => {
  // 먼저 배열의 길이를 비교
  if (array1.length !== array2.length) {
    return false; // 길이가 다르면 두 배열은 동일할 수 없으므로 false 반환
  }
  // 길이가 같을 경우, 모든 요소가 동일한지 검사
  return array1.every((element, index) => element === array2[index]);
};

export const isInViewport = (element: HTMLElement) => {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
};
