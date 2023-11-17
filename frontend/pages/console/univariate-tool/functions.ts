import { api } from "../../../modules/request";
import { UnivariateElements } from "../../../modules/state";
import type { UnivariateElementType } from "../../../modules/state"

export const deleteElement = async (code: string, code_type: string) => {
    let view: UnivariateElementType[] = [];
    const unsubscribe = UnivariateElements.subscribe((currentList) => {
        view = currentList;
    });
    const target = view.find(ele => ele.code === code && ele.code_type === code_type)
    if (!target) {
        throw new Error("Element does not exists")
    }
    UnivariateElements.set(view.filter(ele => ele !== target))
    try {
        await api.member.delete("/feature/user/element", { params: { code, code_type } })
    } catch (error) {
        view.push(target) // 실패시 다시 삽입 후 올바르게 정렬
        view.sort((e1, e2) => new Date(e2.update_time).getTime() - new Date(e1.update_time).getTime())
        UnivariateElements.set(view)
        throw error
    }
    unsubscribe()
}
