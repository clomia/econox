import axios from "axios";
import { onMount } from "svelte";
import { get } from "svelte/store";
import { navigate } from "svelte-routing";
import { api } from "./request";
import { Text, UserInfo, Lang, CountryCodeMap } from "./state";
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
 * 클라이언트 상태에 따라 페이지 접근을 제한합니다.
 * 파라미터로 허용 조건을 입력하고 허용되지 않을 경우의 리디렉션 경로를 failRedirect에 입력하세요.
 * 사용 예시: `verify({conds: {login: true}, failRedirect: "/account"})`
 * @param conds 충족해야 하는 요구 조건
 * @param failRedirect 요구 조건을 충족하지 못할 때 리디렉션할 경로
 */
export const verify = (
  {
    conds: { login = null, membership = null, billingOk = null },
    failRedirect = "/",
  }: VerificationArgs = { conds: {} }
) => {
  onMount(async () => {
    const userInfo = get(UserInfo);
    const failureConditions = [
      login !== null && login !== Boolean(userInfo.id),
      membership !== null && membership !== userInfo.membership,
      billingOk && !["active", "deactive"].includes(userInfo.billing.status),
    ]; // require 혹은 ''(기본값)인 경우는 billingOk가 아님

    if (failureConditions.some(Boolean)) {
      navigate(failRedirect);
    }
  });
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
