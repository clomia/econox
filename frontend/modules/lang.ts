import axios from "axios";
import ISO6391 from "iso-639-1";
import * as yaml from "js-yaml";
import { onMount } from "svelte";
import { writable, derived } from "svelte/store";
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

/**
    * 언어데이터를 불러옵니다. 브라우저로부터 캐싱됩니다.  
    * 스토리지에 직접 접근하지 말고 이 함수를 사용하세요!  
    * @returns 언어데이터 (설정언어, 언어목록, 컨텐츠)
*/
export async function load(): Promise<LangInfo> {
    let multilingual: Contents = await generalObjectStore.get("multilingual");
    let lang: string = await settingObjectStore.get("lang");

    if (!multilingual) {
        // 언어 데이터가 없다면 불러오기
        const requests = axios.create({ baseURL: window.location.origin });
        const res = await requests.get(YAML_PATH);
        multilingual = yaml.load(res.data) as Contents;
        await generalObjectStore.put("multilingual", multilingual);
    }
    if (!lang) {
        // 언어 지정이 안되어있다면 기본값을 지정
        lang = multilingual.base;
        await settingObjectStore.put("lang", lang);
    }

    // multilingual 객체에서 사용되는 모든 언어를 Langs 객체로 파싱
    const langs: Langs = {}; // 지원 언어 목록
    const accumulateSet = new Set<string>(); // 누산하면서 중복 제거하는 용도
    for (const key in multilingual) {
        const content = multilingual[key];
        if (key !== "base" && typeof content === "object") {
            for (const lang in content) {
                accumulateSet.add(lang);
            }
            if (!content[multilingual.base]) {
                throw new Error(`${key} 항목에 대한 기본 언어(${multilingual.base})가 작성되지 않았습니다!`);
            }
        }
    }
    accumulateSet.forEach((lang) => {
        langs[lang] = ISO6391.getName(lang);
    });

    // contents는 multilingual객체에서 base 속성을 제거한것이다.
    const contents = { ...multilingual };
    delete contents.base;

    return { pin: lang, base: multilingual.base, langs, contents };
}

/**
 * 서버로부터 언어데이터를 초기화합니다.
 * 설정값은 변경되지 않습니다.
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
 * multilingual.yaml 데이터를 svelte 호환 객체로 반환합니다.
 * @returns 설정된 언어 텍스트를 가지는 객체
 */
export function setup() {
    const baseStore = writable({}); // 내부적으로 사용되는 기본 저장소
    onMount(async () => {
        const langInfo = await load();
        const pairs = Object.entries(langInfo.contents).reduce((acc, [key, value]) => {
            const pair = (value as Langs); // 언어코드 : 텍스트
            return { ...acc, [key]: pair[langInfo.pin] || pair[langInfo.base] }
        }, {}); // pairs = { 텍스트키: 설정된 언어에 맞는 텍스트 , ... }
        baseStore.set(pairs); // 텍스트 매핑 데이터를 저장소에 저장
    });
    // get동작에 대해 값이 없으면 ""를 반환하는 프록시를 가지는 baseStore 래핑 저장소를 만들어서 반환
    const proxyStore = derived(baseStore, $target => {
        return new Proxy($target, {
            get: (target, prop) => {
                return target[prop] || "";
            }
        });
    });
    return proxyStore
}