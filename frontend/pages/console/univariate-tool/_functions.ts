import { UnivariateElements } from "../../../modules/state";
import type { UnivariateElementType } from "../../../modules/state"

class ElementList {

    static list: UnivariateElementType[] = [];

    static subscribe() {
        UnivariateElements.subscribe((value) => {
            ElementList.list = value;
        });
    }
}

ElementList.subscribe()
