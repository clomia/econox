import { api } from "../../../modules/request";
import { UnivariateElements, Lang } from "../../../modules/state";
import type { ElementType } from "../../../modules/state";

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
 * UnivariateElements를 세팅합니다.
 * 이 함수가 실행된 이후 UnivariateElements를 통해 데이터에 접근 가능해집니다.
 */
export const setElements = async () => {
    let lang: string = "en";
    const unsubscribe = Lang.subscribe((_lang: string) => { lang = _lang; });
    const univariateElements = await api.member.get("/feature/user/elements", { params: { lang } });
    UnivariateElements.set(univariateElements.data);
    unsubscribe();
};