// app/chat/layout.tsx
export default function ChatLayout({
    children,
  }: {
    children: React.ReactNode
  }) {
    return (
      <section className="h-screen w-full flex">
        {children}
      </section>
    );
  }