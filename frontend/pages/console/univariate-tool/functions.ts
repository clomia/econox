import type { NumberFormat } from "libphonenumber-js";
import { api } from "../../../modules/request";
import { Lang } from "../../../modules/state";
import { UnivariateElements, UnivariateFactors, UnivariateElementsLoaded, UnivariateFactorsProgress } from "../../../modules/state";
import type { ElementType, FactorType } from "../../../modules/state";

/**
 * 요소를 제거합니다.   
 * UnivariateElements 배열에서 제거한 후 백엔드에 삭제 요청을 보냅니다.  
 * 백엔드가 삭제에 실패한 경우 해당 요소를 다시 삽입하여 동기화 한 후 에러를 던집니다.  
 */
export const deleteElement = async (code: string, section: string) => {
    let view: ElementType[] = [];
    const unsubscribe = UnivariateElements.subscribe((currentList) => {
        view = currentList;
    });
    const target = view.find(ele => ele.code === code && ele.section === section);
    if (!target) {
        throw new Error("Element does not exists");
    }
    UnivariateElements.set(view.filter(ele => ele !== target));
    try {
        await api.member.delete("/feature/user/element", { params: { code, section } });
    } catch (error) {
        view.push(target); // 실패시 다시 삽입 후 올바르게 정렬
        view.sort(
            (e1, e2) => new Date(e2.update_time as string).getTime() - new Date(e1.update_time as string).getTime()
        );
        UnivariateElements.set(view);
        throw error;
    }
    unsubscribe();
};

/**
 * UnivariateElements를 세팅합니다. 이미 세팅된 경우 아무런 동작을 하지 않습니다.
 * 이 함수가 실행된 이후 UnivariateElements를 통해 데이터에 접근 가능해집니다.
 */
export const setElements = async () => {
    let lang: string = "en";
    let univariateElementsLoaded: boolean = false;
    const unsubscribe1 = Lang.subscribe((v: string) => { lang = v; });
    const unsubscribe2 = UnivariateElementsLoaded.subscribe((v: boolean) => { univariateElementsLoaded = v; });

    if (!univariateElementsLoaded) {
        const univariateElements = await api.member.get("/feature/user/elements", { params: { lang } });
        UnivariateElements.set(univariateElements.data);
        UnivariateElementsLoaded.set(true);
    }

    unsubscribe1();
    unsubscribe2();
};

/**
 * Element에 대한 Factor를 UnivariateFactors를 세팅합니다. 이미 세팅된 경우 아무런 동작을 하지 않습니다.  
 * 이 함수가 실행된 이후 UnivariateFactors를 통해 Element에 대한 Factor들에 접근할 수 있습니다.  
 * 이 함수는 오래걸리니 await을 통해 대기하지 말고 UnivariateFactors를 통해 결과를 스트리밍 받으세요.
 * @param ele Factor를 가져올 Element
 */
export const setFactors = async (ele: ElementType) => {
    let lang: string = "en";
    let univariateFactors: { [key: string]: FactorType[]; } = {};
    let univariateFactorsProgress: { [key: string]: number; } = {};

    const unsubscribe1 = Lang.subscribe((v: string) => { lang = v; });
    const unsubscribe2 = UnivariateFactors.subscribe((v) => { univariateFactors = v; });
    const unsubscribe3 = UnivariateFactorsProgress.subscribe((v) => { univariateFactorsProgress = v; });

    const elementKey = `${ele.section}-${ele.code}`;
    if (elementKey in univariateFactors) {
        unsubscribe1(); // 이미 세팅이 된 경우 아무런 동작 안함
        unsubscribe2();
        unsubscribe3();
        return;
    }

    let page = 0;
    const accumulated: FactorType[] = [];
    while (true) {
        const resp = await api.member.get("/feature/factors", {
            "params": {
                "element_code": ele.code,
                "element_section": ele.section,
                "lang": lang,
                "page": ++page, // 현재 페이지를 알아야 하므로 전위 연산 사용
            }
        });
        const factors: FactorType[] = resp.data["factors"];
        const totalPages: number = resp.data["pages"];

        accumulated.push(...factors);
        UnivariateFactors.set({ ...univariateFactors, [elementKey]: accumulated });
        UnivariateFactorsProgress.set({ ...univariateFactorsProgress, [elementKey]: page / totalPages });

        if (totalPages === page) { // 현재 페이지가 마지막이면 종료
            break;
        }
    };

    unsubscribe1();
    unsubscribe2();
    unsubscribe3();
};