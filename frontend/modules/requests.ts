import axios from "axios";
import * as jwt from "jsonwebtoken";
import Swal from 'sweetalert2';
import { settingObjectStore } from "./storage";
import { loadText } from "./lang"
import type { JwtPayload } from "jsonwebtoken";
import type { InternalAxiosRequestConfig, AxiosError } from "axios";


export const publicRequest = axios.create({ baseURL: window.location.origin })
export const privateRequest = axios.create({ baseURL: window.location.origin }) // 인증 실패 시 강제 로그아웃!

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

/**
 * 강제 로그아웃
 * @param message alert에 띄울 메세지
 */
async function forceLogout(message: string) {
    await settingObjectStore.delete("idToken")
    await settingObjectStore.delete("refreshToken")
    const text = await loadText();
    await Swal.fire({
        title: message,
        confirmButtonText: text.ok
    });
    window.location.reload()
}

/**
 * 로그인 상태인 경우 요청헤더에 토큰을 삽입합니다.  
 * 토큰이 만료되었으면 토큰 갱싱 후 삽입합니다.  
 * 토큰 갱신에 실패한 경우 로그아웃 처리를 합니다.  
 * 로그인 상태가 아닌 경우 토큰을 삽입하지 않습니다.  
 */
async function tokenInsert(config: InternalAxiosRequestConfig) {
    let idToken = await settingObjectStore.get("idToken")
    let refreshToken = await settingObjectStore.get("refreshToken")

    if (idToken && refreshToken) {
        if (isJwtExpired(idToken)) {
            try { // 토큰 갱신
                const token = await api.post("/api/auth/refresh-token", { refresh_token: refreshToken })
                idToken = token["id_token"]
                settingObjectStore.put("idToken", idToken)
            } catch (error) {
                const text = await loadText();
                if (error.response.status === 401) { // 갱신토큰 사용 불가
                    forceLogout(text.sessionInvalid) // 다시 로그인해서 갱신토큰 발급 받아야 함
                }
            }
        }
        config.headers["Authorization"] = 'Bearer ' + idToken
    }
    return config
}

async function errorHandler(error: AxiosError) {
    const text = await loadText();
    if (error.response.status === 401) { // 인증 문제인 경우 강제 로그아웃 처리
        await forceLogout(text.loginRequired)
    }
    throw error
}

publicRequest.interceptors.request.use(tokenInsert)
privateRequest.interceptors.request.use(tokenInsert)
privateRequest.interceptors.response.use(undefined, errorHandler)