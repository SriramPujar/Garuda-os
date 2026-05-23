import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/sidebar";
import TopBar from "@/components/top_bar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Garuda Dharma OS",
  description: "Lifelong spiritual intelligence companion built with Antigravity 2.0 Agent Manager",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex h-screen w-screen overflow-hidden bg-background text-foreground">
        {/* Left Navigation Sidebar */}
        <Sidebar />

        {/* Dynamic Center Workstation */}
        <div className="flex flex-1 flex-col overflow-hidden ml-14">
          <TopBar />
          
          {/* Center Content Panel */}
          <main className="flex-1 overflow-y-auto bg-background/50 px-8 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
