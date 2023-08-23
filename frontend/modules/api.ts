import axios from "axios";
import * as jwt from "jsonwebtoken";

import { settingObjectStore } from "./_storage";

import type { JwtPayload } from "jsonwebtoken";
import type { InternalAxiosRequestConfig } from "axios";

export const apiHostPath = window.location.origin + "/api"
export const publicRequest = axios.create({ baseURL: apiHostPath })
export const privateRequest = axios.create({ baseURL: apiHostPath }) // 인증 실패 시 강제 로그아웃!

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

/**
 * 토큰 갱신 실패시 response.status = 401 에러 발생
 */
const tokenInsert = async (config: InternalAxiosRequestConfig) => {
    let [cognitoIdToken, cognitoAccessToken, cognitoRefreshToken] = await Promise.all([
        settingObjectStore.get("cognitoIdToken"),
        settingObjectStore.get("cognitoAccessToken"),
        settingObjectStore.get("cognitoRefreshToken"),
    ])

    if (cognitoIdToken && cognitoAccessToken && cognitoRefreshToken) {
        if (isJwtExpired(cognitoIdToken) || isJwtExpired(cognitoAccessToken)) {
            const response = await publicRequest.post("/auth/cognito-refresh-token", { cognito_refresh_token: cognitoRefreshToken })
            cognitoIdToken = response["cognito_id_token"]
            cognitoAccessToken = response["cognito_access_token"]
            settingObjectStore.put("cognitoIdToken", cognitoIdToken)
            settingObjectStore.put("cognitoAccessToken", cognitoAccessToken)
        }
        config.headers["Authorization"] = 'Bearer ' + cognitoIdToken
        config.headers["X-Cognito-Access-Token"] = cognitoAccessToken
    }
    return config
}

privateRequest.interceptors.request.use(tokenInsert)