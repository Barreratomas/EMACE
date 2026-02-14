import LoginForm from '@/features/auth/components/LoginForm';

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient decoration */}
      <div className="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-transparent via-primary to-transparent" />
        <div className="absolute bottom-0 left-0 w-full h-1 bg-linear-to-r from-transparent via-secondary to-transparent" />
        <div className="absolute top-1/2 left-0 w-full h-px bg-zinc-900" />
        <div className="absolute top-0 left-1/2 w-px h-full bg-zinc-900" />
      </div>
      
      <div className="relative z-10 w-full flex justify-center">
        <LoginForm />
      </div>

      {/* Background glitch elements */}
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary/5 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-secondary/5 blur-[120px] rounded-full pointer-events-none" />
    </main>
  );
}
