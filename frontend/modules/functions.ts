import Swal from "sweetalert2"

import { request } from "./api"
import { settingObjectStore } from "./_storage"

export const logout = async () => {
    await Promise.all([
        settingObjectStore.delete("cognitoToken"),
        settingObjectStore.delete("cognitoRefreshToken")
    ])
    window.location.reload()
}

export const login = async (email: string, password: string) => {
    const response = await request.public.post("/auth/user", { email, password });
    await Promise.all([
        settingObjectStore.put("cognitoToken", response.data["cognito_token"]),
        settingObjectStore.put("cognitoRefreshToken", response.data["cognito_refresh_token"])
    ])
    window.location.replace(window.location.origin + "/console");
}

const logoutWithAlert = async (message: string) => {
    await Swal.fire({
        icon: 'error',
        text: message,
        // confirmButtonText: (await loadUiText()).text.ok,
    })
    await logout()
}

export const timeToString = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = (time % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}`;
};