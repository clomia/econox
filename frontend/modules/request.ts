import axios from "axios";
import * as jwt from "jsonwebtoken";
import Swal from "sweetalert2";
import { get } from "svelte/store";

import { Text } from "./state";
import { settingObjectStore } from "./_storage";
import { logout, defaultSwalStyle } from "./functions";

import type { JwtPayload } from "jsonwebtoken";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

export const apiHostPath = window.location.origin + "/api";
export const api = {
  public: axios.create({ baseURL: apiHostPath }),
  private: axios.create({ baseURL: apiHostPath }), // 인증
  member: axios.create({ baseURL: apiHostPath }), // 인증 + 권한
};

/**
 * 토큰 만료 여부를 반환합니다.
 * @param token 만료 여부를 확인할 JWT
 * @returns 토큰 만료 여부
 */
const isJwtExpired = (token: string): boolean => {
  try {
    const decoded = jwt.decode(token) as JwtPayload | null;
    return decoded?.exp ? decoded.exp < Math.floor(Date.now() / 1000) : true;
  } catch (error: any) {
    return true;
  }
};

/**
 * Cognito 토큰을 갱신하고, 갱신된 토큰을 반환합니다.
 * @param refreshToken Refresh 토큰 (유효하지 않은 경우 로그아웃)
 * @returns 갱신된 Cognito 토큰
 */
const tokenRefresh = async (refreshToken: string) => {
  const resp = await api.public.post("/auth/refresh-cognito-token", {
    cognito_refresh_token: refreshToken,
  });
  const newCognitoToken: string = resp.data["cognito_token"];
  await settingObjectStore.put("cognitoToken", newCognitoToken);
  return newCognitoToken;
};

/**
 * Axios 요청 객체에 토큰을 삽입하여 반환합니다.
 * @param config Axios 요청 객체
 * @returns Axios 요청 객체
 */
const tokenInsert = async (config: InternalAxiosRequestConfig) => {
  let [cognitoToken, cognitoRefreshToken] = await Promise.all([
    settingObjectStore.get("cognitoToken"),
    settingObjectStore.get("cognitoRefreshToken"),
  ]);

  if (cognitoToken && cognitoRefreshToken) {
    const [idToken, accessToken] = cognitoToken.split("|");
    if (isJwtExpired(idToken) || isJwtExpired(accessToken)) {
      cognitoToken = await tokenRefresh(cognitoRefreshToken);
    }
    config.headers["Authorization"] = `Bearer ${cognitoToken}`;
  }
  return config;
};

/**
 * 토큰을 갱신한 후 동일한 요청을 다시 수행합니다.
 * 토큰 갱신요청 혹은 갱신 후 재요청이 인증 실패하면 로그아웃됩니다.
 */
const retryWithTokenRefresh = async (
  originalRequest: InternalAxiosRequestConfig
) => {
  try {
    const refreshToken = await settingObjectStore.get("cognitoRefreshToken"); // 갱신용 토큰 가져오기
    await tokenRefresh(refreshToken); // 토큰 갱신 후 settingObjectStore에서 토큰 교체
    const tokenRefreshedRequest = await tokenInsert(originalRequest); // 교체된 토큰으로 요청 다시 생성
    return await axios(tokenRefreshedRequest); // 생성한 요청 수행
  } catch (error: any) {
    if (error?.response?.status === 401) {
      // 다른 기기에서 로그인되면 갱신토큰이 비활성화된다.
      // 토큰의 유효기간은 5분이므로 최대 5분 후 갱신을 시도하는데 이때 갱신이 불가능하면 여기로 온다.
      // 갱신토큰은 10년짜리라 갱신토큰이 만료되서 비활성화되는 경우는 고려하지 않음
      const text = get(Text);
      console.log(text.LogoutReasonUseAnotherDevice);
      await Swal.fire({
        ...defaultSwalStyle,
        width: "32rem",
        icon: "info",
        showDenyButton: false,
        text: text.LogoutReasonUseAnotherDevice,
        confirmButtonText: text.Ok,
      });
      return await logout();
    }
    throw error;
  }
};

/**
 * - 에러 원인이 서버 과부화인지 판별하고 서버 과부화인 경우 안내 위젯과 함께 계정 페이지로 리디렉션 시킵니다.
 * - 계정 페이지가 서버 부하가 가장 적으므로 피신처로 쓸건데, 이것도 안되면 다른 방법이 없음
 * - 에러 원인이 서버 과부화가 아닌 경우 아무런 행동도 하지 않습니다.
 */
const serverOverloadHandler = async (error: AxiosError) => {
  if (error.response) {
    const resp = error.response;
    if (resp.status === 502 || resp.status === 504) {
      try {
        JSON.parse(resp.data as any);
      } catch {
        // 응답 코드가 502혹은 504이며 본문이 JSON이 아닙니다.
        const text = get(Text);
        await Swal.fire({
          ...defaultSwalStyle,
          width: "30rem",
          icon: "info",
          showDenyButton: false,
          title: text.ServerOverload,
          confirmButtonText: text.Ok,
        });
        return window.location.replace(window.location.origin + "/account");
      }
    }
  }
};

const authenticationFailureHandler = async (error: AxiosError) => {
  await serverOverloadHandler(error);
  if (error.response?.status === 401) {
    const originalRequest = error.config as InternalAxiosRequestConfig;
    return await retryWithTokenRefresh(originalRequest);
  } else {
    throw error;
  }
};

const permissionFailureHandler = async (error: AxiosError) => {
  await serverOverloadHandler(error);
  const text = get(Text);
  switch (error.response?.status) {
    case 401:
      const originalRequest = error.config as InternalAxiosRequestConfig;
      return await retryWithTokenRefresh(originalRequest);
    case 402:
      await Swal.fire({
        ...defaultSwalStyle,
        width: "30rem",
        icon: "info",
        showDenyButton: false,
        title: text.DeactivatedAccountBillingRequire,
        confirmButtonText: text.Ok,
      });
      return window.location.replace(window.location.origin + "/account");
    case 403:
      return await Swal.fire({
        ...defaultSwalStyle,
        width: "30rem",
        icon: "info",
        title: text.ProfessionalMembershipRequire,
        confirmButtonText: text.ProfessionalMembershipRequire_ConfirmText,
        denyButtonText: text.Ok,
        preConfirm: async () =>
          window.location.replace(window.location.origin + "/account"),
      });
    default:
      throw error;
  }
};

api.private.interceptors.request.use(tokenInsert);
api.private.interceptors.response.use(undefined, authenticationFailureHandler);

api.member.interceptors.request.use(tokenInsert);
api.member.interceptors.response.use(undefined, permissionFailureHandler);
