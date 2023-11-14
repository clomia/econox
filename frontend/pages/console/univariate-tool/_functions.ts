import { api } from "../../../modules/request";
import { UnivariateElements } from "../../../modules/state";
import type { UnivariateElementType } from "../../../modules/state"

class ElementList {
    // 스토어 값 읽기만을 위해 사용됨
    private view: UnivariateElementType[] = [];

    constructor() {
        UnivariateElements.subscribe((value) => {
            this.view = value;
        });
    }

    async append(code: string, code_type: "symbol" | "country") {
        if (this.view.some(ele => ele.code === code && ele.code_type === code_type)) {
            throw new Error("Element already exists")
        }
        const target = { code, code_type, update_time: (new Date()).toISOString() }
        UnivariateElements.set([target, ...this.view])
        try {
            await api.member.post("/feature/user/element", {}, { params: { code, code_type } })
        } catch (error) {
            UnivariateElements.set(this.view.filter(ele => ele !== target))
            throw error
        }
    }

    async delete(code: string, code_type: "symbol" | "country") {
        const target = this.view.find(ele => ele.code === code && ele.code_type === code_type)
        if (!target) {
            throw new Error("Element does not exists")
        }
        UnivariateElements.set(this.view.filter(ele => ele !== target))
        try {
            await api.member.delete("/feature/user/element", { params: { code, code_type } })
        } catch (error) {
            this.view.push(target) // 실패시 다시 삽입 후 올바르게 정렬
            this.view.sort((e1, e2) => new Date(e2.update_time).getTime() - new Date(e1.update_time).getTime())
            UnivariateElements.set(this.view)
            throw error
        }
    }
}
