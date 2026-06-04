import LoginForm from "@/components/LoginForm";

export default function Home() {
  return (
    <main>
      <div className="max-w-sm mx-auto mt-10">
        <h1 className="text-2xl font-bold mb-4">Welcome to Trocks AI Chatbots!</h1>
        <p className="mb-2 text-gray-700">A collection of AI chatbot clients, built and experimented by Trocks AI.</p>
        <p className="mb-2 text-gray-700">Access is restricted to approved testers only. If you would like to try the chatbots, please contact support@tamils.rocks to request a login.</p>
        <p className="mt-4 mb-1 text-gray-700">You can login using:</p>
        <ul className="list-disc list-inside text-gray-700 mb-2">
          <li>Your email and password</li>
          <li>Your Google account via the Sign in with Google button</li>
        </ul>
      </div>
      <LoginForm />
    </main>
  );
}
