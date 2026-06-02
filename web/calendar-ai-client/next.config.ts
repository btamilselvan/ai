import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */

  logging: {
    fetches: {
      fullUrl: true,
    }
  },

  output: "standalone",

  images: {

  },
  // reactStrictMode: true,

  redirects: async () => {
    return [
      {
        source: "/api/calendar/search",
        destination: "http://localhost:8000/api/calendar/search",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
