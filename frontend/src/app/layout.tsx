import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const displayFont = Inter({
  variable: "--font-display",
  subsets: ["latin"],
});

const monoFont = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  themeColor: "#0A0C0E",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "EMACE | Industrial Command Center",
  description: "Critical Mission Control for Intelligent Multi-Agent Systems.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "EMACE",
  },
};

import ToastContainer from "@/components/ui/Toast";
import { WebPerformance } from "@/components/performance/web-vitals";
import { Providers } from "@/components/providers/QueryProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" style={{ colorScheme: 'dark' }}>
      <body
        className={`${displayFont.variable} ${monoFont.variable} antialiased selection:bg-primary/30 selection:text-primary-foreground bg-midnight text-foreground`}
      >
        <div className="bg-noise" aria-hidden="true" />
        <Providers>
          <div className="min-h-screen relative overflow-hidden">
            {/* Mission Critical Background - Mesh Gradients */}
            <div className="fixed top-[-20%] left-[-10%] w-[60%] h-[60%] bg-steel/20 blur-[150px] rounded-full pointer-events-none opacity-50" />
            <div className="fixed bottom-[-10%] right-[-5%] w-[50%] h-[50%] bg-midnight blur-[120px] rounded-full pointer-events-none opacity-50" />
            
            <div className="relative z-10">
              {children}
            </div>
            <ToastContainer />
            <WebPerformance />
          </div>
        </Providers>
      </body>
    </html>
  );
}
