import { api } from "./request"
import { Text, UserInfo } from "./state"
import { loadUiText } from "./uiText"
import { settingObjectStore } from "./_storage"

import type { UiText } from "../static/UiText"

/**
 * 토큰 삭제 후 홈으로 리로딩
 */
export const logout = async () => {
    await Promise.all([
        settingObjectStore.delete("cognitoToken"),
        settingObjectStore.delete("cognitoRefreshToken")
    ])
    window.location.replace(window.location.origin) // 홈으로 리로딩
}

/**
 * 토큰 저장 후 콘솔로 리로팅
 */
export const login = async (cognitoToken: string, cognitoRefreshToken: string, reload: boolean = true) => {
    await Promise.all([
        settingObjectStore.put("cognitoToken", cognitoToken),
        settingObjectStore.put("cognitoRefreshToken", cognitoRefreshToken)
    ])
    if (reload) {
        window.location.replace(window.location.origin + "/console") // 콘솔로 리로딩
    }
}

/**
 * 문자열 내부 중괄호를 매개변수로 채움, f_ 로 시작하는 UiText에 주로 사용
 */
export const format = (template: string, { ...kwargs }) => {
    return template.replace(/{(\w+)}/g, function (match, key) {
        return kwargs.hasOwnProperty(key) ? kwargs[key] : match;
    })
}

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
    ])
    return cognitoToken && cognitoRefreshToken
}

/**
 * 페이지가 처음 로드될 때 한번 작동되는 함수입니다.
 * 이 함수가 완료된 후, 컴포넌트가 실행됩니다.
 * @return value - 저장할 객체
 */
export const init = async () => {
    // ========== www 서브도메인을 붙이도록 강제합니다. ==========
    const currentUrl = new URL(window.location.href);
    const { hostname } = currentUrl;
    const localHosts = ["localhost", "127.0.0.1"];
    if (!hostname.startsWith("www.") && !localHosts.includes(hostname)) {
        currentUrl.hostname = "www." + hostname;
        window.location.href = currentUrl.toString();
    }

    // ========== UI 텍스트와 유저 데이터를 불러옵니다. ==========
    const [cognitoToken, cognitoRefreshToken] = await Promise.all([
        settingObjectStore.get("cognitoToken"),
        settingObjectStore.get("cognitoRefreshToken"),
    ])
    if (cognitoToken && cognitoRefreshToken) {
        const [uiText, userInfo] = await Promise.all([loadUiText(), api.private.get("/user")])
        Text.set(uiText.text as UiText)
        UserInfo.set(userInfo.data)
    }
    Text.set((await loadUiText()).text as UiText);
}

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