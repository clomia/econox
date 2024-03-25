<script lang="ts">
  import { onMount } from "svelte";
  import * as PortOne from "@portone/browser-sdk/v2";

  onMount(async () => {
    const issueResponse = await PortOne.requestIssueBillingKey({
      storeId: "store-bd7abf6b-fb2c-4f8e-b35c-93189fb5b5e7",
      channelKey: "channel-key-19dbbf97-9a55-475d-a030-1935accc819e",
      billingKeyMethod: "CARD",
      issueId: "120302130",
      isTestChannel: true,
      customer: {
        customerId: "104903",
        fullName: "원정후",
        phoneNumber: "+8201075287237",
        email: "cloe001000@gmail.com",
      },
    });
    // 빌링키가 제대로 발급되지 않은 경우 에러 코드가 존재합니다
    if (issueResponse.code != null) {
      return alert(issueResponse.message);
    }

    console.log("빌링키:", issueResponse.billingKey);
  });
</script>
