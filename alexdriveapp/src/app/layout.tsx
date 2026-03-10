import type { Metadata } from "next";
import { Jost, Inter } from "next/font/google";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { Footer } from "@/components/Footer";
import "./globals.css";

const jost = Jost({
  variable: "--font-jost",
  subsets: ["latin", "cyrillic"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "cyrillic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AlexDrive - Автомобили из Южной Кореи",
  description: "Каталог автомобилей от дилера AlexDrive в Сувоне, Южная Корея",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
        <link rel="preconnect" href="https://img.carmanager.co.kr" />
        <link rel="dns-prefetch" href="https://img.carmanager.co.kr" />
        <link rel="preconnect" href={process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001"} />
      </head>
      <body className={`${jost.variable} ${inter.variable} font-sans antialiased`}>
        <Header />
        <div className="flex">
          <Sidebar />
          <div className="flex min-h-[calc(100vh-4rem)] min-w-0 flex-1 flex-col">
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </div>
      </body>
    </html>
  );
}
