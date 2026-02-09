import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import AuthButton from "../components/AuthButton";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "lex",
  description: "lex",
};

import { SWRProvider } from "@/components/SWRProvider";

// ... existing imports

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className} suppressHydrationWarning>
        <SWRProvider>
          <div className="flex items-center justify-between p-4 border-b">
            <Link href={"/"} className="text-xl font-bold">Lex</Link>
            <AuthButton />
          </div>
          {children}
        </SWRProvider>
      </body>
    </html>
  );
}
