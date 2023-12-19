import axios from "axios";
import * as jwt from "jsonwebtoken";
import Swal from "sweetalert2";
import { get } from 'svelte/store';

import { Text } from './state';
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

const isJwtExpired = (token: string): boolean => {
    try {
        const decoded = jwt.decode(token) as JwtPayload | null;
        return decoded?.exp ? decoded.exp < Math.floor(Date.now() / 1000) : true;
    } catch (error) {
        return true;
    }
};


const tokenInsert = async (config: InternalAxiosRequestConfig) => {
    let [cognitoToken, cognitoRefreshToken] = await Promise.all([
        settingObjectStore.get("cognitoToken"),
        settingObjectStore.get("cognitoRefreshToken"),
    ]);

    if (cognitoToken && cognitoRefreshToken) {
        const [idToken, accessToken] = cognitoToken.split("|");
        if (isJwtExpired(idToken) || isJwtExpired(accessToken)) {
            const response = await api.public.post("/auth/refresh-cognito-token", { cognito_refresh_token: cognitoRefreshToken });
            cognitoToken = response.data["cognito_token"];
            await settingObjectStore.put("cognitoToken", cognitoToken);
        }
        config.headers["Authorization"] = `Bearer ${cognitoToken}`;
    }
    return config;
};

const authenticationFailureHandler = async (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
        return await logout();
    }
    throw error;
};

const permissionFailureHandler = async (error: AxiosError) => {
    const text = get(Text);
    switch (error.response?.status) {
        case 401:
            return await logout();
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