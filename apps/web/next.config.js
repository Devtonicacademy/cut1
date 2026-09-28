/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  output: "standalone", // self-contained server for the Docker image
  // On hosts without Caddy (e.g. Railway), the web server forwards /api/* to the API itself.
  // Read at build time, so it is passed to the Docker build as a build argument.
  async rewrites() {
    const api = process.env.API_INTERNAL_URL;
    return api ? [{ source: "/api/:path*", destination: `${api.replace(/\/$/, "")}/api/:path*` }] : [];
  },
};

module.exports = nextConfig;
