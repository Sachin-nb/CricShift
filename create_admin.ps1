$adminDir = "C:\Users\sachi\OneDrive\Documents\Project Phase\Cricshift-main\src\app\admin"
$componentsDir = "C:\Users\sachi\OneDrive\Documents\Project Phase\Cricshift-main\src\components\cricshift"

New-Item -ItemType Directory -Force -Path $adminDir
New-Item -ItemType Directory -Force -Path $componentsDir

$layoutCode = @"
import { AdminSidebar } from "@/components/cricshift/admin-sidebar"

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-black text-white">
      <AdminSidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
"@

$pageCode = @"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Activity, Users, Zap, Database } from "lucide-react"

export default function AdminDashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Monitor system performance, manage users, and configure the momentum engine.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Matches Analyzed</CardTitle>
            <Activity className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">1,248</div>
            <p className="text-xs text-zinc-400">+20% from last month</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Simulations</CardTitle>
            <Zap className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">12</div>
            <p className="text-xs text-zinc-400">Currently running</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Registered Users</CardTitle>
            <Users className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">573</div>
            <p className="text-xs text-zinc-400">+48 new this week</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Database className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">99.9%</div>
            <p className="text-xs text-emerald-500">All systems operational</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Matches Table */}
        <Card className="col-span-4 bg-zinc-950 border-zinc-800 text-white">
          <CardHeader>
            <CardTitle>Recent Match Processing</CardTitle>
            <CardDescription className="text-zinc-400">Live status of the shift detection engine.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800 hover:bg-zinc-900/50">
                  <TableHead className="text-zinc-300">Match ID</TableHead>
                  <TableHead className="text-zinc-300">Status</TableHead>
                  <TableHead className="text-zinc-300">Shifts Detected</TableHead>
                  <TableHead className="text-right text-zinc-300">Processed At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow className="border-zinc-800 hover:bg-zinc-900/50">
                  <TableCell className="font-medium">IND vs AUS (T20)</TableCell>
                  <TableCell><Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Completed</Badge></TableCell>
                  <TableCell>4</TableCell>
                  <TableCell className="text-right text-zinc-400">2 mins ago</TableCell>
                </TableRow>
                <TableRow className="border-zinc-800 hover:bg-zinc-900/50">
                  <TableCell className="font-medium">ENG vs NZ (ODI)</TableCell>
                  <TableCell><Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20">Processing</Badge></TableCell>
                  <TableCell>2</TableCell>
                  <TableCell className="text-right text-zinc-400">Just now</TableCell>
                </TableRow>
                <TableRow className="border-zinc-800 hover:bg-zinc-900/50">
                  <TableCell className="font-medium">SA vs PAK (T20)</TableCell>
                  <TableCell><Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Completed</Badge></TableCell>
                  <TableCell>7</TableCell>
                  <TableCell className="text-right text-zinc-400">1 hour ago</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card className="col-span-3 bg-zinc-950 border-zinc-800 text-white">
          <CardHeader>
            <CardTitle>Engine Configuration</CardTitle>
            <CardDescription className="text-zinc-400">Manage global processing settings.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between space-x-2">
              <div className="flex flex-col space-y-1">
                <span className="text-sm font-medium leading-none">Auto-Simulate Matches</span>
                <span className="text-sm text-zinc-400">Automatically run the shift detector on new live matches.</span>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <div className="flex flex-col space-y-1">
                <span className="text-sm font-medium leading-none">Strict Shift Threshold</span>
                <span className="text-sm text-zinc-400">Require higher momentum delta to trigger a 'Turning Point'.</span>
              </div>
              <Switch />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <div className="flex flex-col space-y-1">
                <span className="text-sm font-medium leading-none">Debug Mode</span>
                <span className="text-sm text-zinc-400">Log detailed engine metrics to the database.</span>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
"@

$sidebarCode = @"
"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, Users, Activity, Settings, Database } from "lucide-react"

export function AdminSidebar() {
  const pathname = usePathname()
  
  const routes = [
    {
      href: "/admin",
      label: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      href: "/admin/matches",
      label: "Matches",
      icon: Activity,
    },
    {
      href: "/admin/users",
      label: "Users",
      icon: Users,
    },
    {
      href: "/admin/database",
      label: "Database",
      icon: Database,
    },
    {
      href: "/admin/settings",
      label: "Settings",
      icon: Settings,
    },
  ]

  return (
    <div className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col h-screen sticky top-0">
      <div className="h-16 flex items-center px-6 border-b border-zinc-800">
        <h2 className="text-lg font-semibold tracking-tight text-emerald-500">Cricshift Admin</h2>
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2">
        {routes.map((route) => {
          const isActive = pathname === route.href
          const Icon = route.icon
          return (
            <Link
              key={route.href}
              href={route.href}
              className={`flex items-center space-x-3 px-3 py-2 rounded-md transition-colors ${
                isActive 
                  ? "bg-zinc-800 text-white" 
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="text-sm font-medium">{route.label}</span>
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-zinc-800">
        <div className="flex items-center space-x-3 px-3 py-2 rounded-md bg-zinc-900 border border-zinc-800">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs font-medium text-zinc-300">Engine Online</span>
        </div>
      </div>
    </div>
  )
}
"@

$layoutCode | Out-File -FilePath "$adminDir\layout.tsx" -Encoding utf8
$pageCode | Out-File -FilePath "$adminDir\page.tsx" -Encoding utf8
$sidebarCode | Out-File -FilePath "$componentsDir\admin-sidebar.tsx" -Encoding utf8

Write-Host "Admin page files created successfully."
