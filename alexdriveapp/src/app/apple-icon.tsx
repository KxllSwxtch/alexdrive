import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#101010",
          borderRadius: "32px",
          fontSize: 80,
          fontWeight: 700,
          color: "#D4AF37",
          fontFamily: "Arial, Helvetica, sans-serif",
        }}
      >
        AD
      </div>
    ),
    { ...size }
  );
}
