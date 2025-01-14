import { get } from "svelte/store";

import { Text } from "./state";
import { api } from "../modules/request";

async function loadPaypalScript(clientId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      const script = document.createElement("script");
      script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&vault=true&intent=subscription`;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Failed to load PayPal script"));
      document.head.appendChild(script);
    } catch (error) {
      reject(error);
    }
  });
}

interface PaypalWidgetOptions {
  planName: string;
  startTime?: string | null;
  onApprove?: (subscriptionId: string, orderId: string) => Promise<any>;
  onLoad?: () => void;
}

/**
 *
 * @param startTime 청구 시작일시(ISO-8601), 기본값: 즉시
 * @param onApprove 작업 완료 후 호출될 함수, 구독 id, order id를 인자로 받아야 함
 * @param onLoad 위젯 로딩 후 호출될 함수
 */
export const paypalWidget = async ({
  planName,
  startTime = null,
  onApprove = async () => {},
  onLoad = () => {},
}: PaypalWidgetOptions) => {
  const resp = await api.public.get("/paypal/plans");
  const clientId = resp.data["client_id"];
  const planId = resp.data["plan_id"][planName];

  await loadPaypalScript(clientId);

  const paypalGround = document.createElement("div");
  Object.assign(paypalGround.style, {
    position: "fixed",
    top: "0",
    left: "0",
    width: "100%",
    height: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: "9999",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
  });
  const paypalContainer = document.createElement("div");
  Object.assign(paypalContainer.style, {
    width: "20rem",
    height: "13rem",
    borderRadius: "0.5rem",
    border: "thin solid rgba(255, 255, 255, 0.1)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    background: "linear-gradient(to bottom, #3b3c3f, #263c42",
  });
  const text = get(Text);
  const closeButton = document.createElement("button");
  closeButton.innerText = text.Close;
  Object.assign(closeButton.style, {
    cursor: "pointer",
    minWidth: "200px",
    height: "2rem",
    borderRadius: "0.3rem",
    color: "var(--white)",
    backgroundColor: "#242626",
  });
  closeButton.addEventListener("mouseover", () => {
    closeButton.style.backgroundColor = "#3D3F40"; // Change color to blue on hover
  });
  closeButton.addEventListener("mouseleave", () => {
    closeButton.style.backgroundColor = "#242626"; // Revert color back to white when hover ends
  });
  closeButton.addEventListener("click", () => {
    document.body.removeChild(paypalGround);
  });

  const paypalSection = document.createElement("section");
  paypalSection.className = "paypal-sdk";

  const paypalButton = document.createElement("div");
  paypalButton.id = "paypal-button";

  paypalSection.appendChild(paypalButton);
  paypalContainer.appendChild(paypalSection);
  paypalContainer.appendChild(closeButton);
  paypalGround.appendChild(paypalContainer);
  document.body.appendChild(paypalGround);

  (window as any).paypal
    .Buttons({
      style: {
        shape: "rect",
        color: "black",
        layout: "vertical",
        label: "paypal",
      },
      createSubscription: (data: any, actions: any) => {
        return actions.subscription.create({
          plan_id: planId,
          start_time: startTime,
        });
      },
      onApprove: async (data: any, actions: any) => {
        document.body.removeChild(paypalGround);
        await onApprove(data.subscriptionID, data.orderID);
      },
    })
    .render(`#${paypalButton.id}`);
  onLoad();
};
