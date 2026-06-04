"use client";

// change the icon from -> and <- to a hamburger menu icon and a close icon, and add a tooltip to the button
// the sidebar should also have a smooth transition when collapsing and expanding, and the content area should adjust accordingly
// the sidebar should also have a dark mode toggle button that allows users to switch between light and dark themes

import { useState } from "react";

interface SidebarProps {
  readonly googleAuthenticated: boolean;
}
// type props = Readonly<{
//   googleAuthenticated: boolean;
// }>;

export default function Sidebar({ googleAuthenticated }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  console.log("available chatbots from env variable:", process.env.NEXT_PUBLIC_CHATBOTS);

  return (
    <aside className={`bg-gray-200 p-4 transition-all duration-300 flex flex-col h-full ${collapsed ? "w-10" : "w-64"}`}>
      <button onClick={() => setCollapsed(!collapsed)}
        className="mb-4 text-gray-600 hover:text-gray-900" title={collapsed ? "Open Sidebar" : "Close Sidebar"}>
        {collapsed ? "→" : "←"}
      </button>
      {!collapsed && <div>

        <h2 className="text-lg font-bold mb-2">Available Chatbots</h2>
        <ul className="space-y-2">
          {process.env.NEXT_PUBLIC_CHATBOTS?.split(",").map((chatbot) => {
            const trimmedChatbot = chatbot.trim();
            return (
              <li key={trimmedChatbot}>
                <a href={`/dashboard/${trimmedChatbot.toLowerCase().replace(/\s+/g, "-")}`} className="text-blue-500 hover:underline">
                  {trimmedChatbot}
                </a>
              </li>
            );
          })}
        </ul>

        <div className="mt-4">
          <h2 className="text-lg font-bold mb-2">Authentication Status</h2>
          <p>{googleAuthenticated ? "Authenticated with Google" : "Not authenticated with Google"}</p>
        </div>
      </div>
      }

      <div className="mt-auto">
        <a href="/api/auth/custom/logout" className="text-red-500 hover:underline">
          {!collapsed && "Logout"}
        </a>
      </div>
    </aside>
  );
}
