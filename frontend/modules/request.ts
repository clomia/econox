import axios from "axios";
import * as jwt from "jsonwebtoken";
import Swal from "sweetalert2";
import { get } from 'svelte/store';

import { Text } from './state';
import { settingObjectStore } from "./_storage";
import { logout, defaultSwalStyle } from "./functions";

import type { JwtPayload } from "jsonwebtoken";
import type { Axios, AxiosError, InternalAxiosRequestConfig } from "axios";

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
    try {
        const resp = await api.public.post("/auth/refresh-cognito-token", { cognito_refresh_token: refreshToken });
        const newCognitoToken: string = resp.data["cognito_token"];
        await settingObjectStore.put("cognitoToken", newCognitoToken);
        return newCognitoToken
    } catch (error: any) {
        if (error?.response?.status === 401) {
            return await logout(); // Refresh 토큰이 유효하지 않으므로 로그아웃해야 함
        }
        throw error
    }
}

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
const retryWithTokenRefresh = async (originalRequest: InternalAxiosRequestConfig) => {
    try {
        const tokenRefreshedRequest = await tokenInsert(originalRequest) // 토큰 갱신 요청
        return await axios(tokenRefreshedRequest) // 갱신된 토큰으로 재요청
    } catch (error: any) {
        if (error?.response?.status === 401) {
            return await logout();
        }
        throw error
    }
}

const authenticationFailureHandler = async (error: AxiosError) => {
    if (error.response?.status === 401) {
        const originalRequest = error.config as InternalAxiosRequestConfig
        return await retryWithTokenRefresh(originalRequest)
    } else {
        throw error
    }
};

const permissionFailureHandler = async (error: AxiosError) => {
    const text = get(Text);
    switch (error.response?.status) {
        case 401:
            const originalRequest = error.config as InternalAxiosRequestConfig
            return await retryWithTokenRefresh(originalRequest)
        case 402:
            await Swal.fire({
                ...defaultSwalStyle,
                icon: "info",
                showDenyButton: false,
                title: text.DeactivatedAccountBillingRequire,
                confirmButtonText: text.Ok,
            });
            return window.location.replace(window.location.origin + "/account");
        case 403:
            return await Swal.fire({
                ...defaultSwalStyle,
                icon: "info",
                title: text.ProfessionalMembershipRequire,
                confirmButtonText: text.ProfessionalMembershipRequire_ConfirmText,
                denyButtonText: text.Ok,
                preConfirm: async () => window.location.replace(window.location.origin + "/account"),
            });
        default:
            throw error;
    }
};

api.private.interceptors.request.use(tokenInsert);
api.private.interceptors.response.use(undefined, authenticationFailureHandler);

api.member.interceptors.request.use(tokenInsert);
api.member.interceptors.response.use(undefined, permissionFailureHandler);