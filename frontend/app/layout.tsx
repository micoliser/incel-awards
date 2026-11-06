import type { Metadata } from "next";
import { Archivo, Commissioner, Syne } from "next/font/google";
import { SiteFooter } from "@/components/site-footer";
import "./globals.css";

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  display: "swap",
});

const commissioner = Commissioner({
  variable: "--font-commissioner",
  subsets: ["latin"],
  display: "swap",
});

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Incel Group Employee Awards",
    template: "%s · Incel Group Awards",
  },
  description:
    "Yearly employee awards for Incel Group across Tourism, Global, and General recognition.",
  icons: {
    icon: "/global-favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${syne.variable} ${commissioner.variable} ${archivo.variable} h-full antialiased`}
    >
      <body className="weave-ground flex min-h-full flex-col font-sans text-ink">
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
