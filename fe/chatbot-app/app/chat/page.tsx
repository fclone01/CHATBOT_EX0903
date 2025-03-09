// app/chat/page.tsx
import { redirect } from 'next/navigation';

export default function ChatPage() {
  // Redirect to a default route that doesn't show any chat selected
  redirect('/chat/new');
}