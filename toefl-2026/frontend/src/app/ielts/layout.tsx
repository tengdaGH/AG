export default function IELTSLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex flex-col h-screen w-screen overflow-hidden bg-white antialiased">
            {children}
        </div>
    );
}
