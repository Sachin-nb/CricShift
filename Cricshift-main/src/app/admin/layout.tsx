import { AdminSidebar } from "@/components/cricshift/admin-sidebar"

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="relative flex min-h-screen text-white">
      {/* Brand-tinted admin backdrop (soft emerald + gold glows over near-black) */}
      <div
        className="pointer-events-none fixed inset-0 -z-10"
        style={{
          backgroundColor: "#08090c",
          backgroundImage:
            "radial-gradient(55% 45% at 18% 0%, rgba(0,200,83,0.10) 0%, rgba(0,200,83,0) 60%)," +
            "radial-gradient(50% 50% at 100% 100%, rgba(255,193,7,0.07) 0%, rgba(255,193,7,0) 60%)," +
            "linear-gradient(180deg, #0d1117 0%, #0a0b0e 55%, #08090c 100%)",
        }}
      />

      <AdminSidebar />

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-[1400px] px-6 py-8 lg:px-10 lg:py-10">
          {children}
        </div>
      </main>
    </div>
  )
}
