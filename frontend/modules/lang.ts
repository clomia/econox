import axios from "axios"; // api 객체 못씀, api객체가 여기있는걸 써야 함
import ISO6391 from "iso-639-1";
import * as yaml from "js-yaml";
import { generalObjectStore, settingObjectStore } from "../modules/storage";

const YAML_PATH = "/static/multilingual.yaml" // <- 이곳에 UI 다국어 텍스트 정의가 작성되어있습니다.

// LangInfo.langs에서는 언어코드: 언어이름
// Contents의 값에서는 언어코드: 텍스트
export interface Langs {
    [code: string]: string;
}

export interface Contents {
    base?: string;
    [key: string]: string | Langs;
}

export interface LangInfo {
    pin: string; // 설정된 언어
    base: string, // 기본 언어
    langs: Langs; // 지원되는 언어들
    contents: Contents; // 텍스트 컨텐츠
}

// UI요소에 사용되는 객체, 적절한 언어 텍스트를 제공한다!

/**
    * 언어데이터를 불러옵니다. 브라우저로부터 캐싱됩니다.  
    * 스토리지에 직접 접근하지 말고 이 함수를 사용하세요!  
    * @returns 언어데이터 (설정언어, 언어목록, 컨텐츠)
*/
export async function load(): Promise<LangInfo> {
    let multilingual: Contents = await generalObjectStore.get("multilingual");
    let pin: string = await settingObjectStore.get("lang");

    if (!multilingual) {
        // 언어 데이터가 없다면 불러오기
        const requests = axios.create({ baseURL: window.location.origin });
        const res = await requests.get(YAML_PATH);
        multilingual = yaml.load(res.data) as Contents;
        await generalObjectStore.put("multilingual", multilingual);
    }
    if (!pin) {
        // 언어 지정이 안되어있다면 기본값을 지정
        pin = multilingual.base;
        await settingObjectStore.put("lang", pin);
    }
    const base = multilingual.base

    // multilingual 객체에서 사용되는 모든 언어를 Langs 객체로 파싱
    const langs: Langs = {}; // 지원 언어 목록
    const accumulateSet = new Set<string>(); // 누산하면서 중복 제거하는 용도
    for (const key in multilingual) {
        const content = multilingual[key];
        if (key !== "base" && typeof content === "object") {
            for (const lang in content) {
                accumulateSet.add(lang);
            }
            if (!content[base]) {
                throw new Error(`${key} 항목에 대한 기본 언어(${base})가 작성되지 않았습니다!`);
            }
        }
    }
    accumulateSet.forEach((lang) => {
        langs[lang] = ISO6391.getName(lang);
    });

    // contents는 multilingual객체에서 base 속성을 제거한것이다.
    const contents = { ...multilingual };
    delete contents.base;
    return { pin, base, langs, contents };
}

/**
 * 언어데이터를 multilingual.yaml 파일과 동기화합니다.
 * 설정값(기본언어)은 변경되지 않습니다.
 * @returns 언어데이터 (설정언어, 언어목록, 컨텐츠)
*/
export async function init(): Promise<LangInfo> {
    await generalObjectStore.delete("multilingual"); // 기존꺼 지우고
    return await load(); // 다시 로딩 (서버로 API 요청)
}


/**
 * 언어설정을 변경합니다 반영하려면 새로고침 해야합니다.
 * @param lang - 변경후 언어 코드
 */
export async function update(lang: string): Promise<void> {
    await settingObjectStore.put("lang", lang); // 선택된 언어로 변경
}

/**
 * 언어 설정에 적합한 텍스트를 제공합니다.
 */
export async function loadText(): Promise<{ [key: string]: string }> {
    const langInfo = await load();
    const pairs = Object.entries(langInfo.contents).reduce((acc, [key, value]) => {
        const pair = (value as Langs); // 언어코드 : 텍스트
        return { ...acc, [key]: pair[langInfo.pin] || pair[langInfo.base] }
    }, {}); // pairs = { 텍스트키: 설정된 언어로 된 텍스트 , ... }
    return pairs
}