// layout with left sidebar and right content area, a top header bar with title and a bottom footer bar with copyright info
// the side bar can be collapsible and the content area should take up the remaining space

import Sidebar from "./Sidebar";
import { cookies } from "next/headers";

const props = {
  headerTitle: "Trocks AI Chatbots",
}

export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {


  const cookiesStore = await cookies();
  const isGoogleAuthenticated = !!cookiesStore.get("googleAccessToken");


  return (

    <div className="h-screen flex flex-col">
      <header className="bg-gray-800 text-white p-4">
        <h1 className="text-xl font-bold">{props.headerTitle}</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar googleAuthenticated={isGoogleAuthenticated} />
        <main className="flex-1 p-4 overflow-hidden flex flex-col">{children}</main>
      </div>
      <footer className="bg-gray-800 text-white p-4 text-center">
        &copy; {new Date().getFullYear()} {props.headerTitle}. All rights reserved.
      </footer>
    </div>

  );
}