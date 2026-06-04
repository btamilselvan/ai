This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### Prerequisite

- install npx ``` npm install -g npx ```
- create project ``` npx create-next-app@latest calendar-ai-client ```

[ You Install NVM ] 
       │
       ▼ (Brings)
[ Node.js ] ──► (Automatically Includes) ──► [ NPM ] & [ NPX ]
       │
       ▼ (You run an NPX command e.g. npx create-next-app@latest calendar-ai-client)
[ Next.js or Vite Project ]
       │
       ▼ (Automatically downloads)
[ React.js ] & [ React-DOM ]

#### What Lives Where?
Global Tools (Installed once on a dev environment): NVM, Node.js, NPM, NPX.

Local Tools (Installed fresh inside every new project folder): Next.js/Vite, React, Tailwind CSS.

```Node.js``` is the base engine (the runtime environment). On its own, Node.js doesn't know anything about web pages, React components, or routing. It just runs JavaScript on your computer.

```Next.js``` is the software (the framework) written in JavaScript that knows how to build web servers, bundle React components, and handle API requests.

When we run ```npm run dev```, we are telling the Node.js engine to execute the Next.js development server code.

Think of it like a car:

Node.js is the engine.

Next.js is the car itself.

### Run

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


### Components
- Next.js (Framework Layer) - managing application architecture and orchestration, routing, server side redering, etc.
- React.js - core runtime engine, manages state on the client side.
- page.tsx (Entry point) - automatically pickedup
- layout.tsx (Persistent UI & State)
- loading.tsx (Instant Loading States)
- error.tsx (Runtime Error Isolation)
- package.json (The Project Manifest)
- next.config.ts (The Framework Compiler Engine)
- SWC (Speedy Web Compiler).
- Bundler (Turbopack) - mapping the relationships between the files.
- route.ts - handles API endpoints. automatically pickedup.

### Servers
- Node.js HTTP Server (The Industry Standard)
- V8 Edge Engines (Cloudflare Workers / Vercel Edge) (Global CDN for static assets and serverless functions)
- Bun - drop in alternative of Node.js

Think of Node.js as the Engine, your Next.js application as the Car, and Railway/Render as the Automated Garage and Highway System. They provide the underlying Linux infrastructure, continuous power, networking rules, SSL certificates, and firewalls required to keep your Node.js engine running smoothly in the cloud.


#### Mentalmodel

Think of Next.js as the Project Manager, SWC as the Translator (turning human-readable TypeScript/JSX into computer-readable JS), and Turbopack as the Logistics Fleet (organizing, separating, and shipping the packages cleanly to the server and the browser).

### What does compiler do?
- Transpilation (Downleveling) - converts advanced, modern JS syntaxes down to older, widely compatible targets
- The React JSX Transformation - Map tsx syntax to standard JS functions
- Minification and Dead Code Elimination (Tree Shaking) - To ensure production files are as small as possible, the compiler runs a minification pass.


### Notes

- Instead of a long-lived object mutating its internal properties, React works like an assembly line of quick, snapshot function executions. Every change in data results in a completely fresh function call that produces a new snapshot of the UI.
- When you write `const [loading, setLoading] = useState(false);` inside a client component, you are telling React: *"Hey, hold onto a piece of mutable state for me behind the scenes. Even when you re-run this entire function, remember what the last value of `loading` was."*

- Use ```.tsx``` extension if the file contains UI components.
- Use ```.ts``` extension if the file is pure configuration

- only a server component can be marked async.
- we cannot use server components in the client components (e.g. cookies)

## Tailwind css
- Utility-first CSS framework.
- Think of traditional CSS as buying pre-assembled LEGO sets, while Tailwind is like getting a massive box of individual bricks.
- Your CSS Stops Growing: In traditional projects, as your site grows, your CSS file gets massive. With Tailwind, because you reuse the same utility classes over and over, your final CSS bundle stays incredibly small.

### Tailwind vs css comparision
Traditional CSS:
<div class="card">
  <button class="btn-primary">Click me</button>
</div>

<style>
  .card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }
  .btn-primary {
    background-color: #3b82f6;
    color: white;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border-radius: 0.25rem;
  }
</style>

Tailwind:
<div class="bg-white p-6 rounded-lg shadow-md">
  <button class="bg-blue-500 text-white font-semibold py-2 px-4 rounded">
    Click me
  </button>
</div>


bg-white -> background-color: white;
p-6 -> padding
rounded-lg -> border-radius: 0.5rem;
shadow-md -> add a medium  box shadow

## Design patterns

## Lifecycle management
- Mounting (component is loading for the first time)
- Updating (component state is updated)
- Unmounting (component is removed from the screen)


## Routing
- [...slug] (Single Brackets) = Catch-All Route
    This requires at least one sub-route in the URL for it to work. If you try to go to the base folder path without a sub-route, Next.js will throw a 404 Not Found error.

Folder: app/api/auth/google/[...slug]/route.js

/api/auth/google/login 🟢 Works (slug is ["login"])

/api/auth/google/callback 🟢 Works (slug is ["callback"])

/api/auth/google ❌ 404 Error (because there is no slug)
- [[...slug]] (Double Brackets) = Optional Catch-All Route
The double brackets make the parameters completely optional. This means it will catch the sub-routes and it will catch the base folder path itself without breaking.

Folder: app/api/auth/google/[[...slug]]/route.js

/api/auth/google/login 🟢 Works (slug is ["login"])

/api/auth/google/callback 🟢 Works (slug is ["callback"])

/api/auth/google 🟢 Works (slug is undefined)