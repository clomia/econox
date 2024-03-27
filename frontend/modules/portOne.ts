// PortOne 빌링 키 발급 SDK를 함수로 제공합니다.

import * as PortOne from "@portone/browser-sdk/v2";
import { swal } from "./functions";

/**
 * @param user
 * @returns 빌링 키 문자열
 */
export const getBillingKey = async (
  userId: string,
  userEmail: string,
  errorReload = true
) => {
  const issueResponse = await PortOne.requestIssueBillingKey({
    storeId: "store-bd7abf6b-fb2c-4f8e-b35c-93189fb5b5e7",
    channelKey: "channel-key-19dbbf97-9a55-475d-a030-1935accc819e",
    billingKeyMethod: "CARD",
    isTestChannel: true,
    issueId: Math.random().toString().slice(2),
    customer: {
      customerId: userId.slice(0, 20),
      email: userEmail,
    },
  });
  if (issueResponse?.code == null) {
    return issueResponse?.billingKey;
  } else {
    await swal(issueResponse?.message || "");
    if (errorReload) {
      location.reload();
    } else {
      throw Error(issueResponse?.message);
    }
  }
};
