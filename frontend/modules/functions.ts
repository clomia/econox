import Swal from "sweetalert2"

import { publicRequest } from "./api"
import { settingObjectStore } from "./_storage"

export const logout = async () => {
    await Promise.all([
        settingObjectStore.delete("cognitoIdToken"),
        settingObjectStore.delete("cognitoAccessToken"),
        settingObjectStore.delete("cognitoRefreshToken")
    ])
    window.location.reload()
}

export const login = async (email: string, password: string) => {
    const response = await publicRequest.post("/auth/user", { email, password });
    await Promise.all([
        settingObjectStore.put("cognitoIdToken", response.data["cognito_id_token"]),
        settingObjectStore.put("cognitoAccessToken", response.data["cognito_access_token"]),
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