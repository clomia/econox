import axios from "axios";
import * as jwt from "jsonwebtoken";

import { settingObjectStore } from "./_storage";

import type { JwtPayload } from "jsonwebtoken";
import type { InternalAxiosRequestConfig } from "axios";

export const apiHostPath = window.location.origin + "/api"
export const request = {
    public: axios.create({ baseURL: apiHostPath }),
    private: axios.create({ baseURL: apiHostPath }) // 인증 실패 시 강제 로그아웃!
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
            const response = await request.public.post("/auth/cognito-refresh-token", { cognito_refresh_token: cognitoRefreshToken })
            const cognitoToken = response["cognito_token"]
            settingObjectStore.put("cognitoToken", cognitoToken)
        }
        config.headers["Authorization"] = `Bearer ${cognitoToken}`
    }
    return config
}

request.private.interceptors.request.use(tokenInsert)