import axios, { Axios } from "axios";
import * as jwt from "jsonwebtoken";
import { settingObjectStore } from "./storage";
import * as lang from "./lang";
import type { JwtPayload } from "jsonwebtoken";
import type { AxiosRequestConfig } from "axios";

function isJwtExpired(token: string): boolean {
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



async function tokenInsert(config: AxiosRequestConfig) {
    let idToken = await settingObjectStore.get("idToken")
    let refreshToken = await settingObjectStore.get("refreshToken")
    if (idToken && refreshToken) {
        if (isJwtExpired(idToken)) {
            const requests = axios.create({ baseURL: window.location.origin });
            try {
                const token = await requests.post("/api/auth/refresh-token", { refresh_token: refreshToken })
                idToken = token["id_token"]
                settingObjectStore.put("idToken", idToken)
            } catch (error) {
                // 토큰 갱신 실패 -> 로그아웃
                settingObjectStore.delete("idToken")
                settingObjectStore.delete("refreshToken")
                const langInfo = await lang.load()
                langInfo.pin
                if (error.response.status === 401) {

                    alert("") // !! 세션이 유효하지 않다 꺼져라.
                } else {
                    throw error
                }
            }
            // 토큰 갱신 요청 보내서 직접 갱신하기
            // 스토어에 저장하고 idToken 변수 바꾸면 됌
        }
    }
}

// axios.interceptors.request.use(insertToken)