import axios from "axios";
import ISO6391 from "iso-639-1";
import * as yaml from "js-yaml";
import { settingObjectStore } from "./_storage";
import type { UiText } from "../static/UiText";

interface UiTextObjectType { // yaml 파일 데이터
    [key: string]: { [key: string]: string }
}

/**
 * 서버로부터 UiText.yaml 파일을 불러와 오브젝트로 반환합니다.
 */
const getUiTextObject = async () => {
    const requests = axios.create({ baseURL: window.location.origin });
    const uiTextYaml = await requests.get("/static/UiText.yaml")
    return yaml.load(uiTextYaml.data) as UiTextObjectType;
}

export const currentLang = async () => {
    return await settingObjectStore.get("lang")
}

/**
 * 브라우저에 언어를 세팅하고 언어와 언어에 대한 텍스트 매핑 오브젝트를 반환합니다.
 */
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
    }, {}) as UiText;
    return { lang, text }
}

/**
 * UiText.yaml로부터 사용 가능한 언어 목록을 반환합니다.
 */
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

/**
 * 언어를 변경한 뒤 언어데이터를 다시 세팅합니다.
 * 반환값은 loadUiText와 같은 형식입니다.
 */
export const changeLang = async (lang: string) => {
    await settingObjectStore.put("lang", lang) // 언어 바꾸고
    return await loadUiText() // 바꾼 언어에 맞게 다시 로딩해서 반환
}