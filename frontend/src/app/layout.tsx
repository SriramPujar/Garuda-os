import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/sidebar";
import TopBar from "@/components/top_bar";
import BottomNav from "@/components/bottom_nav";

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
      <body className="min-h-full flex flex-col md:flex-row h-screen w-screen overflow-hidden bg-background text-foreground">
        {/* Left Navigation Sidebar (Desktop) */}
        <div className="hidden md:block shrink-0">
          <Sidebar />
        </div>

        {/* Dynamic Center Workstation */}
        <div className="flex flex-1 flex-col overflow-hidden ml-0 md:ml-14 pb-14 md:pb-0">
          <TopBar />
          
          {/* Center Content Panel */}
          <main className="flex-1 overflow-y-auto bg-background/50 px-4 py-4 md:px-8 md:py-6">
            {children}
          </main>

          {/* Bottom Navigation (Mobile) */}
          <BottomNav />
        </div>
      </body>
    </html>
  );
}
