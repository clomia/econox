import { api } from "../../../modules/request";
import { UnivariateElements } from "../../../modules/state";
import type { ElementType } from "../../../modules/state"

export const deleteElement = async (code: string, section: string) => {
    let view: ElementType[] = [];
    const unsubscribe = UnivariateElements.subscribe((currentList) => {
        view = currentList;
    });
    const target = view.find(ele => ele.code === code && ele.section === section)
    if (!target) {
        throw new Error("Element does not exists")
    }
    UnivariateElements.set(view.filter(ele => ele !== target))
    try {
        await api.member.delete("/feature/user/element", { params: { code, section } })
    } catch (error) {
        view.push(target) // 실패시 다시 삽입 후 올바르게 정렬
        view.sort((e1, e2) => new Date(e2.update_time as string).getTime() - new Date(e1.update_time as string).getTime())
        UnivariateElements.set(view)
        throw error
    }
    unsubscribe()
}
