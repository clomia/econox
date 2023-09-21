import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
// 1. writeable 객체 변수명은 CamelCase로 짓는다.
// 2. 가급적 모듈 레벨에 writeable 객체를 선언한다 그래야 import 후 바로 $ 표현식 쓸 수 있다.

export const defaultObject = <T>(defaultValue: T): { [k: string]: T } => new Proxy({}, { get: () => defaultValue });

// ============= 전역적으로 사용되는 상태들 =============

export const Lang = writable("en")
export const Text = writable(defaultObject(""))
export const UserInfo: Writable<boolean | object> = writable(false) // 로그인 되었다면 GET /api/user 응답 객체가 있음


// ============= 기능적으로 사용되는 상태들 =============

export const auth = { // 로그인,회원가입 컴포넌트 상태관리용 
    Toggle: writable({ login: true, signup: false }),
    signup: {
        Step: writable(0),
        EmailConfirmTimeLimit: writable(-1),
        PhoneConfirmTimeLimit: writable(-1),
        InputPhoneNumber: writable(""),
        PaymentError: writable(false),
        InputResult: writable({
            cognitoId: "",
            email: "",
            password: "",
            membership: "",
            currency: "",
            tosspayments: null, // or { card_number, expiration_year, expiration_month, owner_id }
            paypal: null, // or { orderID, facilitatorAccessToken, subscriptionId }
            phone: "",
            reregistration: false,
        }) // DB 유저 생성시 필요한 정보들
    }
}

