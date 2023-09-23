import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import type { UiText } from "../static/UiText";
// 1. writeable 객체 변수명은 CamelCase로 짓는다.
// 2. 가급적 모듈 레벨에 writeable 객체를 선언한다 그래야 import 후 바로 $ 표현식 쓸 수 있다.

// ============= 필요한 타입 정의 =============
export const defaultObject: any = (defaultValue: string) => new Proxy({}, { get: () => defaultValue });

export interface UserDetail {
    id: string;
    name: string;
    email: string;
    membership: "basic" | "professional";
    signup_date: string;
    next_billing_date: string;
    billing: {
        currency: "USD" | "KRW";
        transactions: {
            time: string;
            name: string;
            amount: number;
            method: string;
        }[];
    };
}

type PayPalType = {
    order: string;
    subscription: string;
} | null;

type TossPaymentsType = {
    card_number: string;
    expiration_year: string;
    expiration_month: string;
    owner_id: string;
} | null;

interface InputResultType {
    email: string;
    password: string;
    membership: string;
    currency: string;
    tosspayments: TossPaymentsType;
    paypal: PayPalType;
    phone: string;
}

// ============= 전역적으로 사용되는 상태들 =============

export const Lang = writable("en")
export const Text: Writable<UiText> = writable(defaultObject(""))
export const UserInfo: Writable<boolean | UserDetail> = writable(false) // 로그인 되었다면 GET /api/user 응답 객체가 있음


// ============= 기능적으로 사용되는 상태들 =============

export const auth = { // 로그인,회원가입 컴포넌트 상태관리용 
    Toggle: writable({ login: true, signup: false }),
    signup: {
        Step: writable(0),
        EmailConfirmTimeLimit: writable(-1),
        PhoneConfirmTimeLimit: writable(-1),
        InputPhoneNumber: writable(""),
        PaymentError: writable(false),
        Reregistration: writable(false),
        InputResult: writable<InputResultType>({
            email: "",
            password: "",
            membership: "",
            currency: "",
            tosspayments: null,
            paypal: null,
            phone: "",
        })
    }
}

