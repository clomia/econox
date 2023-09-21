import axios from "axios";
import * as jwt from "jsonwebtoken";

import { settingObjectStore } from "./_storage";
import { logout } from "./functions";

import type { JwtPayload } from "jsonwebtoken";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

export const apiHostPath = window.location.origin + "/api"
export const api = {
    public: axios.create({ baseURL: apiHostPath }),
    private: axios.create({ baseURL: apiHostPath })
}

const isJwtExpired = (token: string): boolean => {
    try {
        const decoded = jwt.decode(token) as JwtPayload | null;
        if (decoded) {
            return decoded.exp < Math.floor(Date.now() / 1000);
        }
    } catch (error) {
        return true;
    }
    return true
}

const tokenInsert = async (config: InternalAxiosRequestConfig) => {
    let [cognitoToken, cognitoRefreshToken] = await Promise.all([
        settingObjectStore.get("cognitoToken"),
        settingObjectStore.get("cognitoRefreshToken"),
    ])

    if (cognitoToken && cognitoRefreshToken) {
        const [idToken, accessToken] = cognitoToken.split("|")
        if (isJwtExpired(idToken) || isJwtExpired(accessToken)) {
            const response = await api.public.post("/auth/refresh-cognito-token", { cognito_refresh_token: cognitoRefreshToken })
            const cognitoToken = response.data["cognito_token"]
            settingObjectStore.put("cognitoToken", cognitoToken)
        }
        config.headers["Authorization"] = `Bearer ${cognitoToken}`
    }
    return config
}

const authenticationFailureHandler = async (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
        await logout() // 401 응답 시 토큰들 삭제 후 홈으로 이동
    }
}

api.private.interceptors.request.use(tokenInsert)
api.private.interceptors.response.use(undefined, authenticationFailureHandler)