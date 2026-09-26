/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  output: "standalone", // self-contained server for the Docker image
};

module.exports = nextConfig;
