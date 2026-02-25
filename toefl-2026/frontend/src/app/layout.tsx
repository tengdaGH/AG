import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TOEFL 2026 Assessment Platform",
  description: "Next-Generation language assessment platform and item bank",
};

import { LanguageProvider } from "@/lib/i18n/LanguageContext";
import { DisableContextMenu } from "@/components/DisableContextMenu";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <DisableContextMenu />
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
