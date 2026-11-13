import "./globals.css";

export const metadata = {
  title: "Program OS — Atlas",
  description: "Evidence-grounded portfolio control and decision intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
