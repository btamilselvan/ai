"use client";

// contains the login form for the application, which allows users to authenticate with their Google account and grant permissions to access their calendar data.
//successful login will redirect the user to the home page where they can interact with the calendar AI features.
import { useState, SubmitEvent } from "react";
import { useRouter } from "next/navigation";

export default function LoginForm() {
    // state variables to track the user's email and password input
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<{ email?: string; password?: string }>({});
    const router = useRouter();

    const validateForm = (): boolean => {
        const newError: { email?: string; password?: string } = {};
        if (!email) {
            newError.email = "Email is required";
        } else if (!/\S+@\S+\.\S+/.test(email)) {
            newError.email = "Email is invalid";
        }
        if (!password) {
            newError.password = "Password is required";
        }
        setError(newError);
        return Object.keys(newError).length === 0;
    }

    // function to handle form submission
    const handleSubmit = async (e: SubmitEvent) => {
        console.log("Login form submitted with email:", email);
        e.preventDefault();
        if (!validateForm()) {
            console.error("Form validation failed with errors:", error);
            return;
        }
        // send a POST request to the /api/login URL with the email and password
        // the API route (/api/login/route.ts) will handle the authentication logic and return a response indicating success or failure
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, loginPassword: password }),
        });

        if (response.ok) {
            // console.log("Login successful");
            // print response data for debugging
            const data = await response.json();
            console.log("Response data:", data);

            // redirect to the home page after successful login
            router.push("/dashboard");
        } else {
            console.error("Login failed with status:", response.status);
        }
    };

    const handleClear = () => {
        setEmail("");
        setPassword("");
        setError({});
    }
    const signInWithGoogle = () => {
        // initiate the Google OAuth flow by redirecting the user to the appropriate URL
        globalThis.location.href = "/api/auth/google/login";
    }

    return (
        <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-4 max-w-sm mx-auto mt-10">
                <div className="flex flex-col gap-1">
                    <label htmlFor="email">Email</label>
                    <input className="border p-1 rounded"
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                    {error.email && <p className="text-red-500 text-sm">{error.email}</p>}
                </div>
                <div className="flex flex-col gap-1">
                    <label htmlFor="password">Password</label>
                    <input
                        className="border p-1 rounded"
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    {error.password && <p className="!text-red-500 text-sm">{error.password}</p>}
                </div>
                <button type="submit" className="bg-blue-500 text-white p-2 rounded">
                    Login
                </button>
                <button type="button" onClick={handleClear} className="bg-gray-300 text-gray-700 p-2 rounded">
                    Clear
                </button>
                <button type="button" className="bg-red-500 text-white p-2 rounded" onClick={signInWithGoogle}>
                    Sign in with Google
                </button>
            </div>
        </form>
    );
}