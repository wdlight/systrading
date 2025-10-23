/** @type {import('next').NextConfig} */
const nextConfig = {
  // Prevent build cache corruption issues
  webpack: (config, { dev, isServer }) => {
    // Fix for "Invalid or unexpected token" errors in dev mode
    if (dev) {
      config.cache = false; // Disable webpack cache in dev
    }
    return config;
  },

  // Disable webpack5 persistent caching to prevent corruption
  experimental: {
    webpackBuildWorker: false, // Disable build worker to prevent cache issues
  },

  // Ensure proper file watching
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },

  // Optimize for development
  reactStrictMode: true,

  // Fix for hot reload issues
  compress: false, // Disable compression in dev for faster rebuilds
};

module.exports = nextConfig;
