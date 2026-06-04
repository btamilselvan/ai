export default function Home() {
    // this is the home page that users see after logging in, it can display some basic information about the user and provide links to different sections of the dashboard
    // this page should include a welcome message, the user's name (if available), and a brief overview of the features available in the dashboard. It can also include some quick links to popular sections of the dashboard, such as "My Chatbots", "Calendar Integration", and "Settings". The design should be clean and user-friendly, with clear navigation to help users find what they need quickly.
    // add information saying this is a demo application and not a real product, and that the calendar integration works for only for the allowed test accounts.
    return (
        <main className="p-4">
            <h1 className="text-2xl font-bold mb-4">Welcome to Trocks AI Chatbots Dashboard!</h1>
            <p className="mb-4">Here you can interact with chatbots created by Trocks AI.</p>
            <p className="mb-4 text-sm text-gray-500">
                Note: This is a demo application and not a real product. The calendar integration is only available for allowed test accounts. Contact support if you want to get access or have any questions.
            </p>
            <p className="mb-4">Select a chatbot from the navigation bar to get staterd!</p>
            {/* <div className="space-y-2">
                <a href="/dashboard/my-chatbots" className="text-blue-500 hover:underline block">My Chatbots</a>
                <a href="/dashboard/calendar-integration" className="text-blue-500 hover:underline block">Calendar Integration</a>
                <a href="/dashboard/settings" className="text-blue-500 hover:underline block">Settings</a>
            </div> */}
        </main>
    );
}