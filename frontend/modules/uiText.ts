import axios from "axios";
import ISO6391 from "iso-639-1";
import * as yaml from "js-yaml";

import { settingObjectStore } from "./_storage";

export const settingKey = {
    lang: "uiTextLang",
    text: "uiText",
}

interface UiTextObjectType { // yaml 파일 데이터
    [key: string]: { [key: string]: string }
}

const getUiTextObject = async () => {
    const requests = axios.create({ baseURL: window.location.origin });
    const uiTextYaml = await requests.get("/static/uiText.yaml")
    return yaml.load(uiTextYaml.data) as UiTextObjectType;
}


export const loadUiText = async () => {
    let [text, lang] = await Promise.all([
        settingObjectStore.get(settingKey.text),
        settingObjectStore.get(settingKey.lang),
    ])
    if (!lang) { // 언어 설정이 없으면 영어로 설정
        lang = "en"
        settingObjectStore.put(settingKey.lang, "en");
    }
    if (!text) {
        const uiTextObject = await getUiTextObject()
        text = Object.entries(uiTextObject).reduce((acc, [key, value]) => {
            return { ...acc, [key]: value[lang] || value["en"] }
        }, {});
        settingObjectStore.put(settingKey.text, text);
    }
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

export const changeLang = async (langCode: string) => {
    await Promise.all([
        settingObjectStore.put(settingKey.lang, langCode), // 언어 바꾸고
        settingObjectStore.delete(settingKey.text) // 기존 텍스트 지우고
    ])
    return await loadUiText() // 바꾼 언어에 맞게 다시 로딩해서 반환
}