import axios from "axios";
import * as jwt from "jsonwebtoken";

import { settingObjectStore } from "./_storage";

import type { JwtPayload } from "jsonwebtoken";
import type { InternalAxiosRequestConfig } from "axios";

export const apiHostPath = window.location.origin + "/api"
export const publicRequest = axios.create({ baseURL: apiHostPath })
export const privateRequest = axios.create({ baseURL: apiHostPath }) // 인증 실패 시 강제 로그아웃!

export const settingKey = {
    idToken: "idToken",
    refreshToken: "refreshToken"
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

/**
 * 토큰 갱신 실패시 response.status = 401 에러 발생
 */
const tokenInsert = async (config: InternalAxiosRequestConfig) => {
    let [idToken, refreshToken] = await Promise.all([
        settingObjectStore.get(settingKey.idToken),
        settingObjectStore.get(settingKey.refreshToken),
    ])

    if (idToken && refreshToken) {
        if (isJwtExpired(idToken)) {
            const token = await publicRequest.post("/auth/refresh-token", { refresh_token: refreshToken })
            idToken = token["id_token"]
            settingObjectStore.put(settingKey.idToken, idToken)
        }
        config.headers["Authorization"] = 'Bearer ' + idToken
    }
    return config
}

privateRequest.interceptors.request.use(tokenInsert)