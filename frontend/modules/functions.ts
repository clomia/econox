import Swal from "sweetalert2"

import * as api from "./api"
import { settingObjectStore } from "./_storage"
import { loadUiText } from "./uiText"

const logout = async () => {
    await Promise.all([
        settingObjectStore.delete(api.settingKey.idToken),
        settingObjectStore.delete(api.settingKey.refreshToken)
    ])
    window.location.reload()
}

const logoutWithAlert = async (message: string) => {
    await Swal.fire({
        icon: 'error',
        text: message,
        confirmButtonText: (await loadUiText()).text.ok,
    })
    await logout()
}