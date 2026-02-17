import type { NextConfig } from 'next';
import nextPWA from 'next-pwa';

const withPWA = nextPWA({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
  skipWaiting: true,
});

const nextConfig: NextConfig = {
  webpack: (config) => {
    if (process.env.NEXT_WEBPACK_USEPOLLING) {
      config.watchOptions = {
        ...(config.watchOptions || {}),
        poll: 800,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

export default withPWA(nextConfig);
