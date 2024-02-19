import { writable } from "svelte/store";
import type { UiText } from "../static/UiText";
// * 1. writeable 객체 변수명은 CamelCase로 짓는다. 값 변수명은 snake_case로 짓는다.
// * 2. 모든 타입은 뒤에 Type을 붙인다. writeable을 CamalCase로 쓰니까, 겹치지 않도록

export const defaultObject: any = (defaultValue: any) =>
  new Proxy({}, { get: () => defaultValue });
// ============= 필요한 타입 정의 =============

export interface UserDetailType {
  id: string;
  name: string;
  email: string;
  membership: string;
  signup_date: string;
  next_billing_date: string;
  billing: {
    currency: string;
    registered: boolean;
    status: string;
    method: string;
    transactions: {
      time: string;
      name: string;
      amount: number;
      method: string;
    }[];
  };
}

export type PayPalType = {
  order: string;
  subscription: string;
} | null;

export type TossPaymentsType = {
  card_number: string;
  expiration_year: string;
  expiration_month: string;
  owner_id: string;
} | null;

export interface InputResultType {
  email: string;
  password: string;
  membership: string;
  currency: string;
  tosspayments: TossPaymentsType;
  paypal: PayPalType;
  phone: string;
}

export interface ElementType {
  code: string;
  section: string;
  name: string;
  note: string;
  update_time: string | undefined;
}

export interface FactorType {
  code: string;
  name: string;
  note: string;
  section: {
    code: string;
    name: string;
    note: string;
  };
}

export interface RespPacketType {
  symbols: ElementType[];
}
export interface PacketInfoType {
  query: string;
  resp: RespPacketType;
  elements: ElementType[];
}

export interface CurrentNoteTargetType {
  element: boolean;
  factorSection: boolean;
  factor: boolean;
}

export interface ChartSourceType {
  // key(feature): '{elementSection}-{elementCode}_{factorSectionCode}-{factorCode}'
  [key: string]: [string, string | number][];
}

export interface FeatureType {
  added: string;
  color: string;
  element: {
    section: string;
    code: string;
  };
  factor: {
    section: string;
    code: string;
  };
  name: {
    element: string;
    factor_section: string;
    factor: string;
  };
}

export interface FeatureGroupType {
  id: number;
  created: string;
  name: string;
  description: string;
  chart_type: string;
  public: boolean;
  features: FeatureType[];
}

// Echarts TimeSeries Dataset
export type TsType = [string, ...string[]] | [string, ...number[]];
// key: '{elementSection}-{elementCode}_{factorSectionCode}-{factorCode}'
export type ColorMapType = { [key: string]: string };
// key: Store Name
export type StoreStateType = {
  FgTsOrigin: "before" | "during" | "after";
  FgTsScaled: "before" | "during" | "after";
  FgTsRatio: "before" | "during" | "after";
  FgGranger: "before" | "during" | "after";
  FgCoint: "before" | "during" | "after";
};

// --- key: GroupId ---
export interface FgTsType {
  [key: string]: TsType;
}
export interface FgColorMapType {
  [key: string]: ColorMapType;
}
export interface FgStoreStateType {
  [key: string]: StoreStateType;
}

// ============= 전역적으로 사용되는 상태들 =============

export const Lang = writable("en");
export const Text = writable<UiText>(defaultObject(""));
export const UserInfo = writable<UserDetailType>({
  // 로그인 되었다면 GET /api/user 응답 데이터가 들어옴
  id: "",
  name: "",
  email: "",
  membership: "",
  signup_date: "",
  next_billing_date: "",
  billing: {
    currency: "",
    registered: false,
    status: "",
    method: "",
    transactions: [],
  },
});

// ============= 기능적으로 사용되는 상태들 =============

export const auth = {
  // 로그인,회원가입 컴포넌트 상태관리용
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
    }),
  },
};

// console.SearchBar 상태
export const Packets = writable<
  { query: string; loading: boolean; resp: any }[]
>([]);
export const News = writable<any>({});
export const CountryCodeMap = writable<any>(null);
export const PacketInfo = writable<PacketInfoType>({
  query: "", // 초기값 세팅
  resp: { symbols: [] },
  elements: [],
}); // 검색을 수행하는 비동기 함수는 컴포넌트가 없어진다고 멈추지 않음, 따라서 전역 상태로 관리 가능

// console.univariate-tool 상태
export const UnivariateElements = writable<ElementType[]>([]);
export const UnivariateElementsLoaded = writable(false);
export const UnivariateElementSelected = writable<ElementType | null>(null); // 선택안한 경우 null
export const UnivariateElementQuery = writable("");
// 키는 Element의 "{section}-{code}" 입니다.
export const UnivariateFactors = writable<{ [key: string]: FactorType[] }>({});
export const UnivariateFactorsProgress = writable<{ [key: string]: number }>(
  {}
);
export const UnivariateFactorSelected = writable<FactorType | null>(null);
export const UnivariateFactorQuery = writable("");

export const UnivariateNoteSelected = writable<CurrentNoteTargetType>({
  element: false,
  factorSection: false,
  factor: false,
});
export const UnivariateNoteHovered = writable<CurrentNoteTargetType>({
  element: false,
  factorSection: false,
  factor: false,
});

export const UnivariateChartSource = writable<ChartSourceType>({});

// console.multivariate-tool 상태
export const FeatureGroupsLoaded = writable(false);
export const FeatureGroups = writable<FeatureGroupType[]>([]);
export const FeatureGroupSelected = writable<FeatureGroupType | null>(null);

// console.multivariate-tool -> Chart Data
// Fg(FeatureGroups) Ts(TimeSeries)
export const FgTsOrigin = writable<FgTsType>({});
export const FgTsScaled = writable<FgTsType>({});
export const FgTsRatio = writable<FgTsType>();
export const FgGranger = writable(); // 미구현
export const FgCoint = writable(); // 미구현
// 위의 데이터 스토어 상태 기록자
export const FgStoreState = writable<FgStoreStateType>({});
