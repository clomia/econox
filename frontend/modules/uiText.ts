import axios from "axios";
import ISO6391 from "iso-639-1";
import * as yaml from "js-yaml";

import { settingObjectStore } from "./_storage";

interface UiTextObjectType { // yaml 파일 데이터
    [key: string]: { [key: string]: string }
}

const getUiTextObject = async () => {
    const requests = axios.create({ baseURL: window.location.origin });
    const uiTextYaml = await requests.get("/static/uiText.yaml")
    return yaml.load(uiTextYaml.data) as UiTextObjectType;
}

export const currentLang = async () => {
    return await settingObjectStore.get("lang")
}

export const loadUiText = async () => {
    let lang = await settingObjectStore.get("lang")

    if (!lang) { // 언어 설정이 없는 경우
        const browserLanguage = navigator.language.split("-")[0];
        lang = browserLanguage in await supportedLangs() ? browserLanguage : "en"
        settingObjectStore.put("lang", lang);
    }
    const uiTextObject = await getUiTextObject()
    const text = Object.entries(uiTextObject).reduce((acc, [key, value]) => {
        return { ...acc, [key]: value[lang] || value["en"] }
    }, {});
    return { lang, text }
}

export const supportedLangs = async () => {
    const uiTextObject = await getUiTextObject()

    const nameList: { [key: string]: string } = {}; // 언어코드: 언어이름
    const accumulateSet = new Set<string>(); // 누산하면서 중복 제거하는 용도
    for (const key in uiTextObject) {
        const multilingual = uiTextObject[key];
        for (const lang in multilingual) {
            accumulateSet.add(lang);
        }
    }
    accumulateSet.forEach((lang) => {
        nameList[lang] = ISO6391.getName(lang);
    });
    return nameList
}

export const changeLang = async (lang: string) => {
    await settingObjectStore.put("lang", lang) // 언어 바꾸고
    return await loadUiText() // 바꾼 언어에 맞게 다시 로딩해서 반환
}