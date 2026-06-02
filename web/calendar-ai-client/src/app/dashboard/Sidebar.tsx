"use client";

// change the icon from -> and <- to a hamburger menu icon and a close icon, and add a tooltip to the button
// the sidebar should also have a smooth transition when collapsing and expanding, and the content area should adjust accordingly
// the sidebar should also have a dark mode toggle button that allows users to switch between light and dark themes

import { useState } from "react";

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`bg-gray-200 p-4 transition-all duration-300 ${collapsed ? "w-10" : "w-64"}`}>
      <button onClick={() => setCollapsed(!collapsed)} 
      className="mb-4 text-gray-600 hover:text-gray-900" title={collapsed ? "Open Sidebar" : "Close Sidebar"}>
        {collapsed ? "→" : "←"}
      </button>
      {!collapsed && <div>Sidebar</div>}
    </aside>
  );
}
