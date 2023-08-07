import { writable } from "svelte/store";

const defaultObject = <T>(defaultValue: T): { [k: string]: T } => new Proxy({}, { get: () => defaultValue });

export const uiText = {
    lang: writable("en"),
    text: writable(defaultObject("")),
}

export const auth = {
    toggle: writable({ login: true, signup: false }),
    signup: {
        step: writable(0),
        emailAuthTimeLimit: writable(""),
        inputResult: writable({ email: "" }) // DB 유저 생성시 필요한 정보들
    }
}

