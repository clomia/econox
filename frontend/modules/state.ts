import { writable } from "svelte/store";

export const uiText = {
    lang: writable("en"),
    pairs: writable({}),
}

export const auth = {
    toggle: writable({ login: true, signup: false }),
    signup: {
        step: writable(0),
        emailAuthTimeLimit: writable(""),
    }
}